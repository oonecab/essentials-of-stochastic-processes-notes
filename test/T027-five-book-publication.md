# T027：五书交付验证

关联 [I027](../issues/I027-five-book-publication.md)、[P027](../plan/P027-five-book-publication.md)、[M027](../milestone/M027-five-book-publication.md)。当前范围及公式权威由各书正式 HTML、agent.md 和 code/README.md 定义；本轮不另改计算规则。

## 夹具与场景

初始 `79e8f20` 与 149 个改动文件的指纹固定于 `tmp/release-review/20261017T151250/baseline.json`。测试输出、导出快照、构建包和浏览器图像全部置于忽略目录。

1. 全库 `doctor`、`check`：检查五书结构、编号/来源与题目清单、审阅哈希、维护源码/HTML 同步、严格 C11、ASan/UBSan、C/Python 实际执行、独立模型和非法输入。公式、精度、数值/状态边界以各书已登记基准为准；单位/币种和账期在新书有限模型中不适用，原三书既有回归仍执行。
2. `build` 与 `verify-release`：逐文件归档身份、脚本 CSP、静态资源、内链/锚点、五书十五个入口重定向（含查询参数）、源码 MIME/下载、已收录 PDF Range；两本新书原 PDF 不在公开包内。非法方法、点路径与不存在路径沿现有验证器检查。
3. 实际阅读：书架五卡片和新增十八页在桌面/390px 检查，抽看公式/图/详细题解及阅读注解；检查目录、展开题目、源码说明和下载、章节上下导航与返回书架。视口模拟与实体手机验收分开描述。
4. 提交快照与归档扫描：Gitleaks 使用完整脱敏输出，补充检查非忽略机器路径、私钥、缓存、二进制生成物和源 PDF 边界；检查 diff whitespace。暂存内容与已检查文件指纹对照。
5. 普通提交、推送后读回 HEAD、origin/main、远端 main，检查剩余工作区；线上验收仅在用户明确发布后执行。

## 文档一致性与退出条件

根 README、catalog、书架、构建路由及 deploy/README 的范围一致；书级计算契约及详细推导保持当前正式内容。修复的三/四书描述与断表可从旧差异复核，无算法旧实现失败场景。所有必须执行项如实记录，未执行项说明原因；不以结构或程序执行替代数学来源审核。

## 实际结果

本轮全部证据在忽略目录 `tmp/release-review/20261017T151250/`。`review-notes.json` 记录实际审查范围和内容质量边界，`baseline.json` 记录初始 149 文件与源提交；现有两书逐项来源读回记录与维护源的哈希一致。本文档中的命令与报告采用仓库相对路径。

- 环境：`python3 tools/project.py doctor` 退出 0，Python 3.14.6，全部必需工具及本地 Nginx/OpenSSL 可用。
- 完整检查：`python3 tools/project.py check`，13 个登记命令全部退出 0，报告 `tmp/project-check/20261017T151211-3dmdvyiu/report.json`。视觉群论 12 页/302 题/62 陈述/387 MathML/20 同步源码；测度概率 6 页/115 题/126 陈述与 21 例/2707 MathML/6 同步源码；独立计算、错误实现变异、严格编译和 ASan/UBSan 实际执行通过。
- 构建：`python3 tools/project.py build`，版本 `20261017T151424`，303 文件、74 HTML、54 阅读页、7454 资源引用；归档哈希见 I027。`package-review.json` 确认新书 64 个公开文件不含原 PDF 或临时路径。
- HTTPS：`python3 tools/project.py verify-release --release-id 20261017T151424` 退出 0；`tmp/release-check/20261017T151424-dx1_l2i_/https-verification.json` 记录 298 个实际文件、15 个重定向、查询参数、方法/点路径控制和已收录 PDF 的 206 字节身份。临时 Nginx 已停止。
- 阅读：Ego Lite TaskSpace 22。`browser/matrix.json` 为十八页及书架在 1440/390px 的 38 视图，整页横向溢出为零；38 张页首图与 8 个习题/无 JS 细节另经实际看图。`browser/deep-links.json` 的 834 次访问覆盖新增全部 417 题的两种视口，展开祖先、目录高亮和题目可见均通过。`browser/interactions.json` 记录公式复制 34 例、两份原生浏览器源码下载及哈希、26 个已登记源码下载链接、无 JS 原生折叠与书架路径。复制使用构造的 copy 事件，不访问系统剪贴板。
- 工具调整：第一次深链检查早于异步目录更新，随后按可观察高亮等待；文档末尾短题按视口可见性判定。长资料页的自动滚动超时后读取实际状态再用 DOM 定位；关闭 JS 后定位器助手不能调度，改用 CDP 原生鼠标验证。初始观察保留，未为适配工具改动产品或弱化正式检查。
- 安全：930 文件源码导出与解包后的公开文件分别扫描，`gitleaks-source.json`、`gitleaks-public.json` 均无发现、退出 0。用户主目录前缀、本地文件协议仅出现在检查器用于拒绝这些路径的字符串规则中，不是本机实际地址。Git 忽略目录无文件被跟踪。

