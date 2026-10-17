# P029：生产发布计划

关联 [I029](../issues/I029-astro-production.md)。

1. 核对本地、远端、目标主机、依赖、当前版本、证书及其他站点，保存恢复材料。
2. 重新运行 doctor、完整 Python 检查、parity；提交发布准备记录，从干净提交构建新版本，并与 I028 已验收包核对 SHA256SUMS 和 archive 字节。
3. 快进 main，推送并读取远端引用。上传不可变包及受控发布工具，校验传输哈希。
4. 安装非 root 发布用户、root 拥有的工具及限权 helper；安装 deploy oneshot unit，timer 保持停用，构建继续在本地执行。
5. 使用真实 Linux flock/SHA256/rsync/systemd 执行发布；将现有 vhost 的静态 include 切到 root 拥有的 snippet，nginx -t 后重载，失败恢复旧 vhost。
6. 验证源站与公网全部发布字节、CSP、重定向、MIME、Range 和访问边界；浏览器检查桌面、手机、五书导航、深链及 PDF。确认其他站点配置及 current 未变。
7. 记录实际结果和回滚命令，同步权威文档，提交推送验收记录，再读回 Git 与线上状态。
