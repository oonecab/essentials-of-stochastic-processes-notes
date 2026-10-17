# T033：浏览器稳定性与生产迁移验收

- 节点在 wait 与 evaluate 之间消失时有界重试；真正缺失或页面身份改变必须明确失败，不能默认为通过。重定向和没有习题的辅助页不执行习题深链。
- 失败、初始化异常和进程异常不能覆盖前次成功报告及截图；每轮有唯一目录，JSON 原子写入，最终入口只在驱动退出成功后更新。
- 仅缓存空间的精确 not-found 错误允许创建一次命名空间；显式环境变量校验、用户控制/权限/未知错误不回退；同一会话的并发运行拒绝。
- `pnpm test`、`pnpm build`、`pnpm check:parity`、两次完整 `pnpm check:offline`、`python3 tools/project.py check`，每项记录独立路径和结果。
- 生产：两条独立密钥会话、root-owned 只读 release、受限 helper、unit、回滚/再发布、完整载荷哈希和 HTTPS 语义导航；SSH/FTP/UFW/fail2ban/续期按实际执行记录。

关联 [I033](../issues/I033-browser-stability.md)。执行结果如下；I032 历史证据保留。

## 本地执行记录

浏览器回归先因尚缺 runtime 模块失败；另一个报告索引写失败的回归在原提交顺序下确实失败，修正为最后更新成功入口后通过。当前 `pnpm test` 18 项通过，包含真实回调在模拟 DOM 中的消失/错页变异、原子替换失败、缓存与显式会话、并发互斥、报告及截图保全。Web tmpfiles 的账号回归先失败，拆分构建主机模板后发布策略 7 项通过。

`pnpm build` 通过：74 个 HTML、303 个文件、CSP 9 页覆盖 12 种脚本 hash，篡改脚本被阻止。`pnpm check:parity` 为 54 页 / 0 差异。303 个 dist 文件逐个与 release `20261017T210828` 的路径、字节和 SHA256 相符，压缩包哈希也匹配。全仓检查为 `tmp/project-check/20261017T220647-f7_gzbwy/report.json`。

第一轮完整矩阵为 `browser/all/runs/2026-10-17T14-06-51-062Z-e78d8034/`（前缀 `tmp/reading-notes-migration/`），通过 296 JS / 148 no-JS、0 外部请求。之后用明确失效的空间进行真实失败注入，驱动退出 1，最新尝试为失败，但成功报告字节及 488 张截图的 SHA256 全部保持。证据 `tmp/browser-stability/failure-preservation.json`；原失败日志另存，不把故障注入当成验收成功。第二轮运行时启动 Weiss 检查被共享锁拒绝，未导航当前页面。

实际目视读回了 Weiss 哈希章 1440 首屏、390 最后一题答案及测度第一章 390 首屏；目录、正文和公式可读。本轮修改的是验收驱动，未重新声称完成全书数学审阅。

## 运维执行中的问题与修正

首个配置备份命令把同名 sudoers 文件与安装目录复制到同一扁平目录，因名称冲突停止，尚未改动服务；随后改用保留完整路径的私有备份。Web tmpfiles 引用缺失构建用户导致迁移中止；拆分模板后续行通过。pure-ftpd 的 disable 操作只完成开机项处理，复查仍有进程，后续明确 stop 并 mask，实测 inactive 且无 21 监听。以上失败日志与修正日志均保留在 `tmp/browser-stability/`。

root-owned 只读版本树、固定 helper、sudoers、unit、原版 SHA256 和 Nginx test/reload 已实测；发布身份写文件及 chmod 都被拒绝。SSH 密码认证关闭后密钥新会话成功，UFW 只保留 22/80/443，fail2ban sshd jail 正常。未执行 root 密码轮换。自动 HTTP 证书续期的真实 CA 验证失败为公网 403，仍保留现有有效证书；用户要求后续配置说明，已提供 [DNS 续期交接](../deploy/DNS-RENEWAL.md)，不标记续期完成。

## 最终复跑与生产结果

第二轮 `2026-10-17T14-14-20-731Z-59dd0586` 再次通过 296/148，488 张截图哈希完整；最终构建和 CSP 在报告提交顺序修正后再次通过。13 项 quick 检查通过：`tmp/project-check/20261017T222324-ohbbo6fx/report.json`。

真实 deploy unit 发布成功，回滚 174039 后恢复 210828，两版本测度第一章 HTTPS 哈希不同且各自匹配。公网验证 298 直接响应、15 旧入口和两份 PDF Range 通过；代表页面 16 个真实浏览视图、22 张截图通过，另目视读回书架、测度首章桌面与 Weiss 哈希章手机答案。最终 303 个服务器文件全部匹配且 root 只读。完整结果与明确待办见 [I033 报告](../docs/browser-stability-report.md)。
