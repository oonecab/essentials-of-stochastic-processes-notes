# T016：第一章解释深度验收

关联 [I016](../issues/I016-stochastic-chapter1-explanations.md)。状态：passed（2026-10-16，本地）。

- 按原书目录核对 56 例、31 条结果、77 题，逐条保留审阅问题与具体修订位置。
- 内容验收检查所求目标、为何分类／构造、数和符号的来源、条件使用、步骤依据和结果含义；不以字数或关键词代替读回。
- 保持已有编号、英文摘录、代码、CSS/JS、例 1.4 和其余八页；用节点与文件差异验证。题干的来源澄清限 1.66、1.68、1.70、1.74、1.75，并单列依据。
- 保留错链等 15 项回归，增加习题 1.66 正时间边界的精确回归，合计 16 项。使用六状态转移矩阵及两种等待向量，检查正时间期望等于一步加剩余等待的加权均值，并确认把边界一回填到后续等待会错误增计。另以有理数逐步复算 35 组线性系统及 66 项模型、比例、矩与归一化核对。
- 四视口重新检查受影响页面，选取基础概率、平稳方程、可数耦合、退出问题、证明题和长矩阵实际阅读并记录截图；所有证明入口与习题展开检查。
- 源文和正文读回、计算及浏览器检查后，才记录内容基线。运行按书 quick、source-pages 和相称的完整检查，保留各层证据及复用边界。

实际证据：

- `tmp/stochastic-explanations/exact-and-scope.json`：164 项、262 个既有锚点、例 1.4 逐字保留、其余八页和 164 项以外的正文不变；66 项有理数核对通过。逐项记录与当前 HTML 哈希一致。
- `tmp/stochastic-explanations/tests.log`：16 项回归通过，包含 35 组显示方程与全部消元操作的精确执行，以及习题 1.66 的正时间边界。
- `tmp/stochastic-explanations/coverage.log`：第一章全部入口与过程门禁通过。全书其他章节仍保留原有缺口，未将结构 OK 改称教学审阅通过。
- `tmp/stochastic-explanations/source-pages.log`：九页内容基线、10,780 个公式绑定、353 处编号及 PDF 起始页通过。原书页图另读 PDF 第 40、41、93、94、95、101、102、103 页；页码检查本身不验证翻译或证明。
- `tmp/stochastic-explanations/browser.json`：四视口，27 张最终截图均人工查看；31 个证明链接的实际 hash 与目标核对，77 题实际展开、收起、再展开；可见公式零尺寸和 MathML 错误均为零，整页宽度未溢出。窄屏下既有宽表、长公式的局部横向滚动另有两端证据。
- `tmp/project-check/20261016T010409-qpodwr3t/report.json`：`python3 tools/project.py check --quick`，全仓库通过。
- `tmp/project-check/20261016T010451-8g25drzt/report.json`：`python3 tools/project.py check --book stochastic`，完整检查通过；包含七组程序、159 组数值基准、严格 C11、ASan/UBSan、Python 与跨语言核对。

记录保留：更新前的 source-pages 命令被内容基线阻止，原日志保存在 `source-pages-before-baseline.log`；在完成内容审阅后才记录基线并重新执行通过。浏览器第一次长批处理超时、一次临时文件相对路径写入失败均未作为通过证据；最终分段执行并保存可读记录。已有宽表的局部滚动方式保持，未更改 CSS/JS。