以上为本地集成及阅读验收。既有详细证明、原书校注和模型契约未在本轮改写；没有把自动化通过当成一次新的全书数学独立审计。第五、六章及实体手机/真实读屏不属于已验收范围。Git 交付结果与最终工作区读回待下一条追加。

最后快速检查首次在 `tmp/project-check/20261017T152355-wzq45ed8/report.json` 失败：本测试记录引用了检查器禁止的字面路径前缀。已改为可移植的文字描述，保持检查器规则不变；随后重新检查。

用户已回复确认“是，推送后发布到网站”，生产发布授权成立。将继续核对实际服务器、旧版本及配置恢复点，推送后按部署说明执行并追加线上结果。

修订后的全库快速检查通过，报告 `tmp/project-check/20261017T152426-i4ikna3m/report.json`。154 个文件的暂存差异通过空白检查；930 个索引导出文件经 Gitleaks 扫描退出 0，`gitleaks-staged.json` 无发现。现有服务器对引用对话中的历史密码拒绝认证，已请求当前登录方式；在取得有效认证前不触碰生产配置，Git 交付继续执行。

## Git 与线上验收

用户补充当前登录信息后认证成功，认证值未落入工程文件。内容提交 `fd88594ed4f16265040a9965150c831767a2e731` 已推送到 origin/main；提交后的 HEAD、跟踪分支和远端 main 一致，工作区为空。`deploy/reports/20261017T151424/source-identity.json` 核对 930 个索引文件和归档对应的 283 个维护源。后续验收记录提交仅影响说明文档，公开包的维护源保持同一身份。

生产版本 `20261017T151424` 已生效，归档哈希与本地构建相同。以下证据均位于 `deploy/reports/20261017T151424/`，原始包位于相应 `deploy/portal-releases/` 目录，均为忽略输出。

- `server-before.json`、`server-preparation.json`、`rollback-readiness.json`：上传前核对原 current 与配置；归档与全部 303 文件在服务器验证；旧版 `20261016T232016` 的 239 个文件哈希及配置/CSP 恢复材料已核验。
- `activation.json`、`origin-https.json`、`public-https.json`：原子切换后等待新首页身份及 11 个 CSP 哈希实际生效；源站和公网分别校验 298 个实际文件、15 个入口、查询参数、访问方法/点路径限制及两份 PDF 的 206 字节内容，均通过。
- `browser/matrix.json`：公网新增十八页及书架在 1440/390px 的 38 个视图通过，整页横向溢出为零。`browser/public-interactions.json`：五书入口 10 视图、题目深链 4 视图、公式复制 10 例、两份实际源码下载及哈希通过；桌面目录、右侧注解与手机折叠按各自视口呈现。公网截图已查看，程序和实际显示证据分别保存。
- `browser/pdf-page-104.png`：浏览器页码为 104/282，实际显示 Durrett 第二章 Poisson Processes、印刷 95；两个已公开 PDF 的响应身份与范围读取由 HTTPS 记录分别验证。
- `server-final.json`：current 指向新版本，Nginx active，配置语法检查通过；证书和其他站点的配置/链接与发布前一致。没有执行实际回滚；已保留并核对完整恢复单元。

发布包、源码和线上字节一致；详细推导、既有校注和算法契约沿用本轮已核对内容。Git 末尾验收提交完成后再读回本地、跟踪分支、远端身份与空工作区，结果保存为该发布目录的 `final-readback.json`。
