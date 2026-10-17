# T029：生产验收设计与执行

关联 [I029](../issues/I029-astro-production.md)。本次只改变发布环境，I028 的数学、离线与四视口全量证据继续保留；新构建必须与该包逐字一致才能复用阅读证据。

验收项：

- doctor 与完整 Python 检查退出 0，54 页 parity 无差异；干净源码构建，SHA256SUMS 和归档与 I028 一致。
- 本地 main、origin/main、git ls-remote main 一致；工作区干净。
- Ubuntu 实机读取不可变 release 的 303 个文件哈希、只读权限和原子 current；发布使用非 root 用户、util-linux flock、rsync 和受限 nginx/systemd helper。
- systemd oneshot 真实成功、队列移入 done；timer 未启用；无新增 Node/Python HTTP 服务。
- 源站与公网验证 298 个直接文件、15 个入口重定向、两份 PDF Range、MIME、CSP、缓存和私有路径；检查 gzip、ETag、HSTS。
- 真实桌面与手机阅读、五书目录及跨章导航、习题深链展开、高亮与 PDF 页序；保存截图和浏览器报告，页面/安全策略错误必须说明。
- 已保存旧配置/current/版本及可执行恢复步骤；Nginx 配置检查失败不得留下错误配置；其他虚拟主机状态保持。

执行报告写入被忽略的 deploy/reports/<release-id>/；验收完成后在本文件追加命令、退出码及证据路径。此前 macOS 故障注入证据仍见 T028，不将其冒充 Ubuntu 故障演练。

实机反例：2026-10-17 在与发布 unit 相同的沙箱中运行受限 helper，旧 unit 的 `nginx -t` 因 `/run/nginx.pid` 为只读挂载而退出 1；旧站未切换。修订仅为 root 拥有的 PID 文件增加 `ReadWritePaths`，不开放整个 /run，不改变文件属主或权限。修订前日志保存为 `systemd-preflight.log` 与 journal 摘录，修订后以相同预检及真实发布服务验收。

## 执行结果

- `python3 tools/project.py doctor`：0；本地版本与锁定工具链匹配。
- `python3 tools/project.py check`：0，14 项完整检查，`tmp/project-check/20261017T173935-ujlp932y/report.json`。
- `python3 tools/project.py build --release-id 20261017T174039`：0；303 文件、54 笔记页；SHA 清单和归档与 I028 完全一致。
- `node scripts/verify-parity.mjs`：0；54 页正文、MathML、SVG、锚点、链接及原代码保持。
- `python3 tools/project.py verify-release --release-id 20261017T174039`：0，`tmp/release-check/20261017T174039-94su_hsr/https-verification.json`，临时 Nginx 已停止。
- Ubuntu 同沙箱预检：修订前 1，精确加入 PID 文件例外后 0；真实 `reading-notes-deploy.service`：0。发布用户不能写 root 配置/helper/PID。
- Ubuntu `tools/test_static_publish.py`：0，13 项，最终报告 `deploy/reports/20261017T174039/linux-tests/package-tb28yp20/report.json`。先前测试成功，但报告限制文字固定写 macOS；修订为与平台无关的真实边界后重跑并保留两轮报告。
- `deploy/verify_portal.py` 对源站/公网各退出 0：298 直接文件、15 重定向、两份 PDF 206 Range。额外 gzip/ETag/HSTS/权限/私有路径通过。
- ego-browser 公网矩阵：0，110 个 JS + 55 个 no-JS 视图、209 截图、196 深链、54 手机目录点击、51 局部横滚；运行时错误和外部资源请求均为 0。十条五书跨章点击路径通过。
- 文档编写中的快速检查曾发现尚未创建的发布报告链接，原失败日志保留 `quick-during-authoring.log`；报告落盘后重新运行完整快速检查。

公网 HTTP 实测 403，而源站 HTTP 返回 301；只将 HTTPS 标为上线通过。证书/TLS/续期配置和其他三个站点配置/current/源站响应未变。原始证据位于 `deploy/reports/20261017T174039/`，总结见 [生产发布记录](../docs/astro-production-report.md)。

最终快速检查退出 0：`tmp/project-check/20261017T175557-9xspn6q4/report.json`（11 项）。已验证公开 JS 视图的非 Document 请求均为 data URL，没有额外网络子资源请求。

两份 PDF 浏览器跳转通过：CS:APP 第 38/1122 页、Durrett 第 10/282 页均与链接页序一致，并目视确认章节起页。报告 `browser/pdf.json`。
