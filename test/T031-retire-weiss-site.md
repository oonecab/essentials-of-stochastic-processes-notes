# T031：Weiss 独立站点清理验收

关联 [I031](../issues/I031-retire-weiss-site.md)。

- 删除目标与预检 inode/device、真实路径一致，无嵌套挂载；启用链接只解除链接，目录删除不追随符号链接。
- 只有旧 vhost 引用旧证书；证书 SAN 仅旧域名，自动任务无额外 Weiss 引用。
- nginx -t 和平滑重载成功，旧域名不再出现在有效 Nginx 配置中；旧配置、站点目录、部署目录、日志及 Certbot 旧域名条目均消失。
- Reading Notes 当前版本 306 个文件、主站旧布局回滚版本 303 个文件、com 的 20 个文件和 SICP 的 208 个文件哈希保持；保留 vhost 与证书哈希保持。
- 主站 Weiss 18 个发布文件保持，正式笔记页通过公开 HTTPS 状态及内容哈希验证；主站首页、其他书籍入口、SICP 与 com 的既有响应保持。
- 文件系统净变化单独记录，避免将动态日志变化等同于目标目录精确大小。
- 登记快速检查、差异与密钥扫描通过；Git 本地、跟踪和远端提交一致，工作区干净。

原始证据位于 tmp/weiss-retirement-20261017/。本次不改变页面内容或样式，以现有阅读验收为背景，新增验证只覆盖服务器退役和内容保持。

## 执行结果

- `preflight.json`、`references.json`：旧站与主站目录独立，证书只有旧域名 SAN；仅旧 vhost 引用专属证书，未发现额外自动任务引用。路径、挂载与受保护文件哈希预检通过。
- `removal.json`：解除启用链接后 nginx -t、systemctl reload nginx、源站复查均退出 0；旧日志句柄已释放后删除独立站点及配置，通过 Certbot 清除专属证书，最终 nginx -t 退出 0。
- `postflight.json`：14 个精确目标路径均消失，有效 Nginx 配置不再包含旧域名；保留的 30 项 Nginx 配置、31 项证书文件/链接内容哈希保持，Nginx active。
- 主站当前版本、主站旧布局回滚版本、com 与 SICP 合计 837 个文件哈希及 current 保持。主站 Weiss 的 18 个发布文件包含在该核对中。
- `public-https.json`：使用公开域名、证书和主机名验证，20 个地址 HTTP 200 且与清理前哈希一致：Weiss 14 个 HTML 阅读页及 1 个 C 下载、主站首页、其他四书入口。源站 SICP 为 200，com 保持既有 401 鉴权。
- 根分区可用空间净增 7,680,000 字节（7.32 MiB），使用率保持 36%。原始日志和元数据为观测证据，未复制旧站私钥。
- `python3 tools/project.py check --quick` 退出 0，11 项登记检查全部通过；报告为 `tmp/project-check/20261017T195432-t3a_zxg2/report.json`，日志为 `tmp/weiss-retirement-20261017/project-quick.log`。
