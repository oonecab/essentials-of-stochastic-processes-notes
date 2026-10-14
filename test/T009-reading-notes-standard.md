# T009：跨书方法与接入模板验证

- 关联：[I009](../issues/I009-reading-notes-standard.md)、[P009](../plan/P009-reading-notes-standard.md)、[M009](../milestone/M009-reading-notes-standard.md)。
- 标准：[RN-001](../docs/reading-notes-standard.md)，v1，2026-10-14。
- 变更类型：方法文档与治理入口；计算、单位、精度、时间边界及运行接口均未变化。

| 场景 | 验收要求 |
|---|---|
| TD-001 入口与职责 | AGENTS、README、规则索引和新书说明指向同一标准，模板只记录书级事实，现有三书专项约定仍有入口 |
| TD-002 模板复制 | 在忽略目录模拟目标层级，替换书籍 ID 后检查所有相对链接；待填项及 pending 状态清晰，未执行的审阅不带 passed |
| TD-003 治理一致性 | 生成预览、应用、校验后再次预览无 UPDATE/CREATE/CONFLICT；人工 README/.gitignore 的 PRESERVE 如实记录 |
| TD-004 仓库回归 | 从根入口运行 doctor、check --quick、check、build；失败须调查并记录，不弱化原检查 |
| TD-005 范围保持 | 对照任务开始时的文件 SHA-256 和本次实际编辑路径，确认本任务只改方法文档与配置；并发的书籍变化单列保留 |
| TD-006 标准读回 | 逐项核对来源、全书规划、机制/推导、题干/解答、代码唯一维护源、真实浏览器验收、证据分层与发布授权 |

文档没有新的执行行为，旧实现失败测试不适用；本次使用既有链接/结构及程序回归。模板复制检查验证目标路径和待填状态，不将占位文本当作教学内容。没有修改阅读页面，故本次不以浏览器重验三书作为方法文档完成条件。

## 执行记录

执行日期：2026-10-14（Asia/Shanghai）。首次 `python3 tools/project.py doctor` 因系统默认 Python 低于 3.10 退出；之后仅为本次命令将 Homebrew 加入 PATH，使用已安装 Python 3.14.6，未改机器配置或项目版本基线。

| 验证 | 实际结果与证据 |
|---|---|
| 环境 | doctor 通过，所需 Python、Clang、Make、Poppler、Node 可用 |
| 模板 | 四份模板按新书层级复制、替换 ID/书名/章节后，10 个链接解析成功；无遗留变量和伪造哈希，初始状态保持 draft/pending。见 `tmp/reading-method-standard/template-copy-review.json` |
| 治理 | 预览仅更新 TECH 受管规则，应用后校验通过；再次预览为 UNCHANGED，README/.gitignore 为预期 PRESERVE |
| 全仓快速检查 | 6 项通过，结构检查覆盖 3 本书、75 份 Python 源及 287 个文档链接；报告 `tmp/project-check/20261014T194904-hfq2sfya/report.json` |
| 全仓完整检查 | 9 项通过，覆盖原有结构/归档、随机过程、Weiss 与 CS:APP 已登记执行检查；报告 `tmp/project-check/20261014T194946-v3nb2miw/report.json`，结束时间为北京时间 19:54 |
| 本地构建 | `deploy/portal-releases/20261014T195410/` 构建成功：230 个文件、52 个 HTML、36 个阅读页，检查 4375 个本地引用；以该目录 `release.json` 为版本元数据依据 |
| 范围复核 | 本任务仅涉及 19 份方法文档/配置及记录，详情见 `tmp/reading-method-standard/scope-review.json`。检查期间绑定的 630 个书籍文件到完整检查结束均未变化，见 `full-check-binding.json`；任务开始后观察到的其他变化单列保留 |

TD-001/006 已逐项读回：共享入口指向同一 RN-001，标准覆盖来源/范围、全书规划、推导、题干与解答、唯一代码维护源及学科适配、版式、真实阅读、历史绑定和发布边界。模板填写书级事实，已有书籍的更细规范和历史记录继续生效。新书说明准确列出当前仍需显式修改的检查分派和构建接线。

书籍并发工作新增 I/P/T/M008，本任务使用 I/P/T/M009；TECH 和规则索引里的并发条目保留。初始快照与本次范围记录在 `tmp/reading-method-standard/`。`git diff --check` 通过，新增文件另查尾随空白、机器绝对路径和编号冲突，均未发现。

本次交付为方法与模板的本地固化；没有重写书籍内容，也没有为该本地构建增加浏览器或线上验收结论。上述回归结果是实际运行范围的证据，不扩展为全部数学论证、阅读质量或线上状态的重新证明。

最终文档与记录更新后，再次运行全仓快速检查，6 项通过，报告为 `tmp/project-check/20261014T195555-ledh1ipp/report.json`。最终治理日志见 `tmp/reading-method-standard/governance-validation.log` 与 `governance-preview.log`；最终范围复核见 `final-scope-review.json`，记录编号唯一，共享文档中的并发条目及测试快照中的书籍文件均保持。
