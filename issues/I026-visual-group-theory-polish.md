# I026：视觉群论阅读一致性修订

状态：completed_locally。日期：2026-10-17。依据：用户 V1—V8 评审。

统一十章地图进度，为第 2—4 章补充与正文对应的阅读注解；关键行内公式改为静态语义 MathML；准确标明多步定义和定理英文节选的范围；复核并关闭 Exercise 10.10 与七条交叉引用的陈旧状态。为长题增加可深链的步骤标题，并明确 4.1、6.4、6.5 的小问标签。

原书题号、条件、证明、图及程序算法保持原有数学约定。正式 HTML 是内容权威，摘录和清单随正文同步。关联 [P026](../plan/P026-visual-group-theory-polish.md)、[T026](../test/T026-visual-group-theory-polish.md)、[M026](../milestone/M026-visual-group-theory-polish.md)。

文档影响：更新书级说明、阅读计划、来源摘录/清单、审阅绑定、TECH 与文档索引。无技术栈、环境、接口或部署变化；现有未提交及其他书籍改动保留。

验收：V1—V8 已按范围完成。内容与来源、执行、桌面/手机视口及复制边界详见 [一致性审阅](../books/visual-group-theory/review/polish.md)，最终证据路径与文件绑定见该书 review/validation.json。

追加范围（2026-10-17，已完成本地验收）：依据用户复核补齐 31 个原有显示公式的 aria-label 与 text/plain annotation，并把既有完整公式复制处理扩展到显示公式。保持所有呈现树、题面、证明和程序不变。文档影响为书级公式/复制说明、测试设计及当前审阅绑定；不改变数学计算规则、技术栈或部署环境。

追加结果：31/31 显示公式完成回退；387 个 MathML 名称与 annotation 一致，62 个公式视图及 218 个复制用例通过。按书完整、全库快速及本地 HTTPS 检查通过，详见 review/polish.md 的复核追加及当前 validation.json。
