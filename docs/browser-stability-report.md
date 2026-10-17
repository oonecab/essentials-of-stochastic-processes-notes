# I033：离线验收稳定性与生产迁移结果

2026-10-17，本地复评修复和生产上线已完成；生产为 `20261017T210828`。DNS 自动续期及用户自行轮换 root 密码仍开放，不能将本报告解释为全部服务器安全项已关闭。

## 修复与本地证据

深链执行及最终读回等待目标存在，单次 evaluate 同时确认预期 URL、取得节点并读取状态；瞬时缺失有界重试，错页与真正缺失明确失败。重定向和没有习题的辅助页不再走习题深链。CSP/离线共用会话锁，避免同时导航同一个页面。复评中的报告与日志进度不一致已原样留存，未将并发推断写成已查明的唯一根因。

每轮验收使用 UTC 时间与随机 ID 的独立目录，报告以临时文件、fsync 和原子替换保存；失败报告和截图完整保留。父目录 `report.json` 是最后成功结果，`latest-attempt.json` 是最新尝试。真实失败注入证实：旧成功报告和 488 张截图的哈希保持不变；运行中的第二个验收命令被拒绝。

失效缓存仅在精确 `task space not found: <ID>` 时新建命名空间。`READING_NOTES_CSP_SPACE` 显式指定空间；用户控制、inactive、权限、超时、未知错误及失效显式 ID 都直接失败。恢复及错误分支有单元回归；真实 Ego 的失效 ID 错误已实测，正常复跑复用空间 26。验收结束关闭该空间并清除对应缓存。

| 验证 | 本次结果 |
|---|---|
| Node 回归 | 18 项通过；包含节点消失/错页、会话错误、原子写失败、索引写失败、历史结果保全和互斥 |
| 发布策略 / 持久化单测 | 7 / 5 项通过；Web tmpfiles 用户依赖回归先失败后修复 |
| 最终构建 | 74 个 HTML，54 个正式阅读页，303 文件，28,888,414 字节 |
| CSP 浏览器 | 9 页覆盖全部 12 种脚本 hash，篡改脚本被阻止 |
| 全 DOM parity | 54 页，0 差异 |
| 完整离线矩阵第 1 轮 | 296 JS + 148 no-JS，0 外部请求，380.970 秒 |
| 完整离线矩阵第 2 轮 | 296 JS + 148 no-JS，0 外部请求，381.975 秒 |
| 全仓检查 | 16 项命令通过，`tmp/project-check/20261017T220647-f7_gzbwy/report.json` |
| 最终 quick | 13 项命令通过，`tmp/project-check/20261017T222324-ohbbo6fx/report.json` |

两次正常完整矩阵之间另有一次预期失败注入，报告单独保留。两轮分别保留 488 张截图；Weiss 哈希章 @1440 均通过首末习题深链。另实际目视核对了离线/公网首屏、数学排版和手机答案截图。当前正式内容未改动；I032 的摘录、MathML、短例与前四章范围继续保持其原有边界。

## 生产应用与验收

使用既有 SSH 密钥验证新连接后，应用 root-owned 只读 release、固定 root helper、sudoers 和 deploy unit；发布身份不能直接写正文或 chmod。Web tmpfiles 已与构建主机模板分离，Web 主机无需额外构建用户。原配置及属主模式清单保存在服务器 root 私有恢复目录，原版 `20261017T174039` 与首次迁移恢复点保留。

22:22（北京时间）通过真实 `reading-notes-deploy.service` 发布 `20261017T210828`，Result=success / ExecMainStatus=0，回执进入 done。之后实际回滚旧版，再恢复新版，两个阶段都完成 Nginx test/reload，并以 HTTPS 校验测度第一章的不同版本哈希。最终 `current -> releases/20261017T210828`，303 文件 SHA256 和 root 只读权限全部通过，无未完成事务；deploy timer 保持 disabled。

| 生产验证 | 本次结果 |
|---|---|
| 公网 HTTPS | 298 个直接响应文件逐一核对 SHA256/MIME/CSP；其余 5 个 HTML 为旧入口重定向文件 |
| 入口兼容 | 15 个旧入口的 GET/HEAD、查询参数保留和 POST 拒绝通过 |
| PDF | 两份授权 PDF 均返回 206，Range 字节与发布包一致 |
| 实际浏览 | 8 个代表页面 × 1440/390，共 16 视图、22 截图；五书首章、哈希章、书架和随机过程代码页，CSP/runtime 无错误，深链与手机目录通过 |
| SSH | 密钥新会话成功；PasswordAuthentication=no，AuthenticationMethods=publickey，root 仅公钥 |
| FTP / UFW | pure-ftpd 已 stop/mask，无 21/3306 监听；IPv4/IPv6 仅放行 22/80/443 |
| fail2ban | 已安装并启用，sshd jail 使用 systemd backend，maxretry=5，findtime=10m，bantime=1h |

发布包的构建源仍是 I032 干净提交 `4acee863d6e52b5f7de7f99e651d66353a1d8988`；本轮修改验收及运维设施，最终 dist 的 303 个文件与该包全部相同。归档 SHA256 为 `7f6ec99ead09b35f0c2cf205812005b7efeb0e6a202d24c3d53b4c9d59cd2217`。本轮仓库提交与站点载荷的来源分别记录，不修改旧包元数据。

## 后续操作与证据边界

现有证书有效至 2027-01-09。实际 Certbot webroot 测试由 CA 返回 HTTP 403，现存配置仍为手工 DNS-01；自动续期尚未通过。按用户后续安排，提供了 [阿里云 DNS 自动续期步骤](../deploy/DNS-RENEWAL.md)，包含限定域的 RAM 策略、测试 CA、正式签发、独立证书路径、Nginx 切换及回滚。没有安装新 ACME 客户端，也没有配置或读取 DNS API 凭据。root 密码轮换由用户在自己的终端执行 `passwd root`。

原始失败、故障注入、成功复跑、服务器操作与公网证据保存在忽略目录 `tmp/browser-stability/`，哈希与独立快照索引见 [机器可读证据](browser-stability-evidence.json)，测试设计及过程中的实际失败见 [T033](../test/T033-browser-stability.md)。I032 历史成功快照的 SHA256 仍为 `1ec6d5fe6b18738cf15fd73abd9c86cd990d6bd202f5f9c0d5c80ba0f41d9eed`，未被本轮复跑覆盖。
