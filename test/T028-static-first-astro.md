# T028：静态迁移验证

关联 [I028](../issues/I028-static-first-astro.md)、[P028](../plan/P028-static-first-astro.md)、[M028](../milestone/M028-static-first-astro.md)。

## 设计与故障检出

golden master 分为旧维护源和旧发布视图：前者证明正文、数学及源码副本保持；后者证明既有 URL、资料链接、页码与书架导航保持。冻结基线来自迁移前提交，不在测试中重新生成期望值。比较正文文本、MathML/SVG 树与原始片段、锚点、链接、习题和陈述标记。用删题、改公式、改锚点/链接、漏 CSS/JS 内联的反例验证失败能力。

旧发布版 54/54 阅读页引用 `reader.css`，不满足单文件资源约定；该预期失败已写入 `tmp/reading-notes-migration/baseline/old-published-offline-dependencies.json`。新检查必须检测本地 CSS 依赖，不能只禁止 CDN。

每批实际运行安装、Astro 构建、parity、离线浏览器和按书 Python 检查；试点重复构建比较文件 SHA256SUMS。浏览器覆盖 1800/1440/1024/390，file 协议、断网、脚本关闭、原生折叠、目录标记、深链展开、注解和局部横滚；页面对象及截图哈希绑定到实际产物。截图生成与实际看图分别记录。

发布验证覆盖 allowlist、路径穿越、符号链接、已有 release 拒绝覆盖、并发锁、nginx 配置失败及 reload 失败后的恢复。临时 Nginx HTTP/HTTPS、CSP、MIME、重定向、PDF Range 与全部文件哈希独立验收。实际生产及实体手机保持未执行。

## 已执行证据

2026-10-17，原始 `python3 tools/project.py doctor` 和 `python3 tools/project.py check` 均退出 0；检查报告 `tmp/project-check/20261017T154418-nls22x5i/report.json`。`baseline/inventory.json` 位于 `tmp/reading-notes-migration/`，覆盖 54 页及源元数据哈希；`baseline/published-release.json` 对应旧包 `20261017T151424`。影响清单为同目录 `impact.json`。

后续阶段结果待实际执行后追加；这里的测试设计不代表已通过。

空壳阶段：固定依赖安装与 `pnpm install --frozen-lockfile` 退出 0；`pnpm build --shell` 最终退出 0，构建输出一页，0.579 秒。此前两次配置适配失败分别是 Astro 7 CLI 入口变更及 publicDir 类型要求，日志保留为 `scaffold-build.log` 和 `scaffold-build-retry.log`；修复后使用包声明的入口和受控 public 目录。构建子进程显式设置 ASTRO_TELEMETRY_DISABLED=1；首次 CLI 提示默认遥测，后续执行已禁用。Ego Lite TaskSpace 23 实际打开构建壳，断网并关闭 JS 后标题和正文可读，图像 `tmp/reading-notes-migration/scaffold.png`。正式书籍尚未迁移。


试点门禁：measure-probability 六页、115 题、2707 MathML、4 SVG 与冻结源一致。最终构建 `measure-build-4.log` / `measure-build-5.log` 退出 0；同输入 303 文件的 SHA256SUMS 完全一致（清单哈希 `ed3e84bd9d01018ed0130a6c33482af027c4d1d5d4f065687d8b5346fb21c3b5`）。总构建分别 31.139 / 30.885 秒，后者 Astro 294 ms。六页 HTML 共 1,198,698 字节，内联 JS 24,924 字节，为旧发布页的 1.0 倍。

`measure-parity-verified.log`、`measure-offline-verified.log` 均退出 0。Ego Lite 对 6 页完成 24 个脚本开启视图与 6 个 no-JS 视图；全页静态资源检查及实际 CDP 请求观测均为零子资源。逐页查看联系图，确认桌面目录/注解、窄屏题解、长公式局部横滚和原生折叠可读；图像原件及哈希在 `browser/measure-probability/report.json`，迁移证据另存书级 `review/astro-migration.json`，历史审阅及数学内容基线保持。

试点中检出的实际回归：ReaderLayout 的 head 特殊指令造成 CSS 丢失，手机整页宽 485px。修正显式 head 子节点后重新构建与浏览全矩阵；parity 新增标题、meta 和完整样式内容比较，`head-regression-rejected.log` 退出 1 证实能拒绝失败产物。另两次浏览驱动失败分别为注解镜像被重复计数，以及高表格横滚坐标落在固定顶栏；均与旧页面/真实输入复核后修正测量，原失败记录保留。原生交互、数学库存、宽度及滚动断言继续执行。

试点结论：Go。未解决的迁移问题为空；历史内容审阅的范围、实体手机和真实读屏器边界保持。

试点文档绑定更新后独立 Python 再验退出 0：`tmp/project-check/20261017T162314-9oiv5rvl/report.json`，四个命令均通过；`node --test scripts/parity.test.mjs` 三项测试通过。

