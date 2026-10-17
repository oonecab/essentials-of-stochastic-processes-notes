# M029：生产发布里程碑

状态：带保留完成。关联 [I029](../issues/I029-astro-production.md)、[P029](../plan/P029-astro-production.md)、[T029](../test/T029-astro-production.md)。

完成条件：已验收 Astro 源码推送远端主分支，Ubuntu 原子发布生效，源站和公网验证通过，实际阅读验收完成，旧站恢复单元保留，权威环境文档与最终 Git 状态一致。

2026-10-17 已部署 20261017T174039，源站及公网 HTTPS 全量验证通过。真实 Ubuntu 发布服务与 13 项恢复回归通过，165 个浏览器视图及五书跨章点击通过。旧布局恢复脚本、目录与配置保留；公网 HTTP 403 作为已有边界记录。最终 Git 验收及证据见 [发布记录](../docs/astro-production-report.md)。
