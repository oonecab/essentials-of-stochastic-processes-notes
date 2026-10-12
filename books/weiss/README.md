# Weiss · 数据结构与算法读书笔记

本子项目对应 Mark Allen Weiss《Data Structures and Algorithm Analysis in C》第二版（中国改编版）。[全书地图](notes/book_overview.html)连接十二章，当前共 13 个 HTML 页面、362 道习题和 205 组 C11/Python 实现。

`notes/` 的正式 HTML 是教学正文及双语程序的维护源。各章保留独立离线阅读、MathML、内联 SVG、习题展开与桌面/手机目录。编辑前阅读 [内容和排版规范](notes/README.md)及 [专项维护约定](agent.md)。

书内既有说明中的“仓库根目录”指本子项目 `books/weiss/`；照原命令执行时先 `cd books/weiss`。下面的统一命令则从整个 Reading Notes 仓库根目录执行。

`c/` 是原始压缩包的 171 个图例的独立 C 转换，按图号提供入口，共用 `ch*.c` 与本地 TestKit。它与笔记中的教学实现各有用途；共享实现 `c/ch8.c` 被第八章链接。原资料保存为本子项目根目录的原书 PDF、`WEISS_2E.tar.Z` 与 `WEISS_2E_extracted/`，转换依据见 [C_conversion_audit.md](C_conversion_audit.md)。

在整个 Reading Notes 仓库根目录运行：

```sh
python3 tools/project.py check --book weiss
make -C books/weiss/c check
python3 books/weiss/c/debug_figure.py fig3.10
```

仅需笔记结构检查时运行 `python3 books/weiss/notes/tools/check_notes.py`。完整提取验证使用 `--verify tmp/weiss-check`，结果只写到指定临时目录；算法正文仍在正式 HTML 中。关闭断言模式和已登记实验计数的额外复核通过根入口 `check --book weiss --benchmarks` 执行。详细运行条件集中在 [总览的程序说明](notes/book_overview.html#program-guide)与 [C 图例说明](c/README.md)。

VS Code 应从主仓库根目录打开，根 `.vscode/` 已将调试路径指向 `books/weiss/c/`。本地调试链接与 `bin/` 是构建产物，不纳入版本控制。

统一发布以 [主项目部署说明](../../deploy/README.md)为准。此处 `deploy/` 保存原独立 Weiss 站点的工具和历史说明；它不是统一站点的发布入口。后续维护以本子项目为准，迁移来源目录保留用于比较与恢复。
