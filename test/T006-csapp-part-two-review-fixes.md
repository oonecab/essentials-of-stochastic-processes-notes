# T006：第二部分评估修订验证

状态：passed_locally；关联I006/P006/M006。

## 设计

- 清理：受控直属子进程改变进程组后，quit和EOF均应在有界时间内返回并回收；普通同组作业、自然已退出孩子和停止作业保持正常。信号目标必须是尚未回收的已登记直属PID或其作业组，不触及测试所有权外的进程。先记录原实现卡住及任务清理，再验修复。
- 掩码：调用前已屏蔽通知信号且通知pending时，模板应让handler执行、结束循环并恢复原掩码；从原教学模板直接提取编译的有界用例必须能够区分旧写法和修订写法。
- 分配器：first/next-fit×两种尾部形式，以独立活动区间/游标模型核对选址、分裂、四种合并、有效载荷、零与过大/耗尽失败；失败前后整段arena及控制状态一致。固定种子与显式wrap-around案例；注入next-fit回退成first-fit或游标错误的变异应被检出。
- 集成：严格C11和适用ASan/UBSan；python3 tools/project.py check --book csapp、check --quick、build及verify-release；源码/阅读副本逐字同步，旧审阅哈希保留，更新当前绑定与范围。
- 阅读：第8章8.5.7及shell导读、完整代码和深链接，在1440/390px真实浏览器呈现。必要的全章几何扫描与定点目视分开记录。

## 执行结果（2026-10-14）

旧缺陷已经重新复现：`tmp/csapp/part2-review-fixes/independent-shell-red.json` 记录直属孩子迁到shell组后，旧cleanup在750ms观察窗仍阻塞，只有精确终止持有PID后才完成回收；`template-red.json` 直接提取旧HTML模板，预先屏蔽且pending的SIGCHLD触发保护退出42。修复版相同shell触发见 `independent-shell-green.json`，约10.7ms退出0；这是一次本机观察，不是时限性能承诺。

正式回归在严格C11、ASan/UBSan下执行：10个quit/EOF场景覆盖普通、停止、自然退出、迁组后原组消失/仍存在，全部退出0且测试救援次数为0；另验证仍登记的已退出组长保留原组清理、注入EPERM后不阻塞且报告失败。HTML原样提取编译，在调用者原先屏蔽/未屏蔽SIGCHLD两种情况下都递交通知、保留无关SIGUSR1屏蔽、恢复保护及原掩码。8条错误变异执行被检出，包括旧实现两种迁组场景、错误fallback、提前reap、跳过cleanup、漏解除通知信号和两种错误恢复掩码。

分配器独立活动区间补集及游标参考覆盖 first/next-fit × full/free-only footers：4组各6000次固定种子混合动作，加定向与恢复操作共24490次，初始化/结束检查另计后为24562步。7606次零值、过大和耗尽失败均保持整段arena、游标、模式及合并计数；存活载荷持续核对。两种next-fit各经过显式环回，分别379/575次选址有别于first-fit。丢后向合并、next当first、遗漏游标修复3个变体先失败，真实代码随后在-DNDEBUG下通过。

完整命令与结果：

| 验证 | 结果与证据 |
|---|---|
| `python3 tools/project.py check` | 全仓通过：`tmp/project-check/20261014T104717-f51x4xp_/report.json`。此时信号回归为7条错误变异版本。 |
| `python3 tools/project.py check --book csapp` | 测试自身收紧后完整重跑通过：`tmp/project-check/20261014T104957-jd33ad7l/report.json`，最终8变异及所有原有程序回归。 |
| `python3 tools/project.py check --quick` | 全仓通过：`tmp/project-check/20261014T104958-p7j9y0_i/report.json`。 |
| 独立代码与执行复核 | `tmp/csapp/part2-review-fixes/independent-review.json`，`passed_scoped_independent_review`、零未闭合发现；记录最终四份文件哈希及不同目录执行。 |
| ego-browser阅读 | `tmp/csapp/part2-review-fixes/browser/review.json`；第8章1440/390px、8张截图逐张目视；44个main details全部展开后两宽度页面横向溢出为0，目录/代码展开/深链接通过。源码下载HTTP200，下载与阅读副本SHA一致。 |
| `python3 tools/project.py build` | 最终本地包 `deploy/portal-releases/20261014T105127/`：204文件、49HTML、33阅读页。 |
| `python3 tools/project.py verify-release --release-id 20261014T105127` | 本地Nginx HTTPS通过201个非重定向文件、9个入口重定向、MIME/CSP及PDF范围请求；`tmp/release-check/20261014T105127-4onp7488/https-verification.json`，临时Nginx已停止。 |
| 候选/最终包比较 | `tmp/csapp/part2-review-fixes/final-package-comparison.json`：仅5个审阅JSON更新，HTML/CSS/源码均与浏览器验收候选逐字相同。 |
| 范围与当前绑定 | `tmp/csapp/part2-review-fixes/scope-and-bindings.json`：当前页面/代码/测试工具哈希一致；另外10阅读页和3份来源清单与本轮基线相同。 |

## 调查、联动与边界

独立复核修复了测试本身的两处判定风险：fallback错误变体改为依据首次组kill返回值，避免二次探组时序；正向要求零次测试救援，并用“直接跳过cleanup”变异验证退出后的测试善后不会冒充实现成功。最初0.6秒外部保护遇到一次新编译ASan进程启动超时，按实际启动成本调为1秒；旧失败保留在 `tmp/csapp/part2-review-fixes/ch08/regressions-v1/failure.json`，模板内部保护仍为0.25秒。正式和独立最终执行均通过，未忽略失败断言。

本轮同步维护C、逐字HTML副本、8.5.7/导读/8.26解释、程序说明、规则职责索引、TECH、逐章review、validation、reading及source_reading增量记录。原书引句、题目条件、原有章节结构和旧审阅哈希保留。运行时/兼容基线/服务约定未变，因此机器治理配置、环境文档和ADR无需变更。规则输入输出为进程身份与信号掩码，不涉及金额、单位、舍入或日期口径。

所有执行与阅读结论限本机Darwin/POSIX及浏览器模拟视口；权限失败采用受控调用注入。引用原REA评估，本轮没有新增REA执行；没有重新宣称全书逐题源审。清理负责退出时仍登记的作业组与未回收直属PID，不跟踪已从表中删除的历史作业后代。没有提交、推送或生产部署。

交付预览：`http://127.0.0.1:55788/` 指向最终本地包。`tmp/csapp/part2-review-fixes/final-preview.json` 逐字核对首页、全部11个CS:APP阅读页、shell源码及验证摘要共14文件；任务候选及旧预览服务已停止，最终预览保留。

记录与文档同步后再次全仓quick通过：`tmp/project-check/20261014T105357-y_0iqsus/report.json`；`git diff --check`通过。
