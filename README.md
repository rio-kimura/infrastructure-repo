# 🎓 卒業制作 インフラ自動構築・監視通知基盤 (infrastructure-repo)

このリポジトリは、卒業制作のアプリケーションが24時間365日、安全かつ安定して動き続けるための「サーバー環境（インフラ）」をボタン一つで自動構築するためのマスターコードです。

「インフラの知識がないチームメンバー」でも迷わず自分のPCに全く同じ環境を再現できるよう、専門用語を噛み砕いて解説しています。

---

## 1. プロジェクトの概要（このインフラの目的）
本プロジェクトは、アプリケーションとデータベースを動作させるサーバーを分離し、さらに全体の健康状態を見守る監視専用のサーバーを用意した「疎結合かつ堅牢な3台構成」のシステムです。

手動での複雑な設定作業を一切排除し、プログラム（Ansible）を使ってサーバー構築を完全自動化しています。これにより、誰のPCで実行しても、あるいは本番サーバー（さくらVPS）であっても、寸分違わぬ安全な環境が自動的に完成します。

### 👥 サーバー別の役割とIPアドレス一覧
開発班が作成したアプリケーションやデータベースは、以下のネットワーク上に自動展開されます。

| サーバー名 | 実際の役割（分かりやすい説明） | 開発環境でのIPアドレス | このサーバーで動くもの / ポート番号 |
| :--- | :--- | :--- | :--- |
| **Server A** | **Control Node（司令塔）**<br>他のサーバーに設定を命令したり、データのバックアップを自動で集める中心地です。 | `10.149.245.110` | Ansible (構築ツール), Git, Node Exporter (負荷測定ポート: 9100) |
| **Server B** | **App/DB Node（実行環境）**<br>開発班が作ったWebアプリやデータベースが実際に稼働する本番の舞台です。 | `10.149.245.115` | Docker Engine (コンテナ基盤), **80ポート (Webアクセス窓口)**, Node Exporter (9100) |
| **Server C** | **Monitor Node（監視管制塔）**<br>システム全体の健康状態を24時間見守り、異常があれば即座にアラートを出します。 | `10.149.245.116` | Prometheus (データ収集: 9090), Grafana (グラフ可視化: 3000), `noc_bot` (Discord通知コンテナ) |

---

## 2. 使用している主な技術
難しい専門知識は不要です。「これらが裏側で連携して動いている」ということだけ知っておいてください。
- **仮想化技術（Vagrant / VirtualBox）**: パソコンの中に、AlmaLinux 9というサーバー用の仮想的なPCを3台自動で立ち上げる技術です。
- **自動構築ツール（Ansible）**: 設定手順書（Playbook）を読み込ませることで、3台のサーバーに必要なソフトを自動でインストール・設定するツールです。
- **コンテナ基盤（Docker）**: アプリケーションやデータベースを、他の環境を汚さずに独立して動かすためのカプセル技術です。
- **監視・通知（Prometheus / Grafana / Python）**: サーバーのメモリやCPUの突発的な負荷を検知し、グラフ化してDiscordへメッセージを飛ばすシステムです。

---

## 3. 必要な環境変数やコマンド一覧

### 🔑 変数ファイルの仕組み（group_vars/）
設定値（パラメータ）は、役割ごとに以下のファイルに小分けに保管されています。
- **`all.yml` (共通設定)**: 2GBのスワップ領域（メモリが足りなくなった時の命綱）の確保や、日本標準時への時計合わせ（Chrony）など、全サーバー共通の土台が書かれています。
- **`vagrant.yml`**: 「今は手元のテスト環境（Vagrant）で動かしているよ」という目印（`is_production: false`）が書かれています。
- **`prod.yml`**: 「今はさくらVPS（本番）で動かしているよ」という目印（`is_production: true`）が書かれています。
- **`secrets.yml`**: Discordに通知を送るための大事なURLなど、他人に絶対見られてはいけない機密情報が暗号化されて入っています。

### 🛠️ 定期運用・個別バックアップコマンド
```bash
# アプリやデータベースのデータを手動で今すぐバックアップし、Server Aへ回収する指示
ansible-playbook -i inventories/vagrant/hosts.ini db_backup.yml --vault-password-file /home/vagrant/.vault_password
```

---