视觉群论批次 Go：12 页 / 302 题，源计数 387 MathML / 198 SVG / 62 陈述，全部 parity 差异为 0；HTML 1,900,939 字节，JS 81,475 字节，比例 1。构建 31.691 秒；`vgt-build`、`vgt-parity`、`vgt-offline`、`vgt-python` 日志的退出码全部为 0。独立检查报告 `tmp/project-check/20261017T162448-4ryv1zvk/report.json`；48 个 JS 视图和 12 个 no-JS 视图通过，逐页首屏与各章题解截图实际看图。原审阅及原 HTML 保持，文档维护路径的旧哈希与新值追加记录。

随机过程批次 Go：9 页 / 236 题，13009 MathML / 7 SVG / 150 陈述，parity 差异 0；HTML 5,986,389 字节，JS 38,155 字节，比例 1.0。构建 35.570 秒；`stochastic-build`、`stochastic-parity`、`stochastic-offline-2`、`stochastic-python-2` 退出 0；独立报告 `tmp/project-check/20261017T162900-95_1u10w/report.json`。36 个 JS 视图和 9 个 no-JS 视图通过，逐页看图。初次 Python 检查拦住维护说明旧哈希，按依赖顺序保留旧值并更新文档及记录绑定后通过；初次深链检查取到了章节内隐藏摘要，旧页和新页矩形一致，修正为目标章节本身后通过。原失败日志和 `stochastic-deep-link-diagnosis.json` 保留。

Weiss 批次 Go：13 页 / 362 题，4594 MathML / 227 SVG，原书未使用 statement 容器（计数 0）；parity 差异 0。HTML 6,419,695 字节，JS 23,881 字节，比例 1.0。构建 37.815 秒；`weiss-build`、`weiss-parity`、`weiss-offline`、`weiss-python` 退出 0；独立报告 `tmp/project-check/20261017T163237-h49kv28l/report.json`，包含原 C 图例和教学程序提取执行。52 个 JS 视图和 13 个 no-JS 视图通过，逐页看图；新增迁移审阅入口承接该书原来的散列证据结构。

Weiss 原样导入的 SVG 含 8529 处原有行尾空白，`git show --check 1e145db` 退出非零并保留完整日志 `weiss-original-whitespace.log`；受控源展开字节与冻结原页相同，因此没有清理这些空白，未把该检查记为通过。后续完整构建检出了新维护文档链接未随读者资料页发布，已改为仓库路径说明；现有读者 URL 和 54 页正文链接保持。

CS:APP 批次 Go：14 页 / 419 道原书题 + 36 道自测，656 MathML / 50 SVG / 114 陈述。原正文、数学、链接和脚本 parity 差异为 0；每页单独登记新增 deep-link-settle 导航岛，HTML 合计 2812864 字节、JS 88830 字节，最高比例 1.10252。`csapp-build-4`（40.200 秒）、`csapp-parity-final`、`csapp-offline-4`、`csapp-python`、`csapp-node-tests-final` 退出 0；独立报告 `tmp/project-check/20261017T163622-tcal2v6u/report.json`。实际查看全部首屏与各章题解截图；56 个 JS 和 14 个 no-JS 视图通过。

CS:APP 中间失败均留档：继承的页尾深链在 details 展开增加文档高度后，目录可能仍停上一节；增加稳定等待仍能复现，最终新增两帧后重新定位的独立小岛，未改变原脚本。迁移 parity 只分离逐字节核验的新增岛，其他脚本仍严格比较，新增反例测试拒绝缺失、变更或错误书籍的岛。浏览驱动不支持 Browser.getVersion，改采实际 navigator.userAgent；一次 Astro 打包路径解析错误改为构建根路径后通过。原 CS:APP 12.39 的代理浏览器实验边界保持，不由页面迁移验收替代。

发布层首次完整通过：`phase6-build-2` 退出 0，包 `20261017T170533`；303 文件 / 74 HTML，其中 54 正式阅读页，28,771,319 字节。白名单的 37 个历史 JSON URL 输出固定摘要，正文不变；两份授权 PDF 加固定 SHA 校验。`publish-test-3` 退出 0，报告 `tmp/publish-check/20261017T170533-nia0s55d/report.json`，10 类检查包含真实 SHA/rsync/flock、不可覆盖、原子链接、实际 Nginx test/reload、配置失败与重载失败自动恢复。HTTPS 验收 298 个非重定向文件、15 个旧路由、两个 PDF 范围，另验 HTTP 跳转、gzip、ETag 304、HSTS、内部 symlink 拒绝。

最初两次发布演练失败日志 `publish-test.log`、`publish-test-2.log` 保留：macOS 不允许重命名已经只读的候选根目录，改为先改名再冻结权限；测试中的 HTTP 端口变量遮蔽模块名，修正命名。失败候选从未进入 current。归档旧部署说明时相对链接错误由原结构检查检出，调整归档链接后 `governance-quick-2` 退出 0。

新增 `tools/check_astro_records.py` 使用 Python 独立展开受控源、比较冻结 Git 字节、检查所有当前文档和迁移审阅绑定；原 13 个全量命令保持，并追加这一项。完整发布集成测试的 Linux 分支与 systemd 运行需在 Ubuntu 上另验，本机运行平台是 macOS。
