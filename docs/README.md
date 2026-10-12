# 文档职责索引

<!-- project-governance:managed:start -->
每类事实只能有一个权威来源：

- `../TECH.md`：技术栈、架构、路径、依赖、兼容边界与技术栈变更索引。
- `../AGENTS.md`：短小的 Agent 入口和不可协商红线。
- `../.project-governance.json`：结构化项目设置与已登记命令。
- `governance/`：工作流、测试、安全、变更控制、发布和风险规范。
- `environments.md`：不含秘密的环境变量名、服务和端口清单。
- `rules/`：公式、统计口径、舍入、单位、币种、时间边界等业务/计算规则的权威文档。
- `decisions/`：受控级别下难以回退的技术与架构决策。

禁止在多个文件中手工维护同一事实。其他文档必须链接到权威来源。代码变更完成前必须评估并同步受影响文档。
<!-- project-governance:managed:end -->

## 项目文档

- [人类入口](../README.md)与 [书籍登记](../books/catalog.json)。
- [统一部署与恢复](../deploy/README.md)：实际发布步骤的唯一操作说明。
- [治理更新流程](governance-updates.md)。
- [新增子项目](adding-a-book.md)与 [本次迁移](migration-20261012.md)。
- [架构决策](decisions/ADR-001-book-subprojects.md)、[问题单](../issues/I001-project-merge.md)、[计划](../plan/P001-project-merge.md)、[测试设计](../test/T001-project-merge.md)与 [里程碑](../milestone/M001-project-merge.md)。
- [书籍内容与计算规则入口](rules/README.md)；专项正文规范随各书维护。
