# 架构决策记录

<!-- project-governance:managed:start -->
当决策难以或代价高昂地回退、约束多个组件、改变安全或数据边界，或建立长期兼容性契约时，使用架构决策记录（ADR）。

建议命名：`ADR-NNN-short-title.md`。

ADR 记录持久的决策依据：背景、备选方案、最终选择、后果、验证方式和替代关系。实现步骤属于实施计划，批准与执行门禁属于变更控制记录；不要在 ADR 中重复维护这些内容，也不要用 ADR 隐藏尚未解决的分歧。

新建记录时复制 `_template.md`。复制后删除两行 `project-governance:managed` 标记；实际 ADR 全文由项目自主管理。状态值保持机器可识别，例如 `proposed`、`accepted`、`rejected`、`superseded` 或 `deprecated`；已生效记录不得静默改写，后续变化应新建 ADR 并建立替代关系。
<!-- project-governance:managed:end -->

## 项目专用 ADR 规则

采用顺序编号 `ADR-NNN`，记录日期、状态、依据、兼容影响和恢复方式，后续决策追加而不覆盖旧结论。架构范围由项目所有者确认。

当前决策：[ADR-001 · 书籍子项目](ADR-001-book-subprojects.md)。
