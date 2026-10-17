# Astro 内容与独立检查

受控正文位于 `src/content/books/<book>/`，一章一份 HTML，文件头为 JSON frontmatter。共享 CSS/JS 在 `src/styles/`、`src/scripts/`，由 `RN:include` 标记按原字节展开。`ReaderLayout` 提供 head/body 骨架，组件保留语义片段边界，静态 MathML/SVG 不经重排。目录、注解与复制是独立的渐进增强脚本；基础阅读和原生 details 使用静态 HTML。

`books/<book>/notes/*.html` 是受控源展开后的兼容镜像，供原 Python 检查器独立读取。构建在验证受控源身份后自动生成镜像；`node scripts/sync-legacy.mjs` 单独检查一致性，`--write` 单独生成。兼容快照暂时随 Git 保留以支持独立检查与回滚，正文的唯一权威源是 `src/content/books/`。C/Python 程序仍遵循各书原代码维护入口，先把显示块同步进受控章节，再展开镜像并运行原检查。Weiss 的教学程序维护于受控章节内。

迁移期间 `scripts/migration-state.json` 固定起点，`original_sha256` 和 `git show` 双重守卫禁止正文变化。未来数学内容修订须另开受审阅的变更，连同原题/条件/代码、来源清单、Python 基线、当前审阅绑定与新 golden master 一起更新；不能以同步镜像命令自动认可内容变化。共享资源文件的哈希名称只为去重，不构成内容正确性的证明。

I032 开始，迁移后的明确内容修订在 `src/content-revisions.json` 逐页登记原始 hash、连续修订链、具体锚点、理由及独立内容审阅记录。原始 frontmatter hash、I028 Git 快照和旧审阅数据保持；当前内容必须同时匹配登记值和审阅记录，并保持原习题 ID 与原锚点顺序。构建 parity 比较当前已审阅源经同一发布转换后的全部 DOM，历史零差异迁移与后续内容修订分开陈述。登记脚本不能自动批准正文；每项实质修改先读回再填写原因和证据。

工具链为 **Node/Astro + Python build helpers**：Node 24.21.0、pnpm 11.21.0、Python 3.10+；Python 的 build_portal、prepare-pages、public_policy 参与构建，原独立验证器另行运行。准备本地来源资料，并安装 C/Make/Poppler（完整验证）、Nginx/OpenSSL（发布演练）和可运行的 Ego Lite / ego-browser CLI（浏览器验收），然后执行 `pnpm install --frozen-lockfile`、`pnpm build`。生产 HTTP 仍只由 Nginx 提供。

`pnpm build` 在临时目录准备来源并构建，对全部公开 HTML（当前 74 页，含辅助页和 5 个旧入口页）内联 CSS、favicon 和脚本；下载文件保留链接。正式页完整 DOM 的标签、命名空间、属性和子节点顺序、习题 ID 序列，以及正文/MathML/SVG/代码指纹和内部锚点一起核对。页面数量来自受控条目清单，新增书籍按 catalog、migration-state 与发布 allowlist 登记，不修改固定页数。

构建还启动环回临时 HTTP 服务，以生产 CSP 模板在真实浏览器覆盖每种内联脚本，确认哈希变异被浏览器阻止；打包再校验这些页面和脚本的指纹。所有门禁通过后才替换 `dist/`，保留上一份输出。`node scripts/verify-parity.mjs --book <book>` 比较冻结源和旧发布视图；`node scripts/check-offline.mjs --book <book>` 用 Ego Lite 实际断网打开该书全部公开页面，验证 1800/1440/1024/390 四档、1440/390 两档无 JS、深链、目录和局部横滚；旧入口验证其本地跳转目标。完整命令从仓库根执行，构建与浏览证据写入忽略目录 `tmp/reading-notes-migration/`。

逐书 `review/astro-migration.json`、`content-baseline-astro.json` 和 `release-astro.json` 是新增的迁移证据。旧数学审阅、来源材料、内容完整性基线和程序记录保留原有含义。仅因维护说明改动而更新的当前文档哈希，必须同时保存旧值及原因。
