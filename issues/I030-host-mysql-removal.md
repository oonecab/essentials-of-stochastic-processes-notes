# I030：卸载宿主机遗留 MySQL

日期：2026-10-17。状态：完成。负责人：Codex；批准人：项目所有者。授权来自本次对话中用户明确要求“不需要备份了，直接卸载和删除吧”。范围为已核实的宿主机 MySQL 服务、数据库、专属配置和日志；不创建数据备份。

调查确认该实例至少自 2024 年存在，当前静态站点没有数据库依赖；执行前仅有系统事件调度线程和核查连接。数据库元数据和计数已核实，不复制业务记录。关联 [P030](../plan/P030-host-mysql-removal.md)、[T030](../test/T030-host-mysql-removal.md)、[M030](../milestone/M030-host-mysql-removal.md)；不可逆的数据删除选择见 [ADR-003](../docs/decisions/ADR-003-retire-host-mysql.md)。

包管理器模拟表明，清除 mysql-common 会连带移除 libmysqlclient21、libmailutils8 和 mailutils，因此只清除 mysql-server、mysql-server-8.0、mysql-server-core-8.0、mysql-client-8.0、mysql-client-core-8.0 五个包。保留被邮件工具依赖的共享客户端库和通用配置；不执行全局 autoremove。

执行前核对主机、目录 inode/device、真实路径、挂载和模拟卸载清单。先停止并取消自启，再通过包维护脚本清除服务和数据；任何超出精确清单的包删除、嵌套挂载或路径变化均停止操作。操作不可恢复历史数据库内容；用户明确选择删除且不备份，重新安装只能建立新实例。站点发布目录、配置和证书均保持。

文档影响：宿主机环境变化同步 .project-governance.json 与 docs/environments.md；MySQL 原本不属于 Reading Notes 技术栈，因此 TECH.md 的项目技术栈与变更索引保持。没有环境变量变化，.env.example 保持。教材、计算规则、前端与发布包没有变化，验收以包状态、进程、端口、目录、Nginx 配置/站点指纹及登记的快速检查为准，不另行全书构建或浏览器重验。

原始证据保存在忽略目录 tmp/server-mysql-removal-20261017/，不包含凭据和数据库备份。

执行结果：2026-10-17 19:06（北京时间）完成五个包的清除及数据删除。mysql unit、账号、自启入口、进程和 3306/33060 监听均消失；包管理器状态完整。实测根分区可用空间增加 400,457,728 字节（381.91 MiB），可用空间 24.10 GiB。前后内存可用量从 524,902,400 增至 1,286,217,728 字节，此值为全机瞬时变化。

Nginx 的 32 个配置文件哈希及四个站点 current 完全一致，运行中的服务仅减少 mysql.service。Reading Notes 首页及五书入口公网 HTTPS 正常，五书入口与原 dist 字节一致；SICP 正常重定向至 200，com 保持 401 鉴权。旧独立 weiss 域名的普通 DNS 请求失败，指定公网 IP 并校验证书/主机名时为 200；本次没有修改 DNS，将其作为独立访问边界记录，不宣称该域名解析已验收。
