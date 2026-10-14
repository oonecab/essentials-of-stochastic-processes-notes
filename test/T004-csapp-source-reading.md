# T004：CS:APP 原文、数学与 Chrome DevTools 阅读验收

状态：passed_locally；关联 [I004](../issues/I004-csapp-source-reading.md)。

## 变更与测试设计

- 原文以本地 Global Edition PDF 为准，逐条保存源页、精确英文、原理类别、原公式编号及页面ID；归一化仅处理PDF换行、断词、连字和空格，不能把改写当原文。中译与完整条件由内容复核判断。
- 流水模型用串行一个输出寄存器和流水每级寄存器分别计算，典型任务数与极限吞吐均核对；旧900n必须被期望920n的基准检出。
- Python 分配边界涵盖 size_t 溢出、容器长度上限、零/负值与正常输入，不以实际巨大分配复现。
- 缓存模型保留独立参考，覆盖写回/写直达、分配/不分配、跨块和LRU；遗漏dirty的变异应失败。
- fill 驱动在 -DNDEBUG 下仍运行并检查，错误结果必须显式失败。
- 数学结构检查空MathML、上下标/分式参数、重复ID、错误原公式绑定及正文遗留数学标记。代码符号维持程序语言原貌。
- Chrome DevTools MCP 检查八页的1800/1440/1024/390px视口；展开全部题解、代码、原文后扫描整页几何，检查公式裁切/重叠、页面溢出、固定栏遮挡、表图局部滚动、目录与注解导航。截图逐张目视，包含摘录、重要公式、推导和解答，记录具体发现及修正。

## 实际证据

以下分别记录内容、程序、实际阅读与交付验证；静态通过、公式结构合法和截图文件存在均不能替代读回内容及目视验收。

### 原文与解释

八页分别有 1、5、9、28、16、6、6、7 处摘录，共 78 处；第 2 章包括原书全部 25 条 PRINCIPLE，保留原标题、条件和原公式编号。每处英文、中文解释及关联条件逐一对照同版 PDF；25 条正式原理还对照 20 张完整 PDF 源页图。内容复核覆盖地图、序言、第 1/4/5/6 章连续主文，第 2/3 章新增 44 个伴读块及其 31 个关联推导定位，以及两组长程序的 18 个函数/状态锚点。

独立复核修复了五处问题：地图章节表方位；第 2 章浮点例子的 binary64 精度说明；第 3 章 ISA 段落的省略范围；第 5 章 binary32 反例的舍入前提及过程；第 6 章跨块写入的空缓存/写回/写分配条件。最终 78 个伴读块的完整文本哈希与独立复核读回结果相符。正式记录为 `books/csapp/notes/source_reading_review.json`；明细证据位于 `tmp/csapp/refine/review/`。

### 程序与结构

- 完整执行：`tmp/project-check/20261014T001214-pap9z9_r/report.json`。20 组 C/Python 程序及维护回归通过；当前 40 份维护源与此次执行的哈希相同。
- F1：同一教学模型的串行时间为 `920n ns`，流水时间为 `420(n+2) ns`；代码、期望输出和正文同步。原书另一个以 ps 为单位的示例独立保留。
- F2：分配接口增加 Python 容器长度上限与异常处理；24 个有界案例验证统一失败契约。
- F3：四种缓存写策略共 57 条轨迹、每种语言 3964 次源操作与独立模型对照；遗漏 dirty 的变异被检出。
- fill：在 `-O2 -DNDEBUG`、ASan/UBSan 下执行 3120 个案例，调用与结果检查均不依赖 assert；错误字节变异返回失败。
- 最终 HTML 结构与来源绑定：`tmp/project-check/20261014T003454-vzswdp01/report.json`；78 处来源、25 条原理、55 大节、146 小节、298 原题定位及 40 个展示代码块同步检查通过，6 个破坏性变异被检出。
- 三本书公共检查：`tmp/project-check/20261014T001244-bioqvy_5/report.json`。原有 Durrett/Weiss 内容文件无本轮差异。
- 交付记录同步后再次运行 `python3 tools/project.py check --quick`，结构、发布支持和三本书登记检查均通过：`tmp/project-check/20261014T005137-4l1771pv/report.json`；`git diff --check` 通过。

### Chrome DevTools MCP 实际阅读

使用官方 Chrome DevTools MCP 1.10.1，通过标准 `initialize`、`tools/list`、`tools/call` 与隔离 Chrome 交互；临时本地转接器、工具清单与原始调用保存在 `tmp/csapp/refine/devtools/`，没有以其他浏览器协议冒充 MCP。

浏览器验收版本 `20261014T003500`：八页分别在 1800、1440、1024、390px 视口展开全部主文 details，32 个布局均无页面/正文溢出、数学字形纵向裁切、SVG 文字超出 viewBox 或破图；八页均使用原生 `get_css_styles` 读取实际样式。记录为 `tmp/csapp/refine/devtools/release-20261014T003500/report.json`。

实际目视包括八页桌面/手机入口、八页宽屏/手机原文伴读位置，以及 Amdahl、三分支补码加法、2.45 题干和答案、NaN 标志、流水时间、流水控制题解、浮点结合律、缓存程序导读等 18 个重点视图。另查看横向公式键盘滚动、两处程序定位与首页的 4 张交互截图，共 54 个视图：39 张直接查看，15 张入口图与前轮已查看截图逐字节相同，按哈希复用。文件与观察逐项记录于 `tmp/csapp/refine/devtools/manual-reading.json`。

目视修正：补齐块公式样式、上下标和分式；修复地图短列孤字、来源行字号和相邻分隔线；40 张短表改用自然宽度，使 2.45 的三列表在手机完整可见；实际超宽的公式/图表增加局部滚动提示与键盘焦点。方向键实测使三分支原公式横向滚动从 0 到 77px，页面宽度仍为 390px。

原生点击还覆盖 11 个导航状态：展开全书索引、跳到原理、继续到推导和题解、移动目录、调用段落、Python step/access 自动展开定位及返回首页。`interactions.json`、`targeted-reading.json`、`formula-scroll.json` 和 `calls.jsonl` 保留证据。初次访问有一次 favicon.ico 404，定位为预览站点缺少图标；未观察到阅读脚本错误或 CSP 拒绝。

### 最终交付及范围

最终本地包为 `deploy/portal-releases/20261014T004247/`，包含 178 个文件、46 个 HTML、30 个阅读页面。最终包的 46 个 HTML 与浏览器验收包逐字节相同，记录于 `tmp/csapp/refine/final-release-equivalence.json`。新增正式来源复核记录已包含在最终包中。

`python3 tools/project.py verify-release --release-id 20261014T004247` 通过本地 Nginx 验证：175 个文件、9 个入口重定向、PDF Range 与路由检查通过；报告为 `tmp/release-check/20261014T004247-2zhqkfiv/https-verification.json`。最终预览的八个 HTTP 页面全部与交付包匹配，且再用 Chrome DevTools MCP 打开了全书原文索引；见 `tmp/csapp/refine/final-preview-http.json` 和 `tmp/csapp/refine/devtools/delivery-map.json`。

本轮独立内容复核针对新增原文及关联解释。既有 298 题、34 幅图、官方 Y86/HCL 模拟器与性能测量的历史审阅范围保留在 I003 及相应记录，未扩展为本轮逐题逐图再次独立复审。32 次完整展开几何扫描也不等于每个内容位置逐字目审。没有生产部署。
