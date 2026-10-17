# 环境事实

<!-- project-governance:managed:start -->
## 环境变量名

- `ASTRO_TELEMETRY_DISABLED`：构建子进程强制为 `1`，禁用 Astro 遥测；`.env.example` 记录安全值。
- `READING_NOTES_TEST_CRASH`：仅隔离 dry-run 故障测试使用，选择强制终止阶段；生产路径不读取它作为故障开关。

## 服务

- 本地预览：Python 静态 HTTP 服务，绑定 127.0.0.1
- 正式阅读站点：notes.zzzping.top，Nginx + TLS；部署步骤见 deploy/README.md
- Ubuntu reading-notes-deploy.service 已安装并以 reading-notes 用户完成一次性发布；deploy timer 保持 disabled，构建服务模板留给独立构建主机
- I032 仓库模板：reading-notes 通过固定 root 安装器发布，release 树归 root，移除 unit 的整目录 Nginx 日志写例外；生产应用与实机验收待用户/运维执行，见 deploy/OPERATIONS-I032.md
- 宿主机历史 MySQL 服务及数据已于 2026-10-17 按 I030 卸载；mailutils 依赖的 mysql-common 与 libmysqlclient21 保留为共享客户端组件

## 端口与端点

- 本地预览默认 8000，仅 127.0.0.1；可用 --port 指定
- 生产 Nginx 80 / 443；HTTPS 已验收，源站 HTTP 返回 301，当前公网 HTTP 返回 403（见 I029）
- 原 MySQL 3306 / 33060 监听已随 I030 服务卸载关闭
- Weiss 正式入口：[Reading Notes · Weiss](https://notes.zzzping.top/weiss/notes/book_overview.html)；原 weiss.zzzping.top 独立域名已停用并删除 DNS，服务器旧站文件、Nginx vhost 和专属证书续期条目已于 2026-10-17 按 [I031](../issues/I031-retire-weiss-site.md) 清理

本文件严禁写入凭据或生产数据。`.env.example` 必须与环境变量名清单同步。
<!-- project-governance:managed:end -->

## 项目专属环境说明

本地阅读使用离线 HTML 或环回 HTTP；临时 HTTPS 验收单独创建测试证书和 Nginx 配置，验证后停止测试进程。生产域名、目录、证书和切换步骤以 [部署说明](../deploy/README.md) 为准，执行发布前读取实际状态。当前项目不要求用户设置持久环境变量；本地 TLS 验证器只对自己的子进程设置 `SSL_CERT_FILE`，不修改系统信任。未单独登记预发布环境。

新模板目录为 `/srv/reading-notes`，构建工作目录为 `/opt/reading-notes-builder`；Node/pnpm 只存在于构建主机。Web 主机的 Python/rsync/flock 是一次性发布命令依赖，不是 HTTP 运行服务。现网已在 I029 切换到 /srv/reading-notes/current/site，旧 /var/www/notes.zzzping.top 目录与配置保留为首次迁移恢复点；实际版本见 [生产发布记录](astro-production-report.md)。

I032 的构建 CSP/离线验收需要 Ego Lite 与 ego-browser CLI，在私有任务空间运行；临时 HTTP 服务只绑定回环随机端口，用后关闭。SSH、FTP/UFW、fail2ban 和 Certbot 自动续期均由运维交接执行，不用本地测试结果推断服务器状态。
