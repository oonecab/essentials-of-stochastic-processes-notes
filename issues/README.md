# 问题单

<!-- project-governance:managed:start -->
每个需要持续协作、可独立评审的问题或决策使用一个文件。

建议命名：`issue_YYYYMMDD_HHMMSS_short-title.md`。

状态流转：`open` → `confirmed` → `in-progress` → `resolved` 或 `rejected`。

- 写明已观察事实、影响、范围、风险、验收条件与验证证据。
- 明确变更类型；技术栈、业务/计算规则、API/数据结构、安全、环境或用户可见行为的变更必须填写对应联动字段。
- 对文档影响作出结论：列出需要同步的权威文档；若无需更新，必须写明可复核的理由。
- 以追加方式记录有意义的调查与决策历史，不得抹去不利或失败的既有发现。
- 关联实施计划、测试设计、架构决策记录（ADR）与里程碑。
- 创建问题单时复制 `_template.md`，不得把模板本身当作真实问题单编辑。复制后删除两行 `project-governance:managed` 标记；实际问题单全文由项目自主管理。
<!-- project-governance:managed:end -->

## 项目自定义问题单规则

问题单使用 `INNN-主题.md`，按内容、程序、阅读界面、工具、治理或发布标明范围；明确用户需求、验收和文档影响。当前未接入外部跟踪系统或 SLA。

当前问题：[I001 · 合并两书](I001-project-merge.md)。
