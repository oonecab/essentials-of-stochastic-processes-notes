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
