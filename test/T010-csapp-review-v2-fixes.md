# T010：CS:APP 第二轮严格评估修复测试设计

状态：partially_completed / pending_browser_acceptance；关联 [I010](../issues/I010-csapp-review-v2-fixes.md)。

- F1：合法 SP/HTAB 首尾 OWS、非法字段名空白、Host 缺失/重复与 Expect 组合；维护 TCP 服务器模式及 C/Python 一致性。先证实旧源码失败。
- F2：必要算法和显式自测在严格 `-DNDEBUG`、Python `-O` 下执行；错误变体必须非零，保留告警门禁和必要实际计数。
- F3：同版原题/答案读回；小端 LP64 字符合法别名的两种更新顺序得到 1/257；明确宿主模型和 x86 汇编边界。
- F4：实际 CGI 持有连接、父进程可处理重叠请求，SIGCHLD 循环回收及描述符所有权；慢请求、合并通知与无残留孩子。
- F5：专用浏览器实际通过 HTTP 代理；允许正文、403、对应日志、慢上游并发及不绕过本地目标的证据。
- F6：同一负载、同一可观测空间分母和环境，单独列吞吐与空间结果，解释测量精度及局限。
- F7/F8：MathML 指数结构与 data-tex 一致、页表编号推导，并实际查看渲染。
- 集成：`python3 tools/project.py check --book csapp`、`check --quick`、`build`，受影响页桌面/390px 实际阅读，包与维护源绑定。

证据根目录：`tmp/csapp/review-v2-fixes/`。历史执行与历史哈希保留；当前状态仅由本次实际覆盖支持。

## 本地执行结果

最终完整执行：`python3 tools/project.py check --book csapp`，通过。报告 `tmp/project-check/20261014T213638-7e7waj6i/csapp/report.json` 绑定当前 14 页、登记程序维护源及本轮回归。42 组程序（32 对 C/Python、8 个独立 C、2 个独立 Python）通过；74 个登记阅读代码块同步。额外空间测量源由专项回归逐字核对。原有 Part I/II/III 回归继续执行，含 24,490 次分配器区间操作和信号/进程边界。

| 评估项 | 修前证据与修后结果 | 当前状态 |
| --- | --- | --- |
| F1 HTTP | 同一最终 150 项 TCP 用例，旧源码通过 112 项，当前 150/150；process/select/thread/pool/Python，客户端保持写侧打开。合法 OWS 接受，Host/消息框架错误先于 Expect，非法字段名和控制字节仍拒绝。 | fixed_verified |
| F2 断言 | 旧源码普通/关闭断言执行 22/24，错误变体检出 20/42；当前 24/24、42/42。必要函数先执行，显式失败退出，成功数量来自已执行比较。严格告警未削弱。 | fixed_verified |
| F3 3.33 | 原题与答案 PDF 283–285、376–377 读回，原两种候选保留并补充不重叠条件。小端 LP64 合法字符别名得到 1/257，不重叠控制相等；严格优化、关闭断言及 ASan/UBSan 通过，错误重排变体被拒绝。 | fixed_verified |
| F4 11.8 | 旧 CLI 无异步 CGI 服务；当前实际 C 父进程执行 C/Python CGI，重叠请求、合并 SIGCHLD、父暂停后响应 EOF、描述符与信号状态恢复、提前关 stdin、失败 exec、5 秒超时后继续服务等 8 组通过。 | fixed_verified |
| F5 12.39 | 仅做工具能力探测：代理上下文创建成功，页面创建返回 `Target.createTarget is not allowed`，上下文释放成功。未发出真实浏览器代理请求。 | pending_browser_acceptance |
| F6 9.20 | 64/512 次同轨迹分配，first-fit/next-fit/libc 私有 zone 共 6 组，重复 3 次。峰值请求载荷分别 4280/34424 B；toy 后备块区域 65536 B、libc 1048576 B。每步页区域并集与 size_allocated 交叉核对；仅统计活动块的错误分母变体被拒绝。 | fixed_verified |
| F7 2.85 | 两处负 t 指数完整位于 MathML，data-tex 同步；旧页和缺指数变体均被结构检查拒绝，1440/390px 实际读图确认。 | fixed_verified |
| F8 9.6.3 | PDF 857 读回；编号 8（从 0 起算）即第 9 个区域，9215 = 8×1024+1023，页表合计 16 KiB 保持。 | fixed_verified |

专项证据：`http-cgi/headers-before-final-cases/report.json`、`http-cgi/headers-epipe-final/report.json`、`http-cgi/cgi-epipe-final/report.json`、`assertions/before/report.json`、`assertions/after/report.json`、`content/source-readback.json`、`proxy/browser-attempt.json`。最终完整检查目录中的相应专项报告是最后维护源与工具版本的执行证据。第一次快速检查在修改尚未合并时检出 ch09 阅读副本不一致，记录仍在 `tmp/project-check/20261014T212352-d_o_fzj_/report.json`；随后同步后通过。早先完整检查 `20261014T212819-tb4_331q` 在最后一个内容检查加入前载入了模块，因此以 `20261014T213638-7e7waj6i` 为最终结果。

