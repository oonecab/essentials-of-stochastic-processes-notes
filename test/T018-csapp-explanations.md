# T018：CS:APP 解释补充验收

状态：passed（本地内容修订、执行与阅读验收）。2026-10-16。关联 [I018](../issues/I018-csapp-explanations.md)。

## 内容与来源

读回全书地图、序言、第 1—12 章，涵盖 117 个原书大节中的正文、261 个二级节、419 道本版原书题解、36 道自测及实验和程序旁说明。按“对象和输入是什么、这一步为何需要、数值和状态怎样变化、结论用到什么条件”检查；根据具体缺口补充 109 个解释块，并重写第 5 章 §5.1 的别名例子。

[逐项审阅记录](../books/csapp/notes/explanation_review.json)登记 14 页和 630 个既有锚点（175 个 section 区域、419 道原题、36 道自测），保存各章发现、补充位置及当前 HTML 哈希。section 区域包括导读、原文索引、实验和习题集合，存在父子覆盖，630 不是新增内容数量。新增文字全部再次读回；保留已有充分推导与必要的原书校注。

原书重点抽查实际渲染并目视阅读 PDF 第 253、505、536、692、693、1033 页：分支罚时、CPI 条件、twiddle1/twiddle2、矩阵遍历与共享计数。另读第 504 页提取文本确认 CPI 的频率和气泡数。本轮没有把这些抽查表述为重新逐页校勘整本 PDF。const 与复合赋值另核对 [C11 草案 N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf) §6.7.3p6、§6.5.16.2p3。

来源和修订前快照在 `tmp/csapp-explanations-20261016/`：`baseline/`、`source-pages/`、`readback/`、`additions.json`、`review_notes.json`。

## 执行和兼容

- `python3 tools/project.py check --quick` 通过，证据：`tmp/project-check/20261016T214912-719sf103/report.json`。
- 运行登记的完整命令 `python3 tools/project.py check`，覆盖本书及其他两书，全部通过，证据：`tmp/project-check/20261016T215106-j30s1o70/report.json`。其中 `csapp/report.json` 记录 42 组维护程序、32 对 C/Python、8 个独立 C 和 2 个独立 Python 程序，74 个代码阅读副本一致；C11、ASan/UBSan、跨语言与既有独立回归通过。
- 新增维护回归 `books/csapp/tools/explanation_regressions.py` 直接提取 HTML 中的 twice/once 与函数副作用例子。`-DNDEBUG` 下分别执行 O0、O3、O2+ASan/UBSan；每次含 33 个同址输入和 1089 个异址输入。初值 2 对应 8/6，异址等价；返回值相同而调用计数为 4/1。错误地合并两句相加的变异被拒绝，经 const 指针赋值的编译被拒绝。证据：完整检查目录中的 `csapp/explanations/report.json`。
- `python3 tmp/csapp-explanations-20261016/check_worked_examples.py` 独立核对 40 组算术、位模式、地址、缓存组周期、成本曲线和指令交错；枚举模型确认 20 条交错中 2 条得 2、18 条得 1。结果见 `worked-example-results.json`；有限数值验证与正文的一般性解释分开。
- `python3 tmp/csapp-explanations-20261016/compare_baseline.py` 确认 14 页中全部已有锚点次序、455 份完整题干、114 条英文摘录、172 个原有 h2 与 28 个 CSS/JS 块逐字保持。源 PDF、维护程序文件、既有来源清单保持。结果见 `baseline-comparison.json`。

## 实际阅读与集成

使用 ego-browser TaskSpace 10，预览从构建包解出的站点。14 页分别在 1440×1000、390×900 视口打开、定位新增段落并截图，28 张重点位置截图逐张目视阅读；每页文档宽度未超出视口。十二章分别对补充过的 1.2、2.95、3.19、4.43、5.6、6.37、7.4、8.3、9.6、10.7、11.12、12.26 实际收起并展开，检查深链接自动展开，12 张题解截图也逐张阅读。

第 5 章新增状态表和代码通过键盘横向滚动查看右侧，滚动保持在容器内。窄屏目录点击定位 §5.2，并核对当前节标记；章间导航实际到第 6 章。来源链接在浏览器 PDF 阅读器打开第 536/1122 页，目视确认 twiddle1/twiddle2 所在印刷 535 页。关闭 JavaScript 后，以原生点击展开 5.2，新增解释可读。无脚本时高层选择器自动化依赖的 Runtime 调用超时，改用原生鼠标输入及 DOM 协议完成验证，并恢复脚本设置；这不是阅读页故障。

