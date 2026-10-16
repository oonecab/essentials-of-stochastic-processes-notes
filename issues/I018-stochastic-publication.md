# I018：随机过程全书解释修订的提交与发布

创建日期：2026-10-16。状态：in_progress。执行人：本任务 Codex；范围和生产生效确认人：项目所有者。

授权依据：用户在本次对话明确要求“提交推送到远端，同时部署到服务器”。范围为 I015— I017 的随机过程全书解释、证明入口、逐项审阅及回归检查，提交到 `oonecab/reading-notes` 的 `main`，再通过现有统一发布流程部署到 `https://notes.zzzping.top/`。

发布单位是完整三书静态站点包。采用独立版本目录，校验来源、归档与逐文件哈希；保存现有 `current` 和 Nginx 配置后原子切换。配置、CSP、响应或关键阅读路径验收失败时，同时恢复原链接与配置，并验证恢复结果。服务器登录使用现有认证渠道，凭据及临时认证材料不进入仓库。

文档影响：内容标准、计算规则与技术事实已经在 I015— I017 同步；本次增加发布工作记录及最终机器摘要。技术栈、长期环境、域名和发布机制保持现有约定，无新增迁移或 ADR。书级审阅记录保留各轮实际时间及验证范围，发布事实单独记录。

关联：[P018](../plan/P018-stochastic-publication.md)、[T018](../test/T018-stochastic-publication.md)、[M018](../milestone/M018-stochastic-publication.md)。执行材料保存在忽略的 `tmp/stochastic-publication-20261016/` 与 `deploy/reports/<release-id>/`。