## 4. 詳細ディレクトリ構成（全ファイル完全マスターマップ）
リポジトリ内に存在するすべてのファイルとその具体的な役割の地図です。インフラ班以外の人も、どのファイルが何の設定を司っているかをここから一目で確認できます。

```text
infrastructure-repo/
├── .gitattributes             # WindowsとLinuxの間の改行コード不整合(CRLF/LF)をGitコミット時に自動解決する盾
├── .gitignore                 # パスワードや一時ファイル(`.vagrant/`)をGitHubに誤爆アップロードしないための除外リスト
├── Vagrantfile                # パソコン内にAlmaLinux 9の仮想サーバーを3台同時ブートするスペック定義書
├── ansible.cfg                # Ansibleの動作環境設定（金庫のパスワード読み込み先やエラー回避設定を定義）
├── site.yml                   # インフラ全体の構築を統括するメインのシナリオ指示書
├── db_backup.yml              # 手動・オンデマンドでデータベースのデータをバックアップするための専用指示書
├── kickoff.sh                 # サーバーAの中で自動鍵配布から疎通テストまでを一撃でこなす初期化スクリプト
├── requirements.yml           # Ansibleで高度なシステム操作(SwapやSELinux)を行うための外部部品プラグインリスト
├── group_vars/                # サーバーの設定値（ポート番号やURLなど）が集まる最重要変数フォルダ
│   ├── all.yml                # 全サーバー共通の基本仕様（要塞化SSHポート: 2222, スワップ: 2048MB, 時刻同期）
│   ├── vagrant.yml            # ローカルテスト環境であることを示す目印ファイル (`is_production: false`)
│   ├── prod.yml               # さくらVPS本番環境であることを示す目印ファイル (`is_production: true`)
│   └── secrets.yml            # 暗号化されたDiscordのWebhook URLなどの秘匿情報を厳重保管する金庫ファイル
├── inventories/               # 各サーバーの「住所（IPアドレス）」や接続方法を管理するフォルダ
│   ├── vagrant/
│   │   └── hosts.ini          # テスト環境用の住所録。IP(10.149...)や標準パスワード(vagrant)が記載
│   └── prod/
│       └── hosts.ini          # さくらVPS本番環境用の住所録。rootユーザーで22番ポートから突入するための定義
└── roles/                     # 手順書をソフトや機能ごとに役割分担・小分けにして格納するフォルダ
    ├── common/                # 全台共通で動作させるべき最下層のインフラ土台を作る手順
    │   ├── handlers/
    │   │   └── main.yml       # 時刻同期（Chrony）やSSHDの設定が書き換わった時に、安全に再起動をかけるトリガー
    │   ├── tasks/
    │   │   └── main.yml       # スワップ領域の確保、Chronyインストール、Node Exporter（負荷測定器）の自動配置
    │   └── templates/
    │       └── chrony.conf.j2 # 日本標準時(NICT)のサーバーへ正確に時計を合わせるための動的設定テンプレート
    ├── docker/                # アプリケーションをカプセル化して動かすための環境を作る手順
    │   ├── handlers/
    │   │   └── main.yml       # Dockerのシステム設定（daemon.json）が変わった時だけコンテナエンジンを再起動する仕組み
    │   ├── tasks/
    │   │   └── main.yml       # Docker Engine本体、Composeプラグインの導入と、アプリ用ネットワーク(app_network)の自動作成
    │   └── templates/
    │       └── daemon.json.j2 # Dockerコンテナが出力するログの容量が溢れないよう、10MB×3世代に制限する設定書
    ├── backup/                # Server Bのデータを固めてServer Aへ回収するバックアップ運用手順
    │   ├── tasks/
    │   │   └── main.yml       # バックアップ用スクリプトの配置、毎日深夜03:00の定期実行(Cron)登録、Server Aへの遠隔回収
    │   └── templates/
    │       └── backup_volumes.sh.j2 # Dockerのボリュームデータを根こそぎ安全な圧縮ファイルにするためのシェルスクリプト
    ├── app/                   # ★将来的に開発班が作ったアプリケーションコンテナを自動起動するための連携窓口
    │   └── tasks/
    │       └── main.yml       # 開発班のWebアプリケーション・DBコンテナの立ち上げ手順を記載する空のベースファイル
    ├── monitor/               # サーバーの健康状態をグラフ化し、Discordへ異常を告げる監視センターの手順
    │   ├── handlers/
    │   │   └── main.yml       # Prometheusの設定（監視対象IPなど）が更新された時に、監視デーモンを再起動するトリガー
    │   ├── tasks/
    │   │   └── main.yml       # PrometheusとGrafana의インストール、Systemd起動登録、Discord通知ボットの常駐化
    │   ├── templates/
    │   │   ├── backup_script.sh.j2     # バックアップ処理自体の異常を検知し、失敗時に直接DiscordへSOSを投げる緊急スクリプト
    │   │   ├── discord_bot.py.j2       # Prometheusのデータを15秒おきに監視し、サーバーダウンやメモリ90%超過を検知するPythonプログラム
    │   │   ├── discord_bot.service.j2  # Discord通知Pythonプログラムを、OS起動時にバックグラウンドで自動常駐させるための定義書
    │   │   ├── prometheus.service.j2   # Prometheusを安全な非特権ユーザー（prometheus）でLinux上に常駐させるための管理設定ファイル
    │   │   └── prometheus.yml.j2       # 3台のサーバーそれぞれの「10.149...:9100」を見に行くように指示する監視ターゲット設定書
    │   └── files/
    │       └── noc_bot/       # ボットを独立した Docker コンテナとして Server C 上でスマートに運用するための内製プログラム群
    │           ├── Dockerfile          # Python 3.9-slim 環境をベースにした、ボット専用の軽量Dockerコンテナイメージの設計図
    │           ├── requirements.txt    # ボットが外部通信(requests)を行うために必要なPython外部ライブラリの固定リスト
    │           └── src/
    │               └── main.py         # コンテナの内部で眠らずに働き続ける、Discord通知メインロジックのプログラムソース
    └── security/              # 不正なアクセスを鉄壁の防御でシャットアウトするセキュリティ手順
        └── tasks/
            └── main.yml       # Firewalldの導入、接続フリーズを回避する非同期起動、および環境フラグによるVagrant接続遮断防止
```

