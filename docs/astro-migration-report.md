# Reading Notes 静态优先迁移交付报告

2026-10-17。状态：**带保留完成**。本地迁移与发布演练结论为 **Go**；Ubuntu/systemd 的实机安装仍需在目标环境验收。此次授权范围内没有远程推送或生产部署。最终包 `20261017T172621` 的构建来源为 `f35efd0c7b548369321805781fbf81bce71df686`，构建时工作区干净。

## 改动与等价边界

五书 54 页与书架已由 Astro 7.4.0 输出为单文件 HTML，Node 24.21.0 / pnpm 11.21.0 只在构建机使用。逐章受控源及共享组件/资源位于 src，旧 HTML、原 Python 检查器、数学输入和全部历史审阅保留。生产模板仍只提供 Nginx 静态服务；渐进增强使用现有脚本与独立小岛，未需要 React 或服务端运行框架。

| 书籍 | 页数 | 原书题 | 自测 | 陈述容器 | MathML | 内容 SVG | 成品 HTML 字节 | JS 字节 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 测度概率 | 6 | 115 | 0 | 126 | 2707 | 4 | 1,198,698 | 24,924 |
| 视觉群论 | 12 | 302 | 0 | 62 | 387 | 198 | 1,900,939 | 81,475 |
| 随机过程 | 9 | 236 | 0 | 150 | 13009 | 7 | 5,986,389 | 38,155 |
| Weiss | 13 | 362 | 0 | 0 | 4594 | 227 | 6,419,695 | 23,881 |
| CS:APP | 14 | 419 | 36 | 114 | 656 | 50 | 2,812,864 | 88,830 |

合计 54 页、1434 道原书题、36 道自测、452 个已标记陈述容器、21353 MathML、486 内容 SVG。陈述容器包含定义/原文容器，Weiss 未使用此标记，因此不将 452 冒充全书编号定理总数。旧发布视图已有每页一个导航 SVG，发布页总 SVG 为 540；导航图标不属于新增数学图。

| 比较项 | 结果与差异解释 |
|---|---|
| 54 份原 HTML / 展开后的受控源 | 字节相同；冻结提交 b2aeff3、frontmatter SHA 与当前兼容镜像三方一致 |
| 正文、MathML/SVG 树与原片段、题号、代码 | 全部相同 |
| 原 URL、锚点、PDF #page、相对链接 | 全部相同 |
| CSS 与 head 元数据 | 原内容相同，共享 reader.css 内联以满足离线契约 |
| 原内联 JS | 全部保留；CS:APP 每页另增 590 字节定位岛，共 8260 字节 |
| JS 体积 | 249005 → 257265 字节；最高逐页比 1.102520，低于 1.5 |
| 37 个旧审阅/校验 JSON URL | URL 保留，内容改为固定公开摘要；原私有记录留在仓库，逐项路径见 deploy/publish-allowlist.json |
| PDF | 两份已授权 PDF 保持路径和字节；其余原 PDF 保留本地 |

未重写数学、算法、题号、小问或来源条件。原始源码副本与执行输入保持；原数学审阅与实际运行证据的适用范围继续有效。迁移只追加 content-baseline-astro、release-astro、astro-migration 与最终验收绑定，文档哈希变更保存原值及原因。

变更包括 src 内容/布局/组件/资源、固定依赖、迁移和 parity 工具、Node 打包、Python 独立绑定检查、公开策略、Ubuntu Nginx/systemd/发布工具以及治理记录。完整文件清单见 [变更文件清单](astro-migration-files.txt)；决策见 [ADR-002](decisions/ADR-002-static-first-astro.md)，编写流程见 [Astro 维护说明](astro-authoring.md)，发布操作见 [UBUNTU.md](../deploy/UBUNTU.md)。

## 验证结果与可复现发布

下列命令实际运行的退出码均为 0，原始 stdout/stderr 保留。表中路径相对仓库根；具体秒数、输入/产物身份及报告哈希见 [结构化证据](astro-migration-evidence.json)。

| 命令 | 退出码 | 日志 |
|---|---:|---|
| `python3 tools/project.py doctor` | 0 | `tmp/reading-notes-migration/final/doctor.log` |
| `pnpm install --frozen-lockfile` | 0 | `tmp/reading-notes-migration/final/install.log` |
| `pnpm build` | 0 | `tmp/reading-notes-migration/final/build-1.log` |
| `node scripts/verify-parity.mjs` | 0 | `tmp/reading-notes-migration/final/parity.log` |
| `pnpm check:parity` | 0 | `tmp/reading-notes-migration/final/parity-alias.log` |
| `node --test scripts/parity.test.mjs` | 0 | `tmp/reading-notes-migration/final/node-tests.log` |
| `python3 tools/project.py check` | 0 | `tmp/reading-notes-migration/final/python-all.log` |
| `python3 tools/project.py check --book measure-probability` | 0 | `tmp/reading-notes-migration/final/python-measure-probability.log` |
| `python3 tools/project.py check --book visual-group-theory` | 0 | `tmp/reading-notes-migration/final/python-visual-group-theory.log` |
| `python3 tools/project.py check --book stochastic` | 0 | `tmp/reading-notes-migration/final/python-stochastic.log` |
| `python3 tools/project.py check --book weiss` | 0 | `tmp/reading-notes-migration/final/python-weiss.log` |
| `python3 tools/project.py check --book csapp` | 0 | `tmp/reading-notes-migration/final/python-csapp.log` |
| `python3 tools/project.py build` | 0 | `tmp/reading-notes-migration/final/release-build.log` |
| `python3 tools/project.py verify-release --release-id 20261017T172621` | 0 | `tmp/reading-notes-migration/final/verify-release.log` |
| `python3 tools/test_static_publish.py --release-dir deploy/portal-releases/20261017T172621` | 0 | `tmp/reading-notes-migration/final/publish.log` |
| `node scripts/check-offline.mjs` | 0 | `tmp/reading-notes-migration/final-offline.log` |
| `pnpm check:offline` | 0 | `tmp/reading-notes-migration/final/offline-alias.log` |

