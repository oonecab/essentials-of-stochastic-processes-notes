# T017：第 2—6 章与附录解释验收

状态：passed，2026-10-16，本地。关联 [I017](../issues/I017-stochastic-remaining-explanations.md)。

内容验收标准：对照原书逐项检查目标、为何分解或构造、数字与系数来源、条件使用位置、每一步依据、小问与边界。结构 OK 表示过程和入口存在，解释深度由人工读回另行确认。

| 范围 | 例子 | 定理／引理 | 习题 | 合计 |
| --- | ---: | ---: | ---: | ---: |
| 第 2 章 | 14 | 16 | 61 | 91 |
| 第 3 章 | 10 | 11 | 24 | 45 |
| 第 4 章 | 31 | 18 | 39 | 88 |
| 第 5 章 | 19 | 17 | 10 | 46 |
| 第 6 章 | 9 | 10 | 25 | 44 |
| 附录 A | 23 | 12 | 0 | 35 |
| 合计 | 106 | 84 | 159 | 349 |

实际证据：

- `books/stochastic/notes/remaining_explanation_review.json`：349 个独立条目，包含原页、修订前后内容哈希、逐步推理提纲及本轮文件绑定。原书 PDF 第 104—275 页按章读取；另看第 111、176、255 页原图，核对对数符号、无限服务台及历史报价表。
- `tmp/stochastic-rest-explanations/exact-and-scope.json`：全部条目与当前正文一致；六页保留既有锚点，新增 190 个逐例／证明锚点；第一章、序言、全书地图逐字不变，CSS/JS、程序和 SVG 保持。
- `tmp/stochastic-rest-explanations/tests.log`：24 项维护回归通过。精确执行全书 48 组显示方程和消元操作，其中本批 13 组、176 次操作；另核对竞争时钟、观察方式、无限服务台、修理工、全部离开次序、1024 条倍增历史与历史报价舍入。13 道金融习题的 96 条终点历史、83 个内部节点按独立支付函数和两端现金流核对；每个美式节点检查即时支付与继续值。
- `tmp/stochastic-rest-explanations/coverage.log`：全书 115 条结果、162 例、236 题共 513 项通过；删除证明链接、错种类、错目标、空证明、模板步骤等反例继续失败。
- `tmp/stochastic-rest-explanations/source-pages.log`：九页内容基线、13,009 个公式绑定、353 处原书编号和 PDF 起始页对应通过。编号核对不代替译文或一般证明审阅。
- `tmp/stochastic-rest-explanations/browser.json`：ego-browser 实际检查六页在 1800、1440、1024、390px 下的 24 种布局，打开 84 个证明入口并展开 159 题；35 张截图全部目视查看，含窄屏宽表左右两端。公式无空内容或 MathML 错误，整页无横向溢出；长公式与宽表采用局部滚动。任务浏览器已正常结束。
- `tmp/project-check/20261016T032322-inpsq6c3/report.json`：`python3 tools/project.py check --quick`，全仓库通过，包含其他两书静态检查。
- `tmp/project-check/20261016T032737-7p65nt1k/report.json`：`python3 tools/project.py check --book stochastic`，最终完整检查通过；七组程序、159 组独立数值基准、46 组非法输入、严格 C11、ASan/UBSan、Python 与跨语言核对全部通过，另包含仿真种子与工具回归。
- `tmp/stochastic-rest-explanations/content-regressions.log` 与 `tooling-regressions.log`：四组既有内容回归更新当前显示绑定，工具回归共八项通过；新增变异将正确流量和、平价分数、亚洲期权根值改错，三种情况均被拒绝。

失败记录与处理：`tmp/project-check/20261016T032322-w9qxzm8a/report.json` 保存首次完整检查失败。旧检查要求 alpha_1 字面形式和 414.72/49；现稿使用 r_1 和等值的 10368/1225。更新检查以绑定当前交通方程、代入值、两套初价的平价结果及两种合同支付，并用错值变异防止降低检错能力。正文未为适配测试而改写，浏览器验收对应的页面哈希仍有效。

边界：一般证明、翻译和推理由作者逐项对照与读回，有限回归不等于机器证明全部定理。第一章例 1.24 的原书整图模拟复现限制沿用 I016。本轮只进行本地内容修订和验收。
