# T007：CS:APP 第三部分验证

当前验收状态（I010 增量复核）：12.39 的真实浏览器经代理实验仍待完成；下文为原批次历史记录，其 `completed_locally` 不覆盖该待验收项。更新结果见 [T010](../test/T010-csapp-review-v2-fixes.md)。

状态：completed_locally；关联 [I007](../issues/I007-csapp-part-three.md)。

## 测试设计

- 以同版 PDF 的 SHA-256、原目录和逐页题号独立核验 27 大节、43 二级节、62 道题，核对引文、关键表图、公式与完整题面。源码和文本提取检查不代替源页读回。
- I/O 覆盖零字节、短读写、EINTR、EOF、末行无换行、二进制 NUL、独立 open 与 dup/fork 的偏移共享和关闭责任。
- 网络覆盖字节序、地址转换、临时回环连接、输入分片、EOF/半关闭、HTTP GET/HEAD/POST 的消息长度和错误路径；结束后关闭套接字并回收子进程。
- 并发覆盖线程参数生命周期、join、共享计数、缓冲区满/空、终止与回收；模型独立枚举合法交错和死锁条件。同步代码在适用的严格 C11、pthread、ASan/UBSan 条件下运行。至少一项机制回归在刻意错误的变体上失败。
- 保持既有静态门禁，并按来源清单检查新增完整范围、全部本地链接、共同版式、源码逐字同步、3 道/章原创自测和摘录绑定。
- 实际浏览器检查地图和三章，视口为 1800/1440/1024/390px；检查目录与高亮、上下章、原文索引、题解和代码深链接、局部滚动、图表及公式。几何扫描和目视阅读分别记录。
- 从根目录运行 `python3 tools/project.py check --book csapp`、`python3 tools/project.py check --quick`、`python3 tools/project.py build`，验证最终本地包。

## 起始证据

`tmp/csapp/part3/red-baseline.json` 记录预期 14 页而开始时只有 11 页，第 10—12 章文件均不存在。`tmp/csapp/part3/source_inventory.json` 从 PDF 目录及正文逐页独立提取题号、页码和二级节；原 PDF 不作修改。

## 内容与来源结果

- 按同一份 1122 页 Global Edition 制作第三部分开篇及第 10—12 章，补齐 27 个大节、43 个二级节、62 道原题、9 道原创自测和 21 处原文伴读。合计 14 个阅读页、117 个原书大节、261 个原书二级节、419 道原题、36 道原创自测、114 处摘录。
- 独立审阅覆盖本次 62 道题：主任务读回第 10 章 10 题；第 10 章作者独审第 11 章 13 题与第 12 章 16 题；第 11 章作者独审第 12 章 18 题；主任务另核对 12.9、12.11、12.28—30。作者源审、第二人源审、图像读回与程序执行各自保存范围，未把文本提取等同整页目视。
- 新 21 段英文逐项匹配指定源页，旧 93 条摘录与起始快照一致。保留原说法并解释本版 11.2/11.3 的 16 位题意与书后程序错位、12.2/12.5 的父进程漏关描述符、12.3 的 stdin/socket EOF 混淆、图 12.17 的汇编问题、12.9 的精确省锁条件及 12.11 的 50% 效率。
- `chapter10_review.json`、`chapter11_review.json`、`chapter12_review.json` 保留分工、原页与哈希，汇总至 `source_reading_review.json`。第 1—9 章既有题解沿用历史内容审阅；9 个旧 HTML 与起始快照完全相同，地图扩充第三部分，第 9 章仅接入下一章导航。

## 程序与独立回归

`python3 tools/project.py check --book csapp` 完整通过，证据为 `tmp/project-check/20261014T115154-se4f22c4/report.json`。最终维护程序哈希逐项与此次实际执行记录相同；后续只调整文字与审阅记录。41 组程序含 32 组 C/Python 对、7 组独立 C、2 组独立 Python，页面有 73 份逐字同步的源码副本。第 10 章两个附属 C 文件另列 `additional_sources`。

新增程序按登记使用严格 C11、`-Wall -Wextra -Werror -pedantic`、适用的 `-pthread` 与 ASan/UBSan。两类 HTTP 实现分别登记：C 提供解析与响应核心，Python 使用固定可信路径实际执行 CGI。Python 独立运行项必须登记执行类型与期望输出，此契约也进入静态检查。

独立维护回归 `books/csapp/tools/part_three_regressions.py` 已纳入根检查，实际结果为：

- 每种语言 520 个 Rio 短读写/中断/EOF 前缀案例；55 个二进制复制案例，包含内嵌 NUL、空输入、块边界、无末尾换行和预先关闭 stdin；7 个继承 fd/非法参数案例。把 EINTR 处理改错的变体被检出。
- 每种语言 22 个地址与数值边界；HTTP 检查逐个请求前缀、GET/HEAD/POST、重复长度、路径限制、慢接收端截止时间和调用方描述符标志恢复。macOS 的未公开附加状态位与公开 `fcntl` 标志分开比较。
- 20 种计数交错及 6 组独立锁所有权状态图；12.30 的 197 个可达状态中得到四个死锁 PC，与正文及 C/Python 模型一致。
- 三种 tfgets 各覆盖完整行、EOF 尾行、空输入，另各执行真实“只有部分行、发送方保持打开”的五秒截止测试；检查进程方案恢复调用前已阻塞的 SIGUSR1 掩码。

