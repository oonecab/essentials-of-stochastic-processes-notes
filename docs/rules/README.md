# 业务与计算规则

<!-- project-governance:managed:start -->
本目录保存公式、统计口径、精度、舍入、单位、币种、时间边界和异常处理等规则的唯一权威定义。

- 每项重要规则使用独立文件和稳定规则 ID。
- 修改规则时必须同时更新受影响代码、测试设计、可执行回归测试、API/报表/用户说明。
- 规则文件必须说明生效版本或日期，并保留只追加的变更记录。
- 示例应明确输入、输出、单位和边界，尽量与自动化测试共用夹具。
- 不得用代码注释代替权威规则文档，也不得在多份文档中分别维护同一公式。

新建规则时复制 `_template.md`。其中的 `project-governance:managed` 标记只表示 `_template.md` 本身由生成器维护；复制为实际规则文件后应删除两行标记，实际规则全文由项目自主管理。
<!-- project-governance:managed:end -->

## 规则索引

| 规则 ID | 名称 | 权威文档 | 生效版本/日期 | 责任人 |
|---|---|---|---|---|

## 本项目规则职责

教材陈述、例题、公式和推导由对应正式 HTML 维护；计算实现与数值接口由各书源码/正文及运行说明维护。本次只调整目录与发布接入，不新增计算规则。

- 随机过程：[维护约定](../../books/stochastic/agent.md)、[章节规范](../../books/stochastic/notes/README.md)、[程序接口](../../books/stochastic/code/README.md)。
- Weiss：[维护约定](../../books/weiss/agent.md)、[章节规范](../../books/weiss/notes/README.md)、[程序说明](../../books/weiss/notes/book_overview.html#program-guide)、[原图例接口](../../books/weiss/c/README.md)。

跨书共有的规则登记方式遵循本目录规范；发生公式、精度、单位或边界变更时，在此链接受影响的权威条目、问题单和测试，正文保留原结论与修正依据，不另抄一份算法或定理。
