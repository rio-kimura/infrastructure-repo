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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "noc_super_secret_session_key_999")

# --- [インフラ設計] 環境変数からの接続パラメータ読み込み ---
PROM_URL = os.getenv("PROMETHEUS_URL", "http://10.149.245.116:9090")
DB_HOST = os.getenv("DB_HOST", "noc-db")
DB_NAME = os.getenv("DB_NAME", "noc_audit_db")
DB_USER = os.getenv("DB_USER", "noc_operator")
DB_PASS = os.getenv("DB_PASSWORD", "noc_secure_pass")

# =================================================================
# 🔄 【切り替え用スロット】本番・テストの切り替えはここで行います
# =================================================================
CSV_FILE_PATH = "/opt/noc-system/noc_system/dummy_log.csv"
# =================================================================

ADMIN_USER = "admin"
ADMIN_PASS = "password123"


def check_db_connection():
    """PostgreSQL（noc-db）への接続テストと時系列テーブルの自動初期化"""
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


@app.route("/")
def index():
    if "logged_in" in session and session["logged_in"]:
        return redirect(url_for("search_page"))
    return redirect(url_for("login_page"))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("search_page"))
        else:
            flash("IDまたはパスワードが正しくありません。", "error")
            return render_template("login.html")
    return render_template("login.html")


@app.route("/search", methods=["GET"])
def search_page():
    if "logged_in" not in session or not session["logged_in"]:
        return redirect(url_for("login_page"))
    return render_template("search.html")


@app.route("/report", methods=["GET"])
def report_page():
    if "logged_in" not in session or not session["logged_in"]:
        return redirect(url_for("login_page"))

    year = request.args.get("year")
    month = request.args.get("month")
    day = request.args.get("day")

    if not year or not month or not day:
        flash("日付パラメータが不正です。", "error")
        return redirect(url_for("search_page"))

    # 💡【無条件確定モック出力ロジック】
    # CSVファイルの存在有無に関わらず、テスト時は常にサイバーネオン装飾のHTMLテーブルを出力します。
    html_table = """
    <table>
        <thead>
           <tr>
              <th>対象ノード (Instance)</th>
              <th>平均CPU使用率</th>
              <th>最大CPU使用率</th>
              <th>平均メモリ使用率</th>
              <th>最大メモリ使用率</th>
              <th>最大NW帯域 (KB/s)</th>
              <th>ステータス</th>
              <th>NOCアセスメント・運用診断レポート</th>
           </tr>
        </thead>
        <tbody>
           <tr>
              <td><b>server-a (司令塔)</b></td>
              <td>45.20%</td>
              <td>52.10%</td>
              <td>61.30%</td>
              <td>65.00%</td>
              <td>845.00 KB/s</td>
              <td><span style="background: rgba(34,197,94,0.1); color: #22c55e; border: 1px solid #22c55e; padding: 4px 8px; border-radius: 4px; font-size:12px; font-weight:bold;">HEALTHY</span></td>
              <td>インフラは極めて安定稼働しています。不審なリソーススパイクは検知されていません。</td>
           </tr>
           <tr>
              <td><b>server-b (アプリ班)</b></td>
              <td>55.80%</td>
              <td>62.40%</td>
              <td>78.50%</td>
              <td>82.10%</td>
              <td>1,204.50 KB/s</td>
              <td><span style="background: rgba(234,179,8,0.1); color: #eab308; border: 1px solid #eab308; padding: 4px 8px; border-radius: 4px; font-size:12px; font-weight:bold;">WARNING</span></td>
              <td>⚠️ 警告：一時的なメモリ高負荷を記録しています。アプリ層でのメモリリーク、またはアクセス集中が発生した可能性があります。</td>
           </tr>
           <tr>
              <td><b>server-c (監視管制塔)</b></td>
              <td>88.40%</td>
              <td>92.10%</td>
              <td>84.20%</td>
              <td>89.50%</td>
              <td>12,390.40 KB/s</td>
              <td><span style="background: rgba(239,68,68,0.1); color: #ef4444; border: 1px solid #ef4444; padding: 4px 8px; border-radius: 4px; font-size:12px; font-weight:bold;">CRITICAL</span></td>
              <td>🚨 緊急警告：CPU使用率が臨界点(90%超)を突破しました。即時リソース拡張、またはプロセスの異常暴走を調査してください。</td>
           </tr>
        </tbody>
     </table>
    """

    return render_template(
        "result.html", tables=html_table, year=year, month=month, day=day
    )


@app.route("/download_csv", methods=["GET"])
def download_csv():
    if "logged_in" not in session or not session["logged_in"]:
        return redirect(url_for("login_page"))

    csv_data = "timestamp,server_name,metric_type,value,status\n2026-05-27 09:00:00,server-a,CPU Usage,45.2%,NORMAL\n2026-05-27 09:00:15,server-b,Memory Usage,78.5%,WARNING\n2026-05-27 09:01:15,server-c,CPU Usage,92.1%,CRITICAL"
    csv_buffer = io.BytesIO(csv_data.encode("utf-8-sig"))
    return send_file(
        csv_buffer,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"noc_audit_report_{request.args.get('year')}{request.args.get('month')}{request.args.get('day')}.csv",
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


if __name__ == "__main__":
    check_db_connection()
    app.run(host="0.0.0.0", port=5000, debug=False)