交叉审阅补充：第 11 章 220 项加 15 项定向协议回归通过；HEAD 错误响应正文、Expect 处理和 HTML NUL 问题已修复并复测。第 12 章独立验证 630 组矩阵参数、两别名/两个 16 字节地址的 hostent 深拷贝与原对象变化、四模式 HEAD 与断开后继续服务、慢上游期间另一代理请求完成。16 道早期题另有 22 项独立数值/轨迹/图和线程参数检查。动态池确实在负载中扩容、缩容；有界队列验证每项恰好消费一次。

## 实际浏览器阅读与协议实验

使用同一个 ego-browser TaskSpace，逐页检查地图、第 10—12 章在 1800、1440、1024、390px 的布局。全页展开扫描没有整页横向溢出、主要块越界、SVG 文字超界或破图。目视检查位置包括第三部分主线、文件共享关系图、完整题面/程序、HTTP 导读与首部解释、12.9 校注、12.28 进度图、并发服务器导读与展开源码。长图、表格和代码在窄屏采用局部横向滚动。修正了第 12 章侧栏英文标签与中文正文不一致。

真实点击路径覆盖第三部分地图到 Rio、10→11→12、移动目录展开/点击后收起与当前节高亮、题解深链接自动展开、12.9 到完整原图 12.25、源码深链接与横向滚动、上一章和地图返回。记录在 `tmp/csapp/part3/browser/`，几何扫描与人工读回分别列于 `reading_review.json`，没有将全页扫描称为每段文字的目视阅读。

第 11 章 Python Tiny 已在浏览器原生表单完成 GET −4+7=3、POST 12+30=42；保存的服务日志包含 `GET / HTTP/1.1`、`POST /cgi-bin/adder HTTP/1.1` 及 `Content-Length: 9`。四种 C Tiny 模式 process/select/thread/pool 分别完成 GET 20+22=42、POST −8+50=42，共 8 次表单交互。代理完成协议、过滤/日志及慢上游并发测试；浏览器未配置代理，所以没有将它列为真实浏览器代理验收。实际 HTTP/MPEG/清理记录位于 `tmp/csapp/part3/http-browser/`。

另用 ffmpeg 生成真实 MPEG-1 样本，服务收到浏览器媒体请求；当前 Chromium 的 `canPlayType('video/mpeg')` 为空、媒体错误码 4、readyState 0，因此没有完成播放。MIME/字节传输与浏览器解码结果分别写入 11.7。协议测试使用回环地址与临时文件；本次没有公网服务、生产部署或 Linux 原生执行证据。

## 文档、包与保存边界

已同步来源/习题/摘录/程序清单、全书地图和上下章、catalog/portal、TECH、规则索引、书籍说明及本批治理记录。复用既有 C11/Python/POSIX 和静态发布工具，核心技术栈、环境变量及正式服务配置没有变化。

`python3 tools/project.py check --quick` 三书静态检查通过，记录 `tmp/project-check/20261014T120114-cske_9n0/report.json`。本批构建包、最终 HTTP 字节对照与本地 Nginx 验证在下面追加。原有未提交改动保留，未执行 Git 提交、推送或生产发布。

最终包为 `deploy/portal-releases/20261014T120611/`，含 230 个文件、52 个 HTML、三书合计 36 个阅读页。`python3 tools/project.py verify-release --release-id 20261014T120611` 通过：本地 Nginx HTTPS 核验 227 个发布资源、9 个入口重定向与 PDF Range，临时 Nginx 已停止；证据 `tmp/release-check/20261014T120611-5ln9vp9n/https-verification.json`。

最终三书静态检查为 `tmp/project-check/20261014T120641-zkj89lyv/report.json`。最终预览使用新回环端口，避免同一 URL 的旧浏览器缓存影响结论；地图和三章再次完成 16 组全展开布局扫描，增补检查 12.39 的代理验收范围说明。`tmp/csapp/part3/final-package-http.json` 核对首页、公共样式、地图、9—12 章与代表源码共 10 个 HTTP 响应，均与最终包字节相同。最终预览 `http://127.0.0.1:59783/`。

`git diff --check` 通过；对新增三章与配套源码的有界检查未发现 NUL 或指定凭据特征。`tmp/csapp/part3/preservation.json` 核对已有代码未改、旧 93 条摘录未变、9 个旧 HTML 未变，最终程序哈希与完整执行记录一致。所有临时 HTTP 实验已结束；只保留供用户阅读的最终静态预览。未进行提交、推送或生产发布。

最终入口点击路径：三章页顶“笔记首页”返回书架，经“进入 CS:APP 笔记”打开地图，再从移动目录进入第三部分；当前节高亮和目录收起均正确，记录 `tmp/csapp/part3/browser/final-home-path.json`。新增 27 个章节/代码/回归与审阅文件另作 `git diff --no-index --check`，无空白错误。浏览器工作空间已关闭，已请求在 Codex 阅读面板打开最终本地第三部分入口（工具返回 queued）。

## 全书评估后的增量修订

本记录第 39 行所述 Expect 修复验证的是完整请求到齐后的拒绝响应，未覆盖客户端只发送头部、等待服务器许可后再发正文的握手。本次全书评估另发现 select 接入窗口结束时截断活动请求，以及 proc tfgets 继承 SIGTERM 设置时回收延迟。原有执行证据保留其当时范围，三项修复及新增正式回归见 [I008](../issues/I008-csapp-part-three-review-fixes.md) / [T008](T008-csapp-part-three-review-fixes.md)。
