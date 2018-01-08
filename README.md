# 监控脚本使用说明
#民生mq灾备切换

## 部署、执行
* 脚本在每个宿主机上部署、执行
* 因脚本中执行 docker 命令，所以脚本需要root权限，使用root用户执行，或sudo执行

## 检查方式
* portCheck：端口是否可正常建立连接检查
* procCheck：进程关键字检查
* containerCheck：容器运行状态检查（is running: true | false）

## 三种检查方式中 value 代表的状态
### portCheck
* 0: Connect port success
* 1: Connection refused
* 2: Connection timeout (1s)
* 3: Unknown error

### procCheck
* 0: 实际进程数与期望进程数相等
* 1: 实际进程数多于期望进程数
* 2: 实际进程数少于期望进程数
* 3: Unknown

### containerCheck
* 0: container running
* 1: container stopped
* 2: 执行命令 "docker inspect --format='{{.State.Running}}'" 的返回值非零，可能原因：docker-daemon停止运行；执行该脚本的权限非root权限
* 3：执行命令成功，但返回的结果不正确（正确返回为 true 或 false）

## 定义 Metric key 的配置文件 settings.json
### 配置文件说明
* 配置文件为json格式
* procCheck:  key 为进程关键字，value 为 Metric 中要填入的 key
* portCheck:  key 为端口号，value 为 Metric 中要填入的 key
* containerCheck:  key 为容器名，value 为 Metric 中要填入的 key

### 配置文件使用
* 在配置文件中添加要检查的项和对应的 Metric 使用的 key
* 若检查的项目未在 settings.json 文件中定义，则 Metric 使用的 key 为 "检查项_None"

## 命令行参数
* -h help
* -H 主机IP
* -p 端口列表, e.g. -p "8080, 3306, 2181"
* -c 容器名列表， e.g. -c "ovs, vlan, swarm-agent"
* -P 启动进程的用户:进程关键字:进程数 的逗号分隔列表, e.g. -P "root:mysql:1, alimq:DragoonAgent:1"

* 完整示例： python arkMonitor.py -H "192.168.65.10" -c "ovs, vlan" -P “mysql:mysql:1,  alimq:DragoonAgent:1" -p "8080, 3306, 2181"