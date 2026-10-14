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

教材陈述、例题、公式和推导由对应正式 HTML 维护；计算实现与数值接口由各书源码/正文及运行说明维护。跨书规则由本目录登记，教材模型保持在对应正文中。

跨书的来源核对、全书规划、伴读方法、题解、代码与阅读验收采用 [RN-001 读书笔记共同标准](../reading-notes-standard.md)（v1，2026-10-14）。[新书接入](../adding-a-book.md)与[模板](../templates/reading-notes/README.md)引用该标准；以下各书文件补充本书模型、范围和具体约定，既有更细要求继续生效。

- 随机过程：[维护约定](../../books/stochastic/agent.md)、[章节规范](../../books/stochastic/notes/README.md)、[程序接口](../../books/stochastic/code/README.md)。
- Weiss：[维护约定](../../books/weiss/agent.md)、[章节规范](../../books/weiss/notes/README.md)、[程序说明](../../books/weiss/notes/book_overview.html#program-guide)、[原图例接口](../../books/weiss/c/README.md)。
- CS:APP：[维护约定](../../books/csapp/agent.md)、[章节规范](../../books/csapp/notes/README.md)、[程序约定](../../books/csapp/code/README.md)、[原文来源清单](../../books/csapp/notes/source_excerpts.json)；定宽表示、C11 语义、ABI、流水线与缓存的模型由正式 HTML 定义。新增例子见 [T003](../../test/T003-csapp-companion.md)；流水寄存器开销、分配上限、缓存写策略、浮点精度前提及来源修订见 [I004](../../issues/I004-csapp-source-reading.md) 和 [T004](../../test/T004-csapp-source-reading.md)。

第二部分链接符号/重定位、信号状态与进程生命周期、页表与分配器契约分别由[第 7 章](../../books/csapp/notes/chapter07_linking.html)、[第 8 章](../../books/csapp/notes/chapter08_exceptional.html)、[第 9 章](../../books/csapp/notes/chapter09_virtual_memory.html)定义，执行范围与原书校注见 [I005](../../issues/I005-csapp-part-two.md) 和 [T005](../../test/T005-csapp-part-two.md)。

跨书共有的规则登记方式遵循本目录规范；发生公式、精度、单位或边界变更时，在此链接受影响的权威条目、问题单和测试，正文保留原结论与修正依据，不另抄一份算法或定理。

第二部分修订的信号临时等待掩码、作业清理与分配搜索游标契约见 [I006](../../issues/I006-csapp-part-two-review-fixes.md) / [T006](../../test/T006-csapp-part-two-review-fixes.md)，权威正文和维护程序仍在上述章节及程序约定中。

第三部分可靠 I/O 与文件共享、地址和协议边界、并发与同步的契约分别由[第 10 章](../../books/csapp/notes/chapter10_system_io.html)、[第 11 章](../../books/csapp/notes/chapter11_network.html)、[第 12 章](../../books/csapp/notes/chapter12_concurrency.html)定义，执行与校注范围见 [I007](../../issues/I007-csapp-part-three.md) / [T007](../../test/T007-csapp-part-three.md)。

第三部分修订的 HTTP 首部提前拒绝、接入窗口与活动连接处理、计时子进程取消规则见 [I008](../../issues/I008-csapp-part-three-review-fixes.md) / [T008](../../test/T008-csapp-part-three-review-fixes.md)，权威正文与程序约定仍在第 11/12 章及源码说明中。

第二轮严格评估中的 HTTP 字段空白/Host 先后规则、断言关闭后的必要自测、3.33 别名条件、CGI 子进程所有权与分配器空间统计口径见 [I010](../../issues/I010-csapp-review-v2-fixes.md) / [T010](../../test/T010-csapp-review-v2-fixes.md)。权威定义仍在相应正式正文与源码说明；12.39 的代理浏览器实验按逐题状态保留待验收。
