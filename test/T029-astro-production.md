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