独立复核：`assertions/independent-review.json` 核对 CGI/别名/空间机制，`independent-assertions.json` 核对 11 个断言修订源及 42 个错误变体，均无未关闭代码问题。后者单独重跑 F6 后更新的 C allocator 控制组，避免将其较早的历史哈希当作当前执行证据。CGI 提前关闭 stdin 的中间错误实现及修复后证据都保留在 `assertions/cgi-independent/`、`http-cgi/early-close-before-final/`。

## 真实阅读与集成

本地 QA 包 `20261014T212827`：7 个修订页面（2、3、5、8、9、11、12 章）分别在 1440/390px 全部展开检查，共 14 组；页面溢出、越界元素、SVG 文本越界和坏图片均为 0。人工逐张查看 18 张截图：2.85、3.33、显式自测、连续读取代码、9.20 说明及数据表、9.6.3、CGI 和代理待验收说明，分别覆盖桌面/手机。长代码与表格保留局部横向阅读。

实际点击验证深链接展开代码祖先、折叠后重开、手机目录点击后关闭且 `aria-current=location`、返回三书书架；鼠标横向滚动代码块且页面不溢出。点击下载 `ch09_space.c`，下载字节 SHA-256 与维护源相同。原始结果为 `browser/geometry.json`、`reading-targets.json`、`interactions.json`、`toc-version.json`、`bookshelf-return.json`。浏览器身份按实际 userAgent 记录；版本 CDP 方法不可用，不推测精确发行版本。浏览器工作空间已结束。

全仓快速检查 `python3 tools/project.py check --quick` 已通过，记录 `tmp/project-check/20261014T213651-srdylf5o/report.json`；最终审阅记录写回后再次通过，记录 `tmp/project-check/20261014T214609-a24pzva0/report.json`。`python3 tools/project.py doctor` 检出登记工具及本地 Nginx/OpenSSL 均可用。

最终构建 `python3 tools/project.py build` 生成 `deploy/portal-releases/20261014T214609/`：232 个文件、52 个 HTML、36 个阅读页，4379 个本地引用检查通过。归档 SHA-256 为 `d2dbc0769a9ea5378ae32e27f19ccef2fdf89483cef407a1c7098ed19ac51de6`。与已验读包比较，没有增删文件，仅 10 份 CS:APP 审阅 JSON 更新；全部 HTML、CSS、JS 与代码文件字节相同，因此上述阅读证据适用于最终包。141 份包内非 HTML 维护材料也与当前源逐字匹配，见 `tmp/csapp/review-v2-fixes/release-binding.json`。

`python3 tools/project.py verify-release --release-id 20261014T214609` 通过：本地 HTTPS 核对 229 个文件、路由与 9 个入口跳转；PDF Range 返回 206，32–63 字节与包一致。报告 `tmp/release-check/20261014T214609-x4k_istc/https-verification.json`；临时 Nginx 已停止。这是本地集成证据，不是线上发布观察。

最终独立范围核对在 `tmp/csapp/review-v2-fixes/final-source-binding.json`：97 个报告哈希、120 份登记程序来源有当前绑定或未改依据，419 道原题、114 处原文及译句、原有章节标题、样式、脚本与锚点保留。11 章 CGI 原文旁的实现说明单独登记为本次修订。`final-change-scope.json` 记录本轮 43 个已有文件修改、9 个新增文件，无快照文件删除、无新增行尾空白；它只比较本任务快照范围，不声称对其他历史改动重新审计。

## 证据边界与文档影响

空间实验测的是两端统一的“块存储后备区域”，包括空闲块、缓存和区域内元数据，均排除区域外控制结构。Darwin 私有 scalable zone 与当前页大小属于实验条件；结果不能推出默认 malloc、RSS、总内存开销或一般分配器优劣。空间测量不启用 sanitizer，以保留真实 libc 后端；普通程序、别名及进程回归按对应配置保留 ASan/UBSan。

12.39 仍须取得真实浏览器经代理的允许正文/ALLOW、403/BLOCK/无上游请求、慢上游时第二页并发返回和本地地址不绕过代理的证据。已有协议测试及本轮阅读页面验收都不替代这项实验。当前问题单与里程碑保持未全部完成。

已同步正式 HTML、维护源、程序目录/约定、7 章审阅、source_reading_review、reading_review、validation、TECH、规则索引及 I/P/M/T010；I/P/M/T007 补充当前待验收状态，旧历史完成记录保持其原证据范围。没有核心技术栈/服务/持久环境变量改变，因此无需修改技术栈清单、环境说明或 ADR。既有 Y86 特项、历史其他页的阅读与 Linux/TSan/公网边界均未扩大。本次没有提交、推送或部署。
