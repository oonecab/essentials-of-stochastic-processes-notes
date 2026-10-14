# T008：第三部分评估修复验证

状态：completed_locally；关联 [I008](../issues/I008-csapp-part-three-review-fixes.md)。

## 测试设计

- Expect：真实回环客户端只发送头部，保持写端打开且不发送正文；C process/select/thread/pool 和 Python 应收到完整 417。首部未完整不能提前响应；完整消息仍拒绝；无 Expect 的分段 POST 等到正文完整后成功。保留 HEAD、非法首部、重复长度及代理调用的兼容检查。
- 接入窗口：窗口前接入，窗口后补齐合法 HTTP/echo 输入仍得到完整结果；窗口后不再接入新工作；停滞客户按自己的期限清理。持续回归通过受控时间边界执行同一状态机，另保留默认 120 秒的真实边界验收。旧条件应被正式回归检出。
- 计时器取消：调用方忽略或屏蔽 SIGTERM，输入已准备时应及时返回并回收子进程；原 SIGTERM/SIGUSR1 处理设置与掩码保持，五秒部分行超时回归保留。旧清理信号应被回归检出。
- 以严格 C11、适用 pthread、ASan/UBSan 编译执行；根入口 `python3 tools/project.py check --book csapp` 与 `check --quick`，以及 `python3 tools/project.py build`。
- 第 11/12 章桌面和 390px 实际阅读：改动解释、代码深链接与展开、局部滚动和章节导航；核对源码副本、审阅绑定、最终本地包。

## 证据

起始快照与后续执行产物位于 `tmp/csapp/review-fixes-part3/`。历史 T007 结论保留其当时范围；本轮将真实握手、跨接入窗口、继承 SIGTERM 环境作为新增覆盖。

## 修复与回归结果

- Expect：同一正式回归在旧快照运行 85 案例，61 通过、24 失败，失败为四种 C 模式各 6 个只发送 Expect 首部的等待场景；修复后 85/85 通过，全部保持客户端写端打开。新增 request_ready 表示可生成最终响应，request_size 保留消息完整性语义。记录在 `tmp/csapp/review-fixes-part3/http/before/report.json` 与 `http/after/report.json`；前缀、正文和重复长度的兼容检查一并通过。
- 接入窗口：正式短窗口用例先检出原循环在截止时丢弃活动客户。修复后 HTTP、echo 跨窗口完成，停止接入、停滞客户期限和 listener 关闭均通过。默认 120 秒 CLI 另在第 119 秒接入、第 120.4 秒补齐：select 返回完整 200/25 字节正文，echo 返回完整行；窗口后新连接被拒绝。两模式预算 2、实际接入 1，因此按既有语义以 1 表示未达到连接额度，不能把这一退出码解释为请求处理失败。证据 `window/before.json`、`window/after.json`、`window/default-120s.json`。
- tfgets：旧快照在忽略/屏蔽 SIGTERM 时约 5.05 秒才返回现成输入；修复后的定向测试约 0.04 秒返回。正式用例核对正确行、信号 action/mask 恢复与无未回收孩子；改回 SIGTERM 的两个变异均检出约 5 秒延迟。原三种实现的真实五秒部分行测试保留。证据 `tfgets/before/tfgets_cleanup_report.json`、`tfgets/after/tfgets_cleanup_report.json`。

上述时间是本机观察，不构成实时或性能保证。严格 C11、pthread、ASan/UBSan 实测通过。

独立集成复核检查 HTTP/事件循环及对应正文，并额外执行 271 个前缀、6 个响应边界和两个“跨窗口补齐 Expect 首部/普通 POST 正文”的真实组合场景。发现窗口 HTTP 断言原先仅匹配子串后，已收紧为精确状态行、唯一 Content-Length、准确正文长度和全部 fixture 字节；正式服务器脚本重跑通过，默认长测原始响应独立重解析通过，没有将补解析表述为第二次长测。当前范围无未闭合发现，证据 `tmp/csapp/review-fixes-part3/independent-review.json`、`window/complete-response-check.json`。该独立复核人曾实施 tfgets，记录明确不将其 tfgets 自审作为独立代码审阅；主任务另读回该实现与正式测试。

收紧断言并完成四份 HTML 源码副本同步后，最终 `python3 tools/project.py check --book csapp` 通过，证据 `tmp/project-check/20261014T195029-yzxp2owq/report.json`。检查执行 41 组程序、既有三部分回归和新增 85 个握手场景。首次完整检查及全仓静态检查也通过，分别记录于 `20261014T194656-7enbhtne` 和 `20261014T194709-6utywo5_`；最终状态以本段指定的新版记录为准。

## 阅读与文档

ego-browser 同一 TaskSpace 检查本地构建包的第 11/12 章，1800/1440/1024/390px 共 8 组全展开布局没有整页溢出、内容越界、SVG 文字越界或破图。主任务逐张查看 Expect、HTTP 核心导读、12.31 回收机制、接入窗口说明的 8 张桌面/窄屏截图；实际点击源码展开、12.31 到实现的深链接、移动目录，核对局部横向滚动、目录收起及当前位置。具体范围与截图保存在 `tmp/csapp/review-fixes-part3/browser/`，几何扫描与目视阅读分别记录。

维护源、四份阅读副本、程序约定、两章解释、TECH、规则职责索引和本批治理记录已联动；逐章及汇总审阅保留历史哈希和原证据，新增修复范围及当前绑定。原文摘录、习题题干、章节锚点、样式和脚本与起始快照相同。没有核心技术栈、环境变量、服务或正式端口变更，因此机器配置、环境文件和 ADR 无需修改。

本轮证据限 macOS/POSIX、本地回环协议和本地包阅读；未新增 Linux 原生、ThreadSanitizer、长时间压力或生产验收，不将本次定点修订扩大为全部 419 题重新证明。

最终文档与审阅绑定同步后，`python3 tools/project.py check --quick` 三书静态检查通过：`tmp/project-check/20261014T195709-hop1mqoq/report.json`。本批范围核对见 `tmp/csapp/review-fixes-part3/final-scope.json`，起始 165 文件中 147 个保持字节一致，其余均为登记影响范围；新增文件为 HTTP 回归与 I008/P008/T008/M008。

## 最终本地包

`python3 tools/project.py build` 生成 `deploy/portal-releases/20261014T195816/`，含 230 个文件、52 个 HTML、三书合计 36 个阅读页，4375 个本地引用检查通过。`python3 tools/project.py verify-release --release-id 20261014T195816` 实际通过：本地 Nginx HTTPS 检查 227 个资源、9 个入口重定向与 PDF Range（206），临时 Nginx 已停止；证据 `tmp/release-check/20261014T195816-ez77vqm7/https-verification.json`。

实际浏览器使用的包 `20261014T195030` 与最终包仅五份审阅/验证 JSON 不同，其余全部资源逐字一致；受影响两页和四份源码的 HTTP 响应、最终包及当前维护源分别按发布哈希核对，见 `tmp/csapp/review-fixes-part3/final-package-comparison.json`。保留所有历史审阅范围，本轮为本地修复与验收，未提交、推送或生产发布。
