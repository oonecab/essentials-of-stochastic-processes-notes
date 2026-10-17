# I028：静态优先 Astro 迁移

日期：2026-10-17。状态：带保留完成。本地迁移及发布演练 Go，目标 Ubuntu/systemd 实机验收保留。负责人：Codex；范围和本地执行授权来自本次用户附件。关联 [P028](../plan/P028-static-first-astro.md)、[T028](../test/T028-static-first-astro.md)、[M028](../milestone/M028-static-first-astro.md)、[ADR-002](../docs/decisions/ADR-002-static-first-astro.md)。

目标是让五书正式笔记由 Astro 构建为可离线打开的单文件 HTML，生产继续只提供静态文件。数学、题号、小问、来源、锚点及 PDF 页码链接保持。构建依赖和运行时边界、逐书迁移及失败恢复遵循用户 Phase 0–8；本轮授权包括本地提交，不包含远程部署。

起点为提交 `b2aeff3`，工作区干净。`doctor` 和完整 `check` 均退出 0，13 个登记命令全部通过，报告 `tmp/project-check/20261017T154418-nls22x5i/report.json`。原始日志、54 页副本、正文/MathML/SVG/锚点/链接快照与 SHA256 清单位于 `tmp/reading-notes-migration/baseline/`；原发布包 `20261017T151424` 的 54 页维护源哈希与当前文件一致，另保存发布视图作为对照。

实际范围为 54 页、1434 道原书习题、CS:APP 36 道补充自测、21353 个 MathML、486 个 SVG。452 个陈述容器按既有 `statement` / `source-statement` 标记统计，包含陈述、定义及原文容器；Weiss 没有此类标记，不能把容器数冒充跨书编号定理总数。

影响面包括内容维护路径、共享布局和脚本、独立 Python 校验与旧 HTML 的绑定、统一打包、发布 allowlist、CSP、部署模板及治理文档。计算规则和程序算法保持，源码/正文副本逐字核验；历史数学审阅不重写。旧 HTML 与构建器在新输出通过 parity 前保留。CS:APP 12.39 代理浏览器实验的历史未验收状态继续保留，迁移验收不替它宣称完成。

风险：模板空白影响行内文字、资源内联遗漏、元数据误发布、离线链接依赖、依赖版本漂移和切换失败。以逐页语义/原始片段对比、禁止外部资源、重复构建、浏览器操作与失败回滚测试控制。若用户列出的停止条件成立，停止全量迁移并保留旧站。

执行状态与命令证据追加到 [T028](../test/T028-static-first-astro.md)；最后交付说明汇总未验证范围。

最终报告见 [迁移交付](../docs/astro-migration-report.md)，结构化证据见 `docs/astro-migration-evidence.json`。

后续生产授权与 Ubuntu 实机验收记录于 [I029](I029-astro-production.md)；本文件保留 I028 完成时的本地交付边界。