---

## 5. 開発環境の構築方法（完全再構築マニュアル）

卒業制作：インフラ構築自動化「黄金の3ステップ」再構築マニュアル
本ドキュメントは、開発環境（Vagrant/VirtualBox）を完全に初期化した状態（更地）から、各種ミドルウェアの展開、セキュリティ要塞化、監視管制塔（Grafana）の開通までを、ヒューマンエラーを排除して最短で完結させるための運用プロトコルである。

### 🏃 1. 実行手順（黄金の4ステップ）

#### 1️⃣ Step 1: ホストOS（Windows）での完全クリーン起動
WindowsのPowerShellを開き、プロジェクトのルートディレクトリ（Vagrantfile がある場所）で以下を実行します。

```bash
# 1. 既存の仮想マシン（ゾンビプロセスやセッションロック含む）を強制全破棄
vagrant destroy -f

# 2. まっさらな初期状態の仮想マシンを3台まとめて起動（全員ポート22番で着地）
vagrant up

# 3. 司令塔（Server A）へSSHログイン
vagrant ssh server-a
```

#### 2️⃣ Step 2: ゲストOS（Server A）での初期セットアップと自動鍵配布
サーバーAにログイン後（プロンプトが `[vagrant@server-a ~]$` になっている状態）、以下のコマンド群をまとめてコピー＆ペーストして実行します。

