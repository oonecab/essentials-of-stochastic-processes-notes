# M030：宿主机 MySQL 清理里程碑

状态：完成。关联 [I030](../issues/I030-host-mysql-removal.md)、[P030](../plan/P030-host-mysql-removal.md)、[T030](../test/T030-host-mysql-removal.md)。

完成条件：已授权的 MySQL 服务及历史数据库删除，3306/33060 不再监听；邮件工具依赖、Nginx、站点和证书保持；操作证据与宿主环境说明同步。

2026-10-17 已完成五个 MySQL 包及历史数据库删除，服务、账号与监听消失。Nginx 配置和站点版本不变，主站五书入口公网字节核对通过；项目所有者确认旧独立 Weiss 域名已正常退役，正式入口位于 Reading Notes 主站。登记快速检查 11 项通过，环境记录已同步。
