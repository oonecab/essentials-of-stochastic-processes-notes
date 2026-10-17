# Visual Group Theory 中文伴读

从[全书地图](notes/book_overview.html)进入 Nathan C. Carter 的《Visual Group Theory》。原书为 Mathematical Association of America 2009 版权电子版，10 章；当前包含地图、序言和第 1—10 章，共 12 页、302 道原书习题及全部小问。第 9—10 章本批记录见 [review](review/chapters09-10.md)，第 5—8 章验收见 [review](review/chapters05-08.md)，第 2—4 章历史验收见 [batch02](review/chapters02-04.md)，首批记录保留于 [chapter01](review/chapter01.md)。

[阅读计划](reading-plan.md)说明原书结构、批次与模型约定；[来源清单](notes/source_manifest.json)记录身份和页序；[维护入口](agent.md)及[章节说明](notes/README.md)规定正文和程序的维护位置。程序从[运行说明](code/README.md)开始。

原 PDF 仅作本地对照，副本在忽略目录 `tmp/source.pdf`；它来自用户提供的 Zotero 附件。版权页 ISBN、SHA-256 和完整页序保存在来源清单。新 checkout 可使用同一份 PDF 放到该位置重做来源核验；构建静态笔记不依赖该副本。

从主仓库根目录执行 `python3 tools/project.py check --book visual-group-theory`。`--quick` 检查结构、来源、链接和代码同步；完整模式另实际编译、执行 C11/Python 及独立回归。统一构建和本地预览沿根 README。