```bash
# 共有フォルダへ移動
cd /vagrant

# キックオフスクリプト（kickoff.sh）の自動生成
cat << 'EOF' > kickoff.sh
#!/bin/bash
set -e

INIT_PASS="vagrant"
INVENTORY="inventories/vagrant/hosts.ini"
VAULT_SOURCE=".vault_password"
VAULT_DEST="$HOME/.vault_password"
PUB_KEY="$HOME/.ssh/id_rsa.pub"

echo "=== [1/5] OSパッケージ・sshpass の導入 ==="
sudo dnf install -y epel-release
sudo dnf install -y ansible-core git sshpass

echo "=== [2/5] 依存コレクションの一括導入 ==="
ansible-galaxy collection install ansible.posix community.docker community.general

echo "=== [3/5] 司令塔用 SSHキーペアの生成 ==="
if [ ! -f "$HOME/.ssh/id_rsa" ]; then
    ssh-keygen -t rsa -b 4096 -N "" -f "$HOME/.ssh/id_rsa"
    echo "✔ SSH鍵を新規作成しました。"
else
    echo "✔ SSH鍵は既に存在します。"
fi

echo "=== [4/5] Ansible Vault パスワードファイルのセキュア隔離 ==="
if [ -f "$VAULT_SOURCE" ]; then
    cp "$VAULT_SOURCE" "$VAULT_DEST"
    chmod 600 "$VAULT_DEST"
    echo "✔ Vaultパスワードの権限正常化(600)を完了しました。"
else
    echo "❌ エラー: $VAULT_SOURCE が存在しません。"
    exit 1
fi

echo "=== [5/5] sshpass による公開鍵の全台フルオート配布 ==="
export ANSIBLE_HOST_KEY_CHECKING=False
SSHPASS=$INIT_PASS ansible all -i "$INVENTORY" \
  -m ansible.posix.authorized_key \
  -a "user=vagrant state=present key='{{ lookup('file', '$PUB_KEY') }}'" \
  -c ssh --extra-vars "ansible_password=$INIT_PASS ansible_port=22" \
  -k

echo "================================================================="
echo " 🎉 鍵配布完了！初期ポート(22番)での通信テストを開始します。"
echo "================================================================="
ansible all -i "$INVENTORY" -m ping --extra-vars "ansible_port=22"
EOF

# 実行権限を付与して実行
chmod +x kickoff.sh
./kickoff.sh
```
※最後に全台から緑色の `"ping": "pong"` が返ってくれば大成功です。

#### 3️⃣ Step 3: メインPlaybookによる一括全自動インフラ構築
鍵の配布が完了したら、そのままサーバーAの画面でメインPlaybookをキックします。

```bash
# 共有フォルダの権限制限をバイパスする環境変数を指定
export ANSIBLE_CONFIG=./ansible.cfg

# 隔離した金庫のパスワードを指定し、インフラ全体のフルオート構築を開始
ansible-playbook -i inventories/vagrant/hosts.ini site.yml --vault-password-file ~/.vault_password
```
※対策済みのPlaybookなので、未定義エラーやDockerのタイムアウトを起こすことなく、一気に最後までノンストップで駆け抜けてオールグリーン（failed=0）を叩き出します。
これですべての工程が完全自動で復元されました！

#### 🛠️ 付録：もしコマンドの途中でフリーズ・停止した場合の強制脱出（デバッグ）
VagrantやVirtualBoxの処理を途中で強制終了（Ctrl + C）した際、Windowsのメモリにプロセスの幽霊（ロック）が残って動かなくなった場合は、WindowsのPowerShellで以下をそのまま実行してゾンビプロセスを一掃してください。

```powershell
# 1. Vagrant(Ruby)の幽霊プロセスを強制終了して排他ロックを解除
taskkill /F /IM ruby.exe /T

# 2. VirtualBoxの黒幕プロセスを強制終了してセッションロックを解放
taskkill /F /IM VBoxHeadless.exe /T
taskkill /F /IM VBoxManage.exe /T
taskkill /F /IM VBoxSVC.exe /T
taskkill /F /IM VirtualBox.exe /T
```
※上記を実行した後、再度 `vagrant destroy -f` または `vagrant reload` を叩けば、PCを再起動せずとも100%確実に安全な状態からリトライできます。

---

## 6. 監視管制画面（Grafana）の初期登録手順

### 🛠 Step 1: Prometheusが生きているか確認
まず、データ元（Prometheus）がちゃんとデータを集めているか確認します。

1. ブラウザで http://10.149.245.116:9090 にアクセスします。
2. 上部メニューの **[Status] → [Targets]** を開きます。
3. `server-a`, `server-b`, `server-c` などのステータスがすべて **「UP」（緑色）** になっていれば完璧です。

### 🛠 Step 2: Grafanaに「データソース」を登録する
Grafanaに「データはServer CのPrometheusから取ってきてね」と教えます。

