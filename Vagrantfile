# Vagrantfile (Infrastructure Preparation Mode)
Vagrant.configure("2") do |config|
  # 全台共通：AlmaLinux 9
  config.vm.box = "almalinux/9"

  # --- 1. Server A: Control Node (司令塔) ---
  config.vm.define "server-a" do |node|
    node.vm.network "private_network", ip: "10.149.245.110"
    node.vm.hostname = "server-a"
    node.vm.provider "virtualbox" do |vb|
      vb.memory = "2048"
      vb.cpus = 1
      vb.name = "server-a-ctrl"
    end
  end

  # --- 2. Server B: App/DB Node ---
  config.vm.define "server-b" do |node|
    node.vm.network "private_network", ip: "10.149.245.115"
    node.vm.hostname = "server-b"
    node.vm.provider "virtualbox" do |vb|
      vb.memory = "2048"
      vb.cpus = 2
      vb.name = "server-b-app"
    end
  end

  # --- 3. Server C: Monitor Node ---
  config.vm.define "server-c" do |node|
    node.vm.network "private_network", ip: "10.149.245.116"
    node.vm.hostname = "server-c"
    node.vm.provider "virtualbox" do |vb|
      vb.memory = "2048"
      vb.cpus = 1
      vb.name = "server-c-mon"
    end
  end

  # ※ 自動プロビジョニング(ansible_local)はすべて削除しました。
  # サーバーが立ち上がった後、手動でServer Aを司令塔に設定します。
end