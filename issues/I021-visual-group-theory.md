# I021：《Visual Group Theory》首批伴读

状态：completed_locally。日期：2026-10-17。任务依据：用户提供 Nathan C. Carter 的原书 PDF，并要求“现在需要做一下这本书的读书笔记，现在开始吧”。按 RN-001 与新书接入流程，先完成全书地图、序言与第 1 章完整样章。

基线：主分支工作树干净；新增书籍 ID 为 `visual-group-theory`。原书为 MAA 2009 版权的电子版，312 页，书内制版标记为 2011，PDF 元数据创建于 2012；这些日期不当作新版本声明。身份、页序、目录与编号清单由原 PDF 独立提取并逐页核对本批范围。

范围：三份正式 HTML、第 1 章 1.1—1.14 全部题目及小问、四条 Observation、四条 Rule、Definition 1.9、原创交换图与 C11/Python 有限状态枚举。建立全书目录与未交付项清单，接入本地书架、检查、构建及入口路由。后续第 2—10 章另按阅读计划推进。

风险与处理：原 PDF 文本层会漏掉负号，公式与题目看原页；动作、状态、生成元、复合方向和非正式可逆性分别说明。有限穷举是具体例子的验证，一般证明保留在正文。完整原书只作本地对照，暂存于被忽略目录，发布清单不含 PDF。

文档影响：同步书级 README、reading-plan、agent、来源/习题/摘录清单、review、公共 catalog、README、TECH、规则与文档索引及治理源码边界。沿用静态 HTML/MathML/SVG、C11/Python 与既有预览服务；没有技术栈或环境变量变化。教材计算规则权威为正式 HTML，测试覆盖其具体实例。

授权边界：本任务授权本地笔记制作、接入和验证。提交推送与生产发布另按实际指令。恢复方式为按本单新增文件及公共增量回退，保留原三书及其历史记录。

关联：[P021](../plan/P021-visual-group-theory.md)、[T021](../test/T021-visual-group-theory.md)、[M021](../milestone/M021-visual-group-theory.md)。

完成：首批三页、全部 14 题、图解/交互与配套 C/Python 均已本地交付；原书清单、正式正文、检查器、书架和治理文件同步。内容、执行、阅读和集成证据见 [T021](../test/T021-visual-group-theory.md)及[章节审阅](../books/visual-group-theory/review/chapter01.md)。剩余工作为计划中的第 2—10 章，不计入本批完成声明。