1. Grafana（http://10.149.245.116:3000）にログイン。
2. 左メニューの **[Connections] → [Data sources]** をクリック。
3. **[Add data source]** ボタンを押し、**Prometheus** を選択。
4. Connection (URL) の欄に、Server CのプライベートIPを使って以下を入力します：`http://10.149.245.116:9090`
   *(※コンテナ同士で通信している場合は http://prometheus:9090 の場合もありますが、まずはIPで試すのが確実です。)*
5. 一番下の **[Save & test]** をクリック。**「Successfully queried the Prometheus API.」** と緑色で出れば成功です！

### 🛠 Step 3: グラフを表示させる（ダッシュボードの導入）
自分でグラフを1から作るのは大変なので、世界中で使われている「完成済みダッシュボード」をインポートしましょう。

1. 左メニューの **[Dashboards]** を開き、**[New] → [Import]** をクリック。
2. **[Import via grafana.com]** の欄に、魔法の数字 **`1860`** を入力して **[Load]** を押します。*(※これは「Node Exporter Full」という、CPUやメモリを完璧に表示してくれる超定番ボードです。)*
3. 次の画面で「Prometheus」の選択欄が出るので、先ほど作ったデータソースを選択。
4. **[Import]** をクリック！

### 💡 なぜこれでグラフが見れるようになるのか？
Grafana自体はデータベースを持っていません。以下の3つの連携が完成して、初めてグラフが動き出します。
- **Node Exporter**: 各サーバーのCPU使用率などの「生データ」を出す。
- **Prometheus**: そのデータを定期的に回収して「蓄積」する。
- **Grafana**: Prometheusに「今のメモリ使用率を教えて」とリクエストし、それを「かっこいいグラフ」にする。

### 🚀 これで完成！
インポートしたダッシュボードで、Server A, B, C の負荷がリアルタイムで動いているはずです。

---

## 7. 最終稼働テスト（URL一覧）
すべての自動プロビジョニングおよびダッシュボード登録が完了したら、WindowsのWebブラウザから以下のURLへアクセスし、システムが正常稼働しているか最終確認を行います。

- **監視管制画面（Grafana）**: http://localhost:3000 （初期ID/PW: admin / admin）
- **データ蓄積サーバー（Prometheus）**: http://localhost:9090
- **Webアプリケーション入口（Nginx）**: http://localhost:8080 （Welcome to nginx! の表示）

---

## 8. トラブルシューティング（よくあるエラーと解決策）

### ① ファイアウォールを起動した瞬間に、処理がフリーズして進まなくなる
- **原因**: 防犯の壁（Firewalld）を起動した瞬間、ネットワークスタックが一瞬初期化（瞬断）されるか、既存のSSHセッションがゾンビ化し、サーバーからの完了報告がAnsibleに届かなくなるため。
- **解決策**: 壁を起動する際、Ansibleに**「完了の返事をその場で待たずに、一度通信を切って次のタスクへ進め（非同期：`async: 30` / `poll: 0`）」**という命令を出し、直後のタスクで通信が安定してから安全に再接続（`wait_for_connection`）するロジックをコードに組み込み、フリーズを100%回避しています。

### ② セキュリティを厳しくしたら、自分のパソコン（Vagrant）からも接続できなくなった
- **原因**: インターネットからの攻撃を防ぐため、SSHポートを22番から2222番に変えたり、パスワードでのログインを禁止する要塞化設定を開発環境（Vagrant）でそのままやってしまうと、Vagrant自身の標準の接続ルール（22番ポート・パスワード接続必須）とケンカしてしまい、次からサーバーに一切入れなくなる自己遮断トラブルが起きます。
- **どうやって解決したか**: Variable（変数）ファイルに環境スイッチ（`is_production`）を作りました。プログラム側で**「今はVagrant環境（false）だから、このSSHD設定変更タスクは自動的に実行せずにパス（Skipped）しよう」「さくらVPS（本番：true）の時だけフル稼働させよう」**と自動で賢く判断させることで、開発環境の快適さと本番の超強固なセキュリティを完全に両立させました。

### ③ Windowsで編集しただけなのに、Linuxサーバー上で謎の構文エラーになる
- **原因**: WindowsとLinuxでは、文章の行末にある「見えない改行マーク（改行コード）」の仕様が異なります。Windowsの改行マーク（CRLF）のまま設定ファイルをサーバー（Linux）に送ると、Linux側が「行末に変なゴミ文字がくっついている！」と勘違いし、文字化けや謎の起動エラーを起こすインフラ最大の沼トラブルがありました。
- **どうやって解決したか**: リポジトリ直下に `.gitattributes` というファイルを配備しました。これにより、Windows上でファイルを編集して普通に `git add .` してコミットするだけで、**Gitが裏側で自動的に改行マークをLinux標準の `LF` コードへ綺麗に変換・統一**してくれます。
```
