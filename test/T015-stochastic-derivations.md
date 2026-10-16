# T015：证明入口与逐项过程门禁

关联 [I015](../issues/I015-stochastic-derivations.md)、[P015](../plan/P015-stochastic-derivations.md)、[M015](../milestone/M015-stochastic-derivations.md)。权威正文：第 1 章 HTML；规范：RN-001 与本书 agent.md。范围为 2026-10-15 授权的样章，数学结论保持。

- 全量枚举 9 页/115 结果/162 例/236 题，对照 source_manifest 和原例号来源清单，禁止用新增 HTML 计数反推原书范围。
- 定理入口必须为 proof-link，目标为 source-review，包含相同种类与编号的显式 proof-item、可见题号、至少三步、条件使用、边界和 PDF 来源。原例题入口并存。
- 每个 source-review 至少有一个实际入链；每例有单独编号、模型和有序过程；每题保留 solution-steps，检测空泛模板和结果/核对缺失。结构判据不能自动证明数学正确。
- 反例：将 1.19 的完整证明链接改到周期/库存例题块；改到含相同编号引用但无该条证明的块；删证明步骤；制造孤块；删除例题步骤；保留编号但删除结果。均须失败。1.1 不得匹配 1.10，减法 1.1−225 不得成为编号范围。
- 数学验证：返回周期有限性、零常返截断、乘积链同步可达及相遇后边缘分布、退出矩阵唯一性；矩阵/分数计算用独立 exact Fraction 代回。单位、边界和舍入沿各题原文；时区/币种换算无新增规则。
- 浏览器：第 1 章 1800/1440/1024/390px，定理→证明→原 PDF、长公式与有序过程、习题深链接自动展开、无 JS 阅读。记录当前 SHA、截图和实际看过的范围。

修改前新门禁已经失败：`tmp/stochastic-derivations/check-before.json`。后续记录运行命令、退出码和未闭合项；先完成审阅再 --record，历史时间与哈希保持原值。

## 2026-10-15 执行结果

| 命令 | 结果 | 证据（仓库根相对路径） |
|---|---|---|
| `python3 tools/project.py doctor` | 通过 | I015 修改前环境记录 |
| `python3 tools/project.py check --quick` | 退出 0；三书检查通过 | `tmp/project-check/20261015T232110-5jwikcyi/report.json` |
| `python3 tools/project.py check --book stochastic` | 退出 0；完整程序与内容门禁通过 | `tmp/project-check/20261015T232204-68zp238c/report.json` |
| `python3 books/stochastic/tools/content_integrity.py --source-pages` | 退出 0；9 页、9234 个公式绑定、353 个编号起始页 | `tmp/stochastic-derivations/source-pages.log` |
| `python3 test/test_stochastic_derivations.py` | 15 项通过；含错链等变异与 35 组实际行变换 | `tmp/project-check/20261015T232204-68zp238c/check-05.log` |
| `python3 books/stochastic/tools/derivation_coverage.py --check --page chapter01_markov_chains.html` | 退出 0；31 结果＋56 例＋77 题 | `tmp/stochastic-derivations/coverage-sample.json` |
| `python3 books/stochastic/tools/derivation_coverage.py --check` | 预期退出 1；506 条后续范围诊断 | `tmp/stochastic-derivations/coverage-full-check.json` |

浏览器证据为本地离线文件的 ego-browser 实测。1800/1440/1024/390px 的可用根宽分别为 1785/1425/1009/375px，滚动宽均等于可用宽；全部展开后的 77 题和 3613 个可见 MathML 未造成整页溢出。31 个证明链接实际点击；四视口、随机抽样、长公式／矩阵与无脚本原生展开截图逐张读回。PDF 链接实际导航至第 61 页。明细与图片 SHA 见 `tmp/stochastic-derivations/browser/layouts.json`、`interactions.json` 和正式 [derivation_review.json](../books/stochastic/notes/derivation_review.json)。无 JavaScript 时需要读者手动展开原生 details，这与脚本开启时深链接自动展开分别记录。

原书 PDF 第 33、37、48、57、58、61、62 页已渲染并目视核对关键笔误、周期测度和收敛证明。静态清单、数学读回、程序执行、浏览器阅读与原书模拟未复现的范围分别记录。内容基线在上述审阅后记录；其余八个页面、原 CSS/JS、英文摘录和程序内容不变。

## 例 1.4 读者反馈后的局部验收

原书印刷页 4／PDF 第 13 页的状态定义和矩阵已重新核对。两代路径及 1000 条家族谱系的期望数作为伴读解释标明；以 Fraction 核对三个贡献为 7/100、1/25、1/25，和为 3/20，期望数为 70、40、40。HTML 差异断言确认仅 `#example-1-4` 改变，其他正文、程序与所有既有锚点不变。证据：`tmp/stochastic-derivations/example-1-4-review/exact-and-scope.json`。

ego-browser 在 1800、1440、1024、390px 实测三条路径的解释，额外读回桌面公式、手机模型／求和／结果，共八张截图；根滚动宽分别等于 1785、1425、1009、375px，无整页横向溢出。长式沿原 equation 容器滚动。例 1.18 的续读链接已实际点击并到达对应例题。截图、当前页面 SHA 和交互时间见 `tmp/stochastic-derivations/example-1-4-review/browser.json`。本次未重做无脚本检查，CSS/JS 保持原样；以前的无脚本记录保留原哈希和时间。

- `python3 tools/project.py check --book stochastic --quick`：退出 0，含现有 15 项回归及结构、链接、代码同步和审阅绑定。记录：`tmp/project-check/20261015T234334-pslyc9i1/report.json`。
- `python3 books/stochastic/tools/content_integrity.py --source-pages`：退出 0，9 页、9264 个公式绑定、353 个编号起始页。记录：`tmp/stochastic-derivations/example-1-4-review/source-pages.log`。
- 第 1 章过程门禁与 `git diff --check` 通过；内容审阅和八张截图读回后才记录基线。程序及数值基准未改变，复用前节所列完整程序运行证据，本次未重跑 C/Python 编译执行。

上述结果证明本次局部修改的来源、算术、结构和渲染检查已完成；用户对讲解深度的确认仍待完成。
