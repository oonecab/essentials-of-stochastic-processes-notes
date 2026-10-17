# Astro 生产发布记录（I029）

2026-10-17，用户在本地迁移验收后明确授权提交、推送和部署。五书静态站点已发布到 [Reading Notes](https://notes.zzzping.top/)，版本为 `20261017T174039`；Node/pnpm 仍只用于构建，Ubuntu 的 Nginx 直接提供静态文件。实施依据见 [I029](../issues/I029-astro-production.md)、[P029](../plan/P029-astro-production.md)、[T029](../test/T029-astro-production.md) 和 [ADR-002](decisions/ADR-002-static-first-astro.md)。I028 的本地迁移报告与书级历史审阅保持。

## 版本与发布方式

新包从干净提交 `90c784d039982037ddb98cf62d1a5b1d5196ad80` 构建，303 个公开文件、54 个正式笔记页及书架，总计 28,771,319 字节；压缩包 10,695,615 字节。`SHA256SUMS` 与 `site.tar.gz` 均与 I028 验收包 `20261017T172621` 逐字一致：

- SHA256SUMS 文件：`10ce03afae12150a07b051d70aa683e714ae0965bc7e43233215ac810dc4b025`
- site.tar.gz：`c88c0ed6efb8db836d2adf8fdd93d2c6be2141e9aedc3a5cc868812985df5a8b`
- release.json：`afea5557f9fba6ca537c0d8fa88aadb3fa5dab70be18bd5203cbfaae2d5a1b3a`

生产环境实测为 Ubuntu 22.04.3、Nginx 1.18.0、Python 3.10.12、rsync 3.2.7、util-linux flock 2.37.2。`reading-notes-deploy.service` 以无登录的 `reading-notes` 系统用户运行，使用精确授权的 root helper 检查和重载 Nginx。发布工具由 root 拥有，发布用户不能修改 helper、Nginx snippet 或 PID 文件。部署工具对应提交 `4aaf9f9047b69ad652164fd0989d35f3d36e2623`，安装文件逐一比对当前仓库 SHA256；它在构建提交之后只修正了部署沙箱，不改变页面字节。

17:47（Asia/Shanghai）完成一次性发布，systemd 结果为 `success`、退出码 0，队列包移入 done；timer 保持 disabled。本次不需要在 Web 主机安装 Node 或启动构建服务。目录为：

```text
/srv/reading-notes/releases/20261017T174039/site/
/srv/reading-notes/current -> releases/20261017T174039
/var/spool/reading-notes/done/20261017T174039/
/var/lib/notes-deploy/20261017T174039/
```

release 的 27 个目录为 0555，303 个公开文件及 3 个站外元数据文件为 0444。SHA256 清单及 release.json 位于 web root 外。原站点仅替换静态 include，证书、TLS 选项、ACME 路径、日志位置和续期配置保持；其他三个既有站点的配置、current 和源站首页响应均与发布前一致。

## 验证与实机修订

本次完整 Python 检查 14 项通过，报告 `tmp/project-check/20261017T173935-ujlp932y/report.json`。doctor、Astro build、54 页 parity 与临时 Nginx HTTPS 验证均退出 0；内容与 I028 已验收包逐字相同，因此原四视口离线、数学与程序证据继续适用。新包本地 HTTPS 报告为 `tmp/release-check/20261017T174039-94su_hsr/https-verification.json`。

Ubuntu 的初次沙箱预检实际失败：`ProtectSystem=strict` 使 `nginx -t` 打开 `/run/nginx.pid` 时得到只读文件系统错误。线上旧站尚未切换。修订 unit 只为这个 root 拥有的文件增加 `ReadWritePaths`，仍保留 ProtectSystem、ProtectHome、PrivateTmp 和文件权限；相同预检随即退出 0，真实发布服务也成功。修订前后日志均保留。

Ubuntu 隔离目录再次执行真实发布回归，13 项全部通过：私有路径/链接/原始审阅拒绝、不可变版本、实际 flock 冲突、原子指针切换、Nginx test/reload 故障回滚、显式回滚、事务恢复、当前文件损坏后回退、队列回执幂等，以及临时 HTTPS 的全部文件和路由。报告 `deploy/reports/20261017T174039/linux-tests/package-tb28yp20/report.json`；临时 Nginx 已停止，隔离目录在证据取回后清理。该测试与真实生产 systemd 发布分别记录，没有为演练主动回退在线站点。

源站和公网 HTTPS 各验证了 298 个直接文件的 SHA256、MIME、CSP、缓存，15 个旧入口的重定向、查询参数、HEAD/POST，以及两份已授权 PDF 的 206 Range 与字节。服务器另外确认 gzip、ETag 304、HSTS、303 个部署文件哈希、权限和私有路径 404；current 无未完成事务。

公网 ego-browser 验收覆盖 55 页 × 1440/390 两视口，共 110 个 JS 视图，另有 55 个关闭 JS 的视图、196 次深链定位、54 次手机目录点击和 51 次局部横滚。矩阵保存 209 张截图，未发现整页横向溢出、脚本/安全策略错误或外部资源请求。目视读回书架、五书首章桌面/手机布局与习题、公式及 no-JS 样本；五书两视口的书架→地图→第一章→第二章→书架，共 10 条点击路径均通过。浏览器驱动曾误选折叠目录中的隐藏链接，保留失败日志后改用可见正文导航并完成余下路径；未修改站点来规避验收。

两份原书 PDF 也通过实际点击打开：CS:APP 第 38/1122 页显示第一章扉页，Durrett 第 10/282 页显示 Markov Chains 起页；页码与来源链接一致，截图及查看器快照见 `browser/pdf.json`。

原始证据集中于忽略目录 `deploy/reports/20261017T174039/`：`local-release.json`、`origin-https.json`、`public-https.json`、`server-contracts.json`、`installed-tools.json`、`service-publication.log`、`activation.log`、`browser/report.json`、`browser/interactions.json`、`linux-tests/`。提交前使用高置信凭据模式扫描；Gitleaks 未安装，不把该扫描表述为 Gitleaks 全量审计。认证输入不写入仓库、日志或发布包。

## 恢复与边界

首次目录迁移的恢复单元包括旧 `current -> releases/20261017T151424`、完整旧目录、旧站点配置及元数据，均保持原位并重新验证 SHA256。新包激活脚本在配置、重载或源站全量校验失败时自动恢复旧 vhost；实际激活成功。管理员可在服务器执行：

```sh
python3 /var/lib/notes-deploy/20261017T174039/restore-legacy.py
```

该脚本先验证旧发布文件，再原子恢复旧站点配置、执行 nginx -t 和 reload；新 Astro 目录保留。未来同一 /srv 布局内的版本回退仍使用 `publish.sh --rollback <id>`，中断恢复用 `--recover`，见 [Ubuntu 说明](../deploy/UBUNTU.md)。

当前公网 HTTP 请求返回 403，源站 HTTP 返回 301；该边界在旧部署记录中已出现，本次没有更改 DNS、证书续期或网络接入配置。发布验收确认的是 HTTPS，分享使用完整 HTTPS 地址。CS:APP 12.39 代理实验的历史未验收状态保持，不能由本次部署验收代替。

代码已快进推送 origin/main；最终验收文档随后单独提交。最终 HEAD、origin/main、远端 main 及服务器版本的读回记录保存在该发布目录的 `completion.json`，避免将验收记录提交误记为页面构建来源。
