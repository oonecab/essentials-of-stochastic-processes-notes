# T030：MySQL 卸载验收

关联 [I030](../issues/I030-host-mysql-removal.md)。本次为宿主机服务清理，不改变站点代码或教材内容。

验收项：

- 卸载模拟与实际包清单一致，仅移除五个指定包；保留 mailutils、libmailutils8、libmysqlclient21、mysql-common。
- 目标目录不是符号链接，没有嵌套挂载；执行前 inode/device 与核查记录相符。
- MySQL unit/自启、mysqld 进程、3306/33060 监听、数据及服务专属配置均消失。
- dpkg --audit 与 apt-get check 通过；不执行全局 autoremove。
- Nginx 配置哈希与各站 current 不变，nginx -t 成功；源站与公网响应复查，鉴权站点不绕过登录。
- 文件系统容量与进程资源变化分别记录；全机实时内存波动不等同于单一进程精确释放量。
- 文档链接、JSON 格式和 Git diff 检查通过；没有数据备份、凭据或运行证据进入 Git。

原始证据：tmp/server-mysql-removal-20261017/。

## 执行结果

- 初次模拟发现 mysql-common 会连带删除邮件工具；收窄为五个指定包后，模拟和实际删除范围一致。保留邮件工具及共享依赖。
- 主机、目录 device/inode、真实路径和挂载核对通过；systemctl disable --now、debconf 数据清理选项和 apt-get purge 均退出 0，未创建数据库备份。
- 14 项服务/数据/专属配置路径均已消失，mysql unit 为 not-found，mysqld 进程、系统 mysql 账号和 3306/33060 监听均不存在。
- dpkg --audit、apt-get check、nginx -t 均退出 0；Nginx 32 份配置哈希、四个 current、源站状态与操作前一致。运行服务只减少 mysql.service。
- 公网 Reading Notes 首页及五书入口均 200；五书入口与原 dist 内容哈希一致。SICP 跟随重定向为 200，com 为既有 401 鉴权。
- 旧独立 weiss 域名普通 DNS 查询失败；指定公网 IP、保持证书和主机名验证后为 200。该 DNS 状态本轮未修改，不能据此声称正常域名访问通过。
- 本地 curl 路径出现 TLS 错误，Python 直接 TLS 请求和服务器端 curl 交叉验证完成；原失败结果保留。停止服务后本地 TCP connect 仍可被中间网络接受，但没有 MySQL 握手，因此不以 TCP connect 单项判定服务存活；服务器监听为空，服务器到公网 IP 的 3306 为拒绝连接、33060 超时。
- 根分区可用空间净增 400,457,728 字节（381.91 MiB），使用率由 37% 降至 36%；内存可用量前后为 524,902,400 / 1,286,217,728 字节，属于全机瞬时观测。
- `python3 tools/project.py check --quick` 退出 0，11 项通过；报告为 tmp/project-check/20261017T191008-pybv6q42/report.json。
