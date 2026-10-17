# T032：最终评估修复验收

关联 [I032](../issues/I032-final-assessment-repairs.md)。

- 发布：unpack、rsync、rename、journal、switch 至少五个实际 SIGKILL 点；重启恢复后 current 只指向完整版本。持久化顺序由独立故障模型验证，不能将模型称为真实断电实验。
- journal：截断 JSON 的只读诊断、显式选择已验证版本恢复、原子替换、正常恢复/回滚/队列幂等。
- 构建：全部公开 HTML 离线，保留正式页指纹；DOM 标签/属性/顺序变异与悬空锚点必须失败；新增页/书空跑与动态页数。
- 浏览器：1800/1440/1024/390、no-JS 1440/390，全公开 HTML；CSP 实际响应与脚本失败注入。
- 权限：root 安装边界、发布身份无 release 写权限；cleanup 保留 current/恢复引用，空间/inode 门限，元数据与证据关系。
- 教材：原书扫描定位、定理逐步证明、陈述来源标识、例子分级、具体题目核对记录；C/Python 非法输入及多字段变异。
- 统一：工作单列出的构建、parity、offline、项目及测度书完整检查、发布验证；每类证据保留其真实范围。

执行结果随各批追加。未实机运行的服务器安全步骤保留为运维待执行。

## 发布耐久性批次

新增回归先因缺失 durability 模块失败，完成实现后 5 个文件/目录屏障与原子写单测通过。`tools/test_static_publish.py --release-dir deploy/portal-releases/20261017T174039` 的 21 项演练通过（`tmp/publish-check/20261017T174039-4k2i7xfp/report.json`）：六个实际 SIGKILL 点、截断 journal 只读诊断与显式恢复、后续发布、既有并发/回滚/幂等回执、真实临时 Nginx HTTPS 与 298 个直接响应文件、15 个旧入口和 PDF Range。目录 rename 前将顶层目录设为 0555 在 macOS 失败；已改为先持久化内容、rename 后锁定并同步目录，再持久化父目录。落盘失败使用 fsync 错误及顺序模型，未声称物理服务器断电实测。

## 全站构建与发布模板批次

- `pnpm install --frozen-lockfile`、`pnpm test`（9 项）、`pnpm build`、`pnpm check:parity` 通过。DOM 变异测试在加入 DOM 指纹前失败；修复后标签、hidden、role/aria/class、转义 set:html、数学标签与失效锚点均能检出。新增 dummy 书/页可从 catalog 枚举并生成缺失镜像。
- `pnpm check:offline`：74 个 HTML、296 个 JS 视图、148 个 no-JS 视图全部通过，0 外部请求；正式 54 页仍为 0 parity 差异。实际查看了 14 个辅助页桌面/手机的四张联系图，首屏、代码局部滚动及排版正常；未重新声称全书数学内容审阅。
- 真实 CSP 浏览器冒烟覆盖 9 页中的全部 12 种内联脚本；正常无 CSP/runtime 错误，故意修改脚本后浏览器阻止执行；打包同时核对验收后 HTML 与 hash。记录位于 `tmp/reading-notes-migration/csp/`。
- root 安装器的固定参数/路径边界、队列 symlink 拒绝、字节/inode 门限、保护 current/前版/事务和过期临时目录等 5 项回归通过。root 属主及真实 Ubuntu systemd/sudo 边界仍需运维应用后实测，不能由 macOS 单测代替。
- 登记快速检查 13 项通过：`tmp/project-check/20261017T202028-ut52iqg9/report.json`。新本地测试 release `20261017T202235` 为 303 文件、74 HTML、54 正式页、28,854,317 字节；元数据已改为部署状态另记。临时 Nginx 验证通过，21 项发布演练通过：`tmp/release-check/20261017T202235-9q90zh1x/https-verification.json`、`tmp/publish-check/20261017T202235-o3peaf08/report.json`。此测试包记录了当时未提交的修复源状态，不作为已部署版本。
- I028 根记录及五书迁移记录标明 local snapshot，并分别链接 I029 生产报告，旧摘要的哈希变更原因和原值保留。服务器 P0-3 与权限模板的应用/回滚/验收交给 `deploy/OPERATIONS-I032.md`，本轮未执行。

### P0-4 定理 1.5.5

人工核对印刷 19 / PDF 31 后补全 1216 字证明，保留反例及修正条件边界。工作单要求先证 D 对补封闭并不由所给条件直接推出；本次从上升并/下降交取得单调系，再用推论 1.3.4 得到 σ(A) 的指示函数、非负简单函数、二进上升逼近。有限值误差与无穷值情形均展开。来源核查、独立推导由本次 Codex 完成，不宣称另一个审阅人已签字。

`pnpm build`、54 页全 DOM parity、测度结构检查与历史/当前绑定检查通过。1800/390 目视读回证明两段截图，公式可读，无整页溢出。证据位于 `tmp/final-assessment/build-proof.log`、`proof-browser.json`、`proof-{1800,390}-{start,limit}.png`。最终全站浏览器和发布包将在各分项完成后重新绑定。

### P1-7 原文状态

126 条 statement 一一登记：8 条核心定义/定理逐页目视转录，118 条明确只做页码定位；原有两段序言引文独立保留。引文数学排版的规范化及摘录范围逐条说明。检查器新增锚点、原页、状态、可见文本对应断言，状态改变和 PDF 页码漂移两种变异均被拒绝。`pnpm build`（含 CSP 浏览器冒烟）与 54 页全 DOM parity 通过，结构结果 `tmp/final-assessment/excerpts-structure.json`，构建日志 `build-excerpts.log`。摘录视觉检查随最终四章读回完成。

### P1-8 例子分级

逐一读回 21 例，标明 7 个完整例题、14 个定义性短说明，新增可跳转索引。2.3.1 明列八个外测度值和六个失败切割；2.3.2 区分初始覆盖条件与扩张后的 σ 有限性；4.3.1 验证概率测度、绝对连续与密度矛盾；4.5.1 对全部四个信息事件代回积分定义。结构检查逐例绑定类型，`pnpm build`/54 页全 DOM parity/CSP smoke 通过。证据 `tmp/final-assessment/build-examples.log`、`examples-structure.json`；例子正文视觉检查并入最终读回。

### P1-9 具体审阅记录

147 项陈述/例子和原通用记录对应的 35 道习题已逐项读回当前正文。每项记录实际条件、证明步骤与边界；另外 80 道习题中，3.14 的简短记录补明两小问，其余 79 题保留既有具体记录；全部补齐统一锚点。147/147 item review、115/115 exercise review 文本各不相同，检查器绑定原清单锚点并拒绝重复占位。该检查只防退回模板，不代替内容阅读。新记录明确本轮 HTML 逻辑读回与旧扫描页审阅的差别，8 条摘录和 1.5.5 的原图核对单独登记。结构及 Astro 当前/历史绑定检查通过，正文没有因该项再改变。
