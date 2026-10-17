# I031：清理已退役 Weiss 独立站点

日期：2026-10-17。状态：完成。负责人：Codex；批准人：项目所有者。用户已确认 weiss.zzzping.top 停用且 DNS 解析已删除，并明确要求清理服务器上的旧独立站点文件和 Nginx 配置，保留 Reading Notes 主站中的 Weiss 笔记。

核查确认旧站独占 /var/www/weiss.zzzping.top、/var/lib/weiss-deploy、同名 Nginx vhost 与访问/错误日志；证书 SAN 仅包含旧域名，其他 vhost 未引用它。Reading Notes 当前版本为 /srv/reading-notes/releases/20261017T174039，其中 site/weiss 的 18 个文件另行保留。关联 [P031](../plan/P031-retire-weiss-site.md)、[T031](../test/T031-retire-weiss-site.md)、[M031](../milestone/M031-retire-weiss-site.md)、[ADR-004](../docs/decisions/ADR-004-retire-weiss-site.md)。

先核对精确路径、inode/device、嵌套挂载、引用和主站字节指纹，再移除旧 vhost 启用链接；nginx -t、平滑重载和保留站点复查通过后，删除旧站目录、部署记录、日志与可用配置，用 Certbot 删除旧域名专属证书和续期条目。重载前失败恢复启用链接；重载后、清理前若主站校验失败，同样恢复旧配置。后续重建旧独立站点需要重新发布及配置域名/证书。

文档影响：同步 .project-governance.json、docs/environments.md 与当前部署说明。项目技术栈、源码、教材内容、正式发布版本及环境变量保持，TECH.md 与 .env.example 的现有基线仍适用；历史发布记录保留原时点事实。服务器操作和验证证据存入忽略目录 tmp/weiss-retirement-20261017/，只记录证书元数据和哈希，不保存私钥内容。

2026-10-17 19:52（北京时间）已完成清理。14 个精确目标路径消失，保留的 30 项 Nginx 配置与 31 项证书文件/链接内容哈希均一致；主站、回滚版本、com 与 SICP 的 837 个文件保持。公开 HTTPS 验证 20 个地址均为 200 且字节一致，其中 Weiss 14 个 HTML 阅读页和 1 个 C 下载，另含主站首页及其他四书入口。根分区可用空间净增 7,680,000 字节（7.32 MiB）。
