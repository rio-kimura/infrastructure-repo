#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime
import io
import requests
import psycopg2
import pandas as pd
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    flash,
)

app = Flask(__name__)

# --- [セキュリティ設計] セッション暗号化用の秘密鍵 ---
# ログイン状態（Cookie）の改ざんを防ぐための鍵です。
app.secret_key = os.getenv("FLASK_SECRET_KEY", "noc_super_secret_session_key_999")

# --- [インフラ設計] 環境変数からの接続パラメータ読み込み ---
PROM_URL = os.getenv("PROMETHEUS_URL", "http://10.149.245.116:9090")
DB_HOST = os.getenv("DB_HOST", "noc-db")
DB_NAME = os.getenv("DB_NAME", "noc_audit_db")
DB_USER = os.getenv("DB_USER", "noc_operator")
DB_PASS = os.getenv("DB_PASSWORD", "noc_secure_pass")

# --- [NOC運用設計] 固定の管理者認証情報 ---
# 「サーバーの管理者のみ」がアクセスできるようにするための固定ID/PWです。
ADMIN_USER = "admin"
ADMIN_PASS = "password123"  # 🚨本番時はAnsible Vault等での管理を推奨


# =================================================================
# ⚙️ 内部ロジック関数（ヘルパーメソッド）
# =================================================================


def check_db_connection():
    """PostgreSQL（noc-db）への接続テストと時系列テーブルの自動初期化（冪等性の担保）"""
    init_sql = """
    CREATE TABLE IF NOT EXISTS noc_metrics_history (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        instance VARCHAR(50) NOT NULL,
        cpu_utilization NUMERIC(5, 2),
        memory_utilization NUMERIC(5, 2),
        network_receive_bytes BIGINT,
        UNIQUE(timestamp, instance)
    );
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
        cur = conn.cursor()
        cur.execute(init_sql)
        conn.commit()
        cur.close()
        conn.close()
        print("[+] PostgreSQL NOC History Table is ready.")
    except Exception as e:
        print(f"[-] Database initialization error: {e}")


def get_metrics_from_db(target_date_str):
    """PostgreSQLから特定の日付（YYYY-MM-DD）の生データを抽出し、Pandas DataFrameに変換する"""
    sql = """
    SELECT timestamp, instance, cpu_utilization, memory_utilization, network_receive_bytes
    FROM noc_metrics_history
    WHERE timestamp::date = %s
    ORDER BY timestamp ASC;
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
        df = pd.read_sql_query(sql, conn, params=(target_date_str,))
        conn.close()
        return df
    except Exception as e:
        print(f"[-] DB Fetch Error for date {target_date_str}: {e}")
        return pd.DataFrame()


# =================================================================
# 🌐 Webアプリケーション 画面ルーティング＆状態遷移制御
# =================================================================


@app.route("/")
def index():
    """ルートURLへのアクセス。セッションの有無でログインか検索画面へ自動振り分け（状態⓪）"""
    if "logged_in" in session and session["logged_in"]:
        return redirect(url_for("search_page"))
    return redirect(url_for("login_page"))


# --- 【状態①】ログイン画面 (Login) ---
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        # 画面から入力されたユーザーIDとパスワードを取得
        username = request.form.get("username")
        password = request.form.get("password")

        # 管理者情報と一致するか検証
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            session["username"] = username
            print(f"[+] 管理者 {username} がログインに成功しました。")
            return redirect(url_for("search_page"))
        else:
            # 認証失敗時はフラッシュメッセージをセットして再レンダリング（状態①維持）
            flash("IDまたはパスワードが正しくありません。", "error")
            return render_template("login.html")

    return render_template("login.html")


# --- 【状態②】レポート検索画面 (Search) ---
@app.route("/search", methods=["GET"])
def search_page():
    # 🚨ゲートキーパー設計: 未ログイン状態での裏口侵入を完全にシャットアウト
    if "logged_in" not in session or not session["logged_in"]:
        return redirect(url_for("login_page"))

    return render_template("search.html")