证据为 `tmp/csapp-explanations-20261016/browser/` 下的 `1440-audit.json`、`390-audit.json`、`exercise-interactions.json`、`navigation.json` 和对应截图。全部文本的读回与这些重点位置的目视验收范围分别记录，未声称检查每一屏像素。阅读 QA 初始包为 `20261016T215018`；后续包补入审阅元数据，14 页 HTML 的源哈希与已验收包一致。

## 边界与文档影响

本次为本地解释修订，保留各题模型、机器参数与历史测量的适用范围。宿主检查是 macOS 上的执行；官方 Y86 和其他目标实验沿用其原有证据范围。12.39 的真实浏览器经代理实验仍待验收，读者页面 QA 不替代该实验。本轮没有提交、推送或生产部署。

同步了书级维护约定、notes/README、规则职责索引、TECH、validation.json 的独立增量记录及 I018/P018/M018。技术栈、环境变量、长期服务与部署流程沿用现状，无需修改技术栈和环境清单。正式内容仍在原 HTML 文件维护。

最终本地构建包：`deploy/portal-releases/20261016T220343/`，238 个文件、52 个 HTML、36 个阅读页、5783 条本地引用检查通过。`package-audit.json` 逐字节确认十四个 CS:APP 发布 HTML 与已读回的 QA 包相同，两个最新审阅元数据文件与维护源匹配。补齐文档后 `tools/check_structure.py` 再次通过（418 个文档链接），`git diff --check` 通过；本轮 26 个改动/新增维护文件的高置信凭据模式扫描未发现匹配。

## 全书图追修验收（2026-10-16）

修复前在构建包实际页面确认图内只有四个章节链接，缺第 1、6—12 章；按原书章节清单核对的结果为失败，见 `tmp/csapp-map-fix-20261016/before-navigation.json`。本次验收范围是三部分分组、十二章入口及各部分阅读顺序，需逐个实际打开目标章、验证键盘访问和 390px 局部滚动。原程序和计算内容未变，本次静态与浏览器结果独立于前轮程序执行记录。

追修结果：图内十二章均有独立链接，第一部分为第 2—6 章、第二部分为第 7—9 章、第三部分为第 10—12 章；第 1 章作为总览单列。图中横向箭头表示各部分的阅读顺序，图后的文字解释跨章知识联系。修复范围严格限于原图和紧邻的一句说明，29 个已有锚点及其顺序保持，其余十三页与首轮记录的哈希相同，见 `tmp/csapp-map-fix-20261016/source-audit.json`。

`python3 tools/project.py check --book csapp --quick` 通过，报告为 `tmp/project-check/20261016T221931-770okvll/report.json`。浏览器使用 ego-browser TaskSpace 11，实际阅读包 `20261016T221607`；1800、1440、1024、390px 四种宽度截图均已目视检查。首次桌面检查发现图的最小宽度过大，调整后前三种宽度完整显示；390px 图内可滚动 379px，整页横向滚动量为 0。十二个节点全部实际点击并核对章标题，Tab 依次到达十二章，Enter 从第 12 章节点打开相应正文；窄屏通过方向键滚动后打开第 6 章。关闭 JavaScript 后也用原生鼠标点击打开第 6 章，之后恢复脚本。辅助访问树列出十二个有章节名称的链接。

本次证据在 `tmp/csapp-map-fix-20261016/browser/`：`viewports.json`、`interactions.json`、`no-js.json` 和五张最终截图。首轮历史记录保持；新绑定见 `explanation_review.json` 的 `followup_revisions` 和 `validation.json` 的 `whole_book_map_revision`。更新书级 README 及本问题、计划、里程碑记录；图内导航修复不改变程序、计算规则、技术栈或长期环境，相关权威文档无需调整。

追修最终构建包为 `deploy/portal-releases/20261016T222117/`：238 个文件、52 个 HTML、5791 条本地引用检查通过。`tmp/csapp-map-fix-20261016/package-audit.json` 核对最终 HTML 与浏览器验收包逐字节相同，两个增量元数据文件与维护源相同；文档结构检查和 `git diff --check` 通过。预览已切到此包，本次完成范围为本地修复。