Python 全量报告：`tmp/project-check/20261017T171328-afbgru05/report.json`。原 13 项全量检查继续执行，追加当前 Astro 源与审阅绑定检查，共 14 项；五书的完整检查也分别重跑。

浏览器实际断网使用 file 协议，覆盖 55 页 × 1800/1440/1024/390 四个宽度，共 220 个 JS 视图与 55 个 390px no-JS 视图，319 张截图并核验哈希。目录高亮、手机折叠、代表性首末题深链、注解栏和适用页面的真实局部横滚通过。无脚本时每页静态数学/图数量一致，并实际点击代表性原生 details 查看题干与答案。全程外部请求 0；这里不声称逐个点击了所有 1434 个答案。

`node scripts/check-offline.mjs` 与 `pnpm check:offline` 两次完整运行均通过。前一轮原图保留在 `tmp/reading-notes-migration/browser/all-node-run/`，relocation.json 记录归档前缀；最终矩阵为 `tmp/reading-notes-migration/browser/all/report.json`。各书逐页首屏、各章题解/no-JS 联系图及代表性 1440/1024 原图均实际查看，书架五个视图另行看图。

两个最终 Node 构建阶段用时 41.222 / 40.399 秒；含归档的根 build 命令为 45.423 秒。Node 阶段包含旧独立结构检查、Astro、内联、parity 与发布策略。303 个公开文件共 28,771,319 字节，其中 74 个 HTML，54 个正式阅读页共 18,318,585 字节；压缩包 10,695,615 字节。相同输入的逐文件清单与三个版本归档字节相同，记录为 `tmp/reading-notes-migration/final/reproducibility.json`。

- SHA256SUMS 文件散列：`10ce03afae12150a07b051d70aa683e714ae0965bc7e43233215ac810dc4b025`。
- site.tar.gz 散列：`c88c0ed6efb8db836d2adf8fdd93d2c6be2141e9aedc3a5cc868812985df5a8b`。

最终本地 HTTPS 报告：`tmp/release-check/20261017T172621-yexqb_ax/https-verification.json`；发布演练：`tmp/publish-check/20261017T172621-zge0662j/report.json`。真实 Nginx 验证 298 个非重定向文件哈希、MIME、CSP，15 个旧入口及查询参数/HEAD/POST，两份 PDF 的 206 与真实字节，HTTP→HTTPS、gzip、ETag 304、HSTS、私有路径及内部 symlink 拒绝。13 类发布集成检查通过，包括 flock 并发拒绝、已有版本拒绝覆盖、观测原子切换、nginx test/reload、故障自动回滚、中断事务恢复、损坏活动版本回滚及队列回执恢复。

发布结构是不可变 releases/<id>/site 加私有 SHA256SUMS/release.json，通过临时 symlink 与 POSIX rename 原子替换 current。生产模板由 root 持有固定 Nginx 配置，非 root 发布用户只能调用固定 test/reload helper；新脚本 CSP 必须审查安装，避免可写 release 配置被 root 直接 include。

## 保留项与最终门禁

全部迁移门禁通过，open_migration_findings 为空。保留范围为：Ubuntu/systemd 和 util-linux flock 命令分支没有在 Linux 实机运行（本机使用 fcntl.flock 与真实 macOS Nginx）；实体手机和真实读屏器未验；CS:APP 12.39 原代理浏览器实验保持历史未验收边界。公开站点、远程 Git、DNS、生产证书没有变更。

Weiss 原样导入 SVG 的 8529 处原行尾空白保留，整段导入的 Git whitespace 检查非零；新工具/文档 diff --check 通过。没有为使检查变绿而改写这些源字节。凭据检查使用高置信度模式扫描，未安装 Gitleaks，不把此范围称为全面秘密审计。

试点及中间失败、修复原因和原日志见 [T028](../test/T028-static-first-astro.md)：包括 head 内联丢失样式、旧深链展开定位、资料页相对链接、macOS 只读目录改名与测试端口变量遮蔽。没有改变数学期望、删除 fixture 或放宽原 Python 断言。

旧原 HTML、旧构建器、原 release 20261017T151424 和冻结基线仍可用。新布局若部署到 Ubuntu，按 UBUNTU.md 保存原生产目录/配置后执行切换；当前任务只交付经过本地演练的发布件。

最终审阅记录与报告追加后，再运行 `python3 tools/project.py check --quick` 退出 0，报告 `tmp/project-check/20261017T172823-u8vpbh9r/report.json`；正文与程序输入未再变化。`tools/check_astro_records.py` 和最终五书证据绑定核验同样通过，记录为 `tmp/reading-notes-migration/final/final-binding.json`。

后续生产发布与 Ubuntu 实机验证已在 [I029 发布记录](astro-production-report.md) 单独登记；本文保留本地迁移阶段的命令、来源与交付边界。
