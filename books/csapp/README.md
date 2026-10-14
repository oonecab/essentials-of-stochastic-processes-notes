# CS:APP 读书笔记

原书为 Bryant / O’Hallaron 第三版 Global Edition，Pearson 2016。进入 [全书地图](notes/book_overview.html)，再从 [序言](notes/preface.html) 和第 1 章进入 Part I 第 2—6 章，再读 Part II 第 7—9 章和 Part III 第 10—12 章，共十四页 HTML，117 个原书大节、419 道原书习题、36 道补充自测与 C/Python 实验。

页面沿用 Reading Notes 的纸色、绿色强调、宽屏目录和窄屏折叠导航，公式与图示内嵌，可直接离线打开。各章讲清原书机制、必要推导、例子和边界，三个部分的学习关系和阅读入口集中在地图中。

本地来源是 `csapp.pdf`；版次、页码与 SHA-256 见 [来源清单](notes/source_manifest.json)。Global Edition 的题号、输入和部分答案与北美版不同。全部题号按本地原书独立枚举，见 [习题来源清单](notes/exercise_manifest.json)；题干、子问与数据先于解答。发现矛盾时同时保留本版条件、修正推导与依据，各章 `chapterNN_review.json` 记录来源复核和执行范围。

维护前阅读 [agent.md](agent.md)、[笔记规范](notes/README.md) 与 [程序说明](code/README.md)。程序源在 `code/`，HTML 中是逐字同步的阅读副本。

从 Reading Notes 根目录运行：

```sh
python3 tools/project.py check --book csapp --quick
python3 tools/project.py check --book csapp
python3 tools/project.py build
```

快速检查包含来源、页序、结构、内链、原文绑定与代码同步；完整检查另运行严格 C11、ASan/UBSan、Python、独立基准及跨语言对照。第二部分涵盖链接、异常控制流与虚拟内存，新增 59 道本版题解；其来源复核、执行与阅读记录见 [T005](../../test/T005-csapp-part-two.md)。第一批浏览器与本地阅读包验证记录见根 [T003](../../test/T003-csapp-companion.md) 和 [T004](../../test/T004-csapp-source-reading.md)。阅读包按来源清单收录原 PDF，章首、正文来源及习题页码均可点击跳到对应原页，浏览器后退返回笔记。该功能的本地构建与实际跳转验收见 [T011](../../test/T011-csapp-pdf-navigation.md)；本地准备与线上部署分别记录。

第一批八页的 78 处原文摘录，其中第 2 章覆盖 25 条原书 `PRINCIPLE`。从[经典原文与重要原理](notes/book_overview.html#source-reading)进入，或沿章节读英文、中文陈述及相邻推导。来源页、原标题和原式见[原文清单](notes/source_excerpts.json)。

本批已执行的来源、程序、浏览器和本地包检查绑定在 [验证摘要](notes/validation.json)，其中明确区分宿主执行、静态汇编生成、模型计算与本地阅读验收。

第三部分涵盖系统级 I/O、网络编程和并发编程，新增 62 道本版题解。沿[第三部分导读](notes/book_overview.html#part-iii)进入；本批源审、程序、阅读与本地包验证记录见 [T007](../../test/T007-csapp-part-three.md)。
