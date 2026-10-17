# 测度论与概率论基础 · 中文伴读

程士宏编著，北京大学出版社 2004 年第 1 版。先从[全书总览](notes/book_overview.html)看六章之间的关系，再读[序言与前言](notes/preface.html)、[第一章：可测空间和可测映射](notes/chapter01_measurable_spaces.html)、[第二章：测度空间](notes/chapter02_measure_spaces.html)、[第三章：积分](notes/chapter03_integration.html)与[第四章：符号测度](notes/chapter04_signed_measures.html)。

当前共六个独立 HTML，前四章沿原书十九个小节展开，包含 126 个编号定义/命题/定理/推论/引理、21 个编号例子及全部 115 道习题的题干与解答。第三、四章本批新增 72 项编号内容与 58 道习题。公式采用静态 MathML，图示为内嵌 SVG；保留目录可见性、章节导航、习题深链接与源码下载。第 5—6 章在地图中规划，正文待续。

三组 [C11/Python 程序](code/README.md)用于枚举有限 sigma 域、覆盖外测度、二进简单函数逼近，以及有限加权积分、Jordan/Lebesgue 分解与条件期望，具有明确输入范围和独立基准。数学证明及原书校注由正式 HTML 维护；有限枚举只验证所示模型。

原书为 256 页扫描 PDF，正文印刷页加 12 即 PDF 页序。[来源清单](notes/source_manifest.json)、[独立编号清单](notes/source_inventory.json)、[题目清单](notes/exercise_manifest.json)和[校注清单](notes/source_issues.json)记录定位。原 PDF 仅在本地忽略目录对照。

从 Reading Notes 主仓库根运行：

```sh
python3 tools/project.py check --book measure-probability --quick
python3 tools/project.py check --book measure-probability
python3 tools/project.py build
python3 tools/project.py serve --port 8000
```

维护入口为 [agent.md](agent.md)、[阅读计划](reading-plan.md)与[章节说明](notes/README.md)，当前来源、程序、浏览器和集成证据分开保存在 [review/](review/)。
