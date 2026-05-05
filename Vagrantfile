# Vagrantfile
Vagrant.configure("2") do |config|
  # 全台共通：AlmaLinux 9 を使用
  config.vm.box = "almalinux/9"

  # Server A: Control Node（司令塔）
  config.vm.define "server-a" do |node|
    node.vm.network "private_network", ip: "10.149.245.110"
    node.vm.hostname = "server-a"
    node.vm.provider "virtualbox" do |vb|
      vb.memory = "1024"
      vb.cpus = 1
      vb.name = "server-a-ctrl"
    end
  end

  # Server B: App/DB Node（実行環境）
  config.vm.define "server-b" do |node|
    node.vm.network "private_network", ip: "10.149.245.115"
    node.vm.hostname = "server-b"
    node.vm.provider "virtualbox" do |vb|
      vb.memory = "2048"
      vb.cpus = 2
      vb.name = "server-b-app"
    end
  end

  # Server C: Monitor Node（監視・通知）
  config.vm.define "server-c" do |node|
    node.vm.network "private_network", ip: "10.149.245.116"
    node.vm.hostname = "server-c"
    node.vm.provider "virtualbox" do |vb|
      vb.memory = "2048"
      vb.cpus = 1
      vb.name = "server-c-mon"
    end
  end
end