# --- 【状態③】表形式レポート出力画面 (Result) ---
@app.route("/report", methods=["GET"])
def report_page():
    if "logged_in" not in session or not session["logged_in"]:
        return redirect(url_for("login_page"))

    # 画面のプルダウンメニューから送られてきた年・月・日を取得
    year = request.args.get("year")
    month = request.args.get("month")
    day = request.args.get("day")

    # 🚨堅牢化バリデーション: プルダウンによる「2月31日」などの存在しない日付をチェック
    target_date_str = f"{year}-{month}-{day}"
    try:
        datetime.strptime(target_date_str, "%Y-%m-%d")
    except ValueError:
        flash(
            f"エラー: 指定された日付「{target_date_str}」はカレンダー上存在しません。",
            "error",
        )
        return redirect(url_for("search_page"))

    # データベースから該当日のデータを引っ張る
    df = get_metrics_from_db(target_date_str)

    if df.empty:
        # データがまだ蓄積されていない日付の場合は、検索画面に戻して警告を表示
        flash(
            f"指定された日付（{target_date_str}）の監査ログはデータベースに蓄積されていません。",
            "warning",
        )
        return redirect(url_for("search_page"))

    # --- Pandasを活用した高度なNOC統計解析ロジック ---
    summary_reports = []
    for instance, group in df.groupby("instance"):
        avg_cpu = group["cpu_utilization"].mean()
        max_cpu = group["cpu_utilization"].max()
        avg_mem = group["memory_utilization"].mean()
        max_mem = group["memory_utilization"].max()
        max_net = group["network_receive_bytes"].max() / 1024  # KB/s単位に換算

        # NOCアセスメント自動判定エンジン
        status_badge = "HEALTHY"
        assessment = "インフラは極めて安定稼働しています。不審なリソーススパイクは検知されていません。"

        if max_cpu > 80 or max_mem > 90:
            status_badge = "WARNING"
            assessment = "⚠️ 警告：一時的な超高負荷を記録しています。アプリ層でのメモリリーク、またはアクセス集中が発生した可能性があります。"
        elif max_net > 5000:  # 5MB/sを超えるスパイク通信
            status_badge = "TRAFFIC ALERT"
            assessment = "⚠️ 帯域警告：突発的なネットワークトラフィックを検知。開発班による大量デプロイ、またはDoS攻撃の予兆を否定できません。"

        summary_reports.append(
            {
                "instance": instance,
                "avg_cpu": f"{avg_cpu:.2f}",
                "max_cpu": f"{max_cpu:.2f}",
                "avg_mem": f"{avg_mem:.2f}",
                "max_mem": f"{max_mem:.2f}",
                "max_net": f"{max_net:.2f}",
                "status": status_badge,
                "assessment": assessment,
            }
        )

    return render_template(
        "result.html",
        date_str=target_date_str,
        reports=summary_reports,
        year=year,
        month=month,
        day=day,
    )


# --- 【状態③の拡張】CSVダウンロード処理 (Download API) ---
@app.route("/download_csv", methods=["GET"])
def download_csv():
    if "logged_in" not in session or not session["logged_in"]:
        return redirect(url_for("login_page"))

    year = request.args.get("year")
    month = request.args.get("month")
    day = request.args.get("day")
    target_date_str = f"{year}-{month}-{day}"

    # 指定日の全監査ログをDBから引っ張る
    df = get_metrics_from_db(target_date_str)

    if df.empty:
        return "データが存在しません", 404

    # 💡プロのこだわり: サーバーのディスクを汚さないよう、メモリ上の仮想ファイル（BytesIO）にCSVを出力
    csv_buffer = io.BytesIO()
    # UTF-8でExcelでも文字化けしないように出力（インフラ監査提出用）
    df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
    csv_buffer.seek(0)

    filename = f"noc_audit_report_{year}{month}{day}.csv"

    # ブラウザに対して「これはダウンロードファイルである」という適切なHTTPヘッダーを付与して返却
    return send_file(
        csv_buffer, mimetype="text/csv", as_attachment=True, download_name=filename
    )


# --- ログアウト処理 ---
@app.route("/logout")
def logout():
    """セッションを安全に破棄し、ログイン画面（状態①）へ戻す"""
    session.clear()
    return redirect(url_for("login_page"))


# =================================================================
# 🚀 アプリケーション起動エントリポイント
# =================================================================
if __name__ == "__main__":
    # 起動時にデータベースとテーブルの存在確認を100%自動実行（冪等性の担保）
    check_db_connection()

    # 外部のNginxコンテナからのリクエスト（リバースプロキシ）を受け付けるため、
    # 0.0.0.0 の 5000番ポートでアプリケーションサーバーを常駐起動させます。
    app.run(host="0.0.0.0", port=5000, debug=False)
