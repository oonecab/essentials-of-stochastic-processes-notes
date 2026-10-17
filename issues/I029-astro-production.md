# I029：Astro 静态站点生产发布

日期：2026-10-17。状态：实施中。负责人：Codex；批准人：项目所有者。用户在 I028 本地迁移完成后明确要求提交、推送远端并部署服务器，本次授权覆盖 Git 主分支快进与 notes.zzzping.top 生产发布。认证信息仅通过 SSH 交互输入，不进入文件。

范围：将已验收的五书 Astro 构建及部署工具推送至 origin/main，在 Ubuntu 22.04 上安装最小权限发布工具，并将 Nginx 静态 root 切换到 /srv/reading-notes/current/site。54 页、1434 道原书题、正文、程序、URL、锚点和 PDF 页码链接沿用 I028，不改变教材计算规则。依据 [ADR-002](../docs/decisions/ADR-002-static-first-astro.md)，执行 [P029](../plan/P029-astro-production.md)，验收 [T029](../test/T029-astro-production.md)，里程碑 [M029](../milestone/M029-astro-production.md)。

已核实起点：本地 b70ba6a，远端 main 为 b2aeff3；工作区干净，主分支可以快进。线上仍为旧布局 release 20261017T151424；Ubuntu 22.04.3、Nginx 1.18.0、Python 3.10.12、rsync 3.2.7、util-linux flock 2.37.2。/srv/reading-notes 尚不存在。证书和站点 TLS 配置已存在。

发布风险是目录迁移、权限、systemd 沙箱、CSP 生效和 Nginx 重载。先保存旧 current、站点配置、元数据指纹及其他虚拟主机状态；新目录准备时旧站继续服务。安装已审核的 CSP snippet 后，以 reading-notes 用户执行发布服务，最后只替换既有站点的静态 include，保留证书、TLS、ACME 和日志约定。任何配置、源站指纹或公开关键路径失败均恢复旧站配置并重载。旧目录及恢复材料保留，不清理历史版本。

文档影响：更新 TECH.md、.project-governance.json、docs/environments.md、部署文档及发布记录；环境变量没有新增，.env.example 的 ASTRO_TELEMETRY_DISABLED 仍适用。I028 记录保持本地阶段的历史事实。数学、API、数据库和业务规则不变，书级历史审阅与迁移绑定保持。
