# T002：CS:APP 内容、例子与阅读接入

- 关联：[I002](../issues/I002-csapp-part-one.md)、[P002](../plan/P002-csapp-part-one.md)、[M002](../milestone/M002-csapp-part-one.md)。
- 内容与计算权威：`books/csapp/notes/*.html`、[程序约定](../books/csapp/code/README.md)。
- 生效：2026-10-13，第一批笔记。

## 场景设计

| 场景 | 覆盖与独立依据 |
|---|---|
| S01 来源与范围 | PDF SHA-256、1122 页、印刷/PDF 页序、八页与 55 个原书大节；Part I 开篇扫描页核对 |
| S02 结构与同步 | 唯一 ID、相对链接、原书页序、无外部运行依赖、六组源码与 HTML 阅读副本逐字相同；临时变异使断链/代码漂移检查失败 |
| S03 表示 | 8 位编码全部 256 个输入，精确整数权值和范围；截断/扩展、溢出边界；浮点例子以 IEEE binary64 严格求值条件说明 |
| S04 地址与 ABI | `offsetof` / `sizeof` 实际观察；LP64 示例标明前提；x86-64 汇编独立跨目标生成，只核对静态输出，执行证据来自本机 C |
| S05 流水线 | 理想模型的周期数与延迟/吞吐量代数计算；不将其标为完整 Y86-64 PIPE 模拟器 |
| S06 归约 | 空、单元素、奇偶长度、uint64 模回绕；Python 精确整数求和取模为独立基准；改变结合顺序的浮点反例 |
| S07 缓存 | 原书 0,1,13,8,0 轨迹、1/2 路组相联、LRU 驱逐、跨组/重复地址；独立按集合历史表计算；8×8 矩阵行列访问的手算基准 |
| S08 执行 | Clang 严格 C11、ASan/UBSan、Python 3；C/Python 可比输出；非法缓存参数非零退出 |
| S09 接入 | `tools/project.py check` / `build` / `verify-release`；原两书检查继续通过，归档全部本地链接可解析，CSAPP 原 PDF 未进入公共包 |
| S10 真实阅读 | 八页 1440px / 390px；目录定位、当前项、深链接展开、章节导航、回首页、代码下载、局部滚动；无 JS 与打印检查 |

基线缺少 CSAPP 正式页与按书分派，应在接入前失败。数值测试可以检查有限实例和不变量，不能替代正文的一般推导。计时数据、真实 x86-64 执行、完整 Y86-64 模拟器与全套原书题解不在本批证据内。单位以位、字节、周期和纳秒分别标明；币种、业务账期和时区计算不适用，因为这些程序没有相应输入。

## 执行证据


- 基线：新增接入前 `python3 tools/project.py check --book csapp --quick` 因未登记 csapp 返回 2；接入后按书与全仓库检查通过。
- `python3 tools/project.py check`：通过；记录 `tmp/project-check/20261013T191533-hsu2wpc5/report.json`。包含原两书完整检查及 CSAPP 严格 C11、ASan/UBSan、256 个编码、11 个归约长度、33 组缓存基准轨迹和每语言 8 组非法输入；三个内存变异检查检测断链、重复 ID 和代码漂移。
- `python3 tools/project.py build`：本地版本 `20261013T191922`，100 文件、46 HTML、30 阅读页、3180 个本地引用；原 CSAPP PDF 未收录。
- `python3 tools/project.py verify-release --release-id 20261013T191922`：本地 HTTPS 通过，97 个直接文件、9 个入口、哈希、MIME、CSP、旧 PDF Range 和禁止路径；临时 Nginx 已停止。记录 `tmp/release-check/20261013T191922-co9msdgg/https-verification.json`。
- 浏览器：原文件/阅读包八页 × 1440/390px，共 32 种布局；截图逐页目视核对。阅读包 154 次目录点击、36 个自测深链接和 12 次语言切换通过，标题未被固定导航遮挡。记录 `tmp/csapp/browser/source-layouts.json`、`release-layouts-toc.json`、`deep-code-offline-print.json`。
- 缓存宽表左右滚动、地图/公式/代码局部滚动与原生无脚本问题展开通过；源码下载实际完成，SHA-256 与维护源相同，首页返回成功。记录 `tmp/csapp/browser/download-scroll.json`。打印检查针对 beforeprint/afterprint 的展开和原状态恢复；未生成打印 PDF。
- 工具异常与修复：首次补充截图的 CSS 定位未命中，核实真实 DOM 后改用唯一表格容器；关闭脚本后自动化点击助手等待运行时回调超时，改用原生 DOM/Input 协议实际点击并截屏，正文脚本保持关闭。深链接与代码检查先写独立报告，补充验证完成后合并。
- 版本与结果绑定见 [正式验证摘要](../books/csapp/notes/validation.json)。编写正文中的一般推导与来源核对独立于有限程序测试。

- 文档与证据整理后，`python3 tools/project.py check --quick` 再次通过，记录 `tmp/project-check/20261013T201115-04cz5jzv/report.json`；治理校验和差异空白检查通过。此阶段仅更新文档/记录，正式页和程序哈希与完整运行记录保持一致。
