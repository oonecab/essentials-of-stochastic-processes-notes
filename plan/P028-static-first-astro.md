# P028：静态迁移实施顺序

关联 [I028](../issues/I028-static-first-astro.md)、[T028](../test/T028-static-first-astro.md)、[M028](../milestone/M028-static-first-astro.md)。

1. 固定当前源码、发布页面与既有检查证据；比较实际目录和用户给定范围。
2. 通过 ADR-002 登记 Astro / Node / pnpm 的构建边界，建立空壳、逐页 parity 和离线检查。
3. 测度概率六页试点；完成重复构建、独立 Python、四断点、无 JS、断网和深链后作 Go/No-Go。
4. 通过试点后依次迁移视觉群论、随机过程、Weiss、CS:APP；每本书独立核验、追加证据并提交。
5. 建立 dist allowlist、不可变 release、临时链接加 rename 原子切换、失败恢复；本地验证 Ubuntu 发布脚本和 Nginx。
6. 完整运行根入口与 pnpm 检查，记录产物身份、耗时、体积、剩余风险及最终状态。

新正文以逐章受控 HTML 保存，MathML/SVG 和源码显示副本原样搬运。共享资源按原字节去重；现存 HTML 在迁移期作为可复核兼容产物保留。输出和截图始终位于忽略目录。正文变化与迁移不混在一批处理。

执行结果：六个阶段步骤均完成。本地结论 Go，目标环境保留项及命令退出码见 [最终报告](../docs/astro-migration-report.md)。
