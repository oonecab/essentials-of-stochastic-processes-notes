# 合并前统一站点的部署记录

归档日期：2026-10-12。本文件保存迁移前的部署说明和历史验收叙述；其中外部 Weiss 路径、旧构建命令及状态仅代表当时记录。当前操作以 [统一部署说明](../../deploy/README.md) 为准，生产状态需按实际环境复核。

## 两本书的统一入口：notes.zzzping.top

`portal/` 保存读书笔记首页；两本书以独立子目录发布：

```text
index.html、styles.css、favicon.svg    # 书架首页
stochastic/index.html                 # 离线入口；HTTPS 由服务器直接重定向到全书地图
stochastic/notes/                     # 九个笔记页面及页面引用的复核记录
stochastic/code/                      # 原有章节源码、说明与 Makefile
stochastic/assets/                    # 原书 PDF
weiss/index.html                      # 离线入口；HTTPS 由服务器直接重定向到全书地图
weiss/notes/                          # 总览、十二章与页面引用的辅助文件
weiss/c/ch8.c                         # 第八章引用的共享实现
```

维护首页时编辑 `portal/index.html` 和 `portal/styles.css`。首页书名和阅读按钮都直接指向各书的 `notes/book_overview.html`。Nginx 对 `/stochastic`、`/stochastic/`、`/stochastic/index.html` 及对应的 Weiss 三个入口返回301，目标是本书全书地图并保留查询参数；浏览器直接加载地图。包内的两个 `index.html` 保留为离线入口。

书的内容仍在各自项目维护。统一打包在两套原有结构检查通过后执行；发布时为每个阅读页加入顶部常驻导航、页头和页尾的“笔记首页”链接，使用相对路径返回书架。共享样式在 `portal/reader.css`，发布转换及资料网页在 `deploy/reader_views.py`。公式与 C/Python 实现保持原有内容。两本书都保留 `notes/` 这一层，Weiss 的 `../c/ch8.c` 因而仍指向本书的源码目录。

网页里的代码运行说明、版本页码记录、逐章复核记录和验证结果分别打开对应的 HTML 资料页；原始 Markdown、JSON 和源码作为明确的下载入口保留。代码资料页提供七组示例、六章运行说明和包含全部源文件及 Makefile 的 ZIP。构建检查所有 HTML 页面引用和锚点，将链接逐项记录到私有的 `navigation.json`；文献链接的可用原论文来源替换记录在 `release.json`。

在本项目运行：

```sh
python3 deploy/build_portal.py --weiss-root /path/to/WEISS_2ED_C
```

输出位于 `deploy/portal-releases/<release-id>/`，含统一站点包、逐文件 SHA-256、版本清单、静态路由 include 与完整 Nginx 域名配置。构建核对全部本地资源与 HTML 锚点，检查内嵌脚本并生成其 CSP 哈希。`release.json` 与 `SHA256SUMS` 留在站点目录之外；页面引用的复核 JSON 随原有笔记发布。

服务器约定：网页位于 `/var/www/notes.zzzping.top/releases/<release-id>/`，`current` 指向当前版本；发布材料位于 `/var/lib/notes-deploy/<release-id>/`。域名配置为 `/etc/nginx/sites-available/notes.zzzping.top`，其中 include 必须对应本次版本的 `nginx-static.inc`。

更新时上传新版本，先校验压缩包和解包后的全部文件，保存当前 `current` 目标与 Nginx 配置，再原子切换 `current`、安装本次配置，运行 `nginx -t` 后 reload。重载命令返回后，用新建的 HTTPS 连接轮询响应头，确认 CSP 已包含本版全部脚本哈希，再运行完整响应校验；Nginx 旧工作进程退出与新进程接管之间可能有短暂时差。若配置或响应检查失败，立即恢复原配置及原链接。回滚同样要同时恢复版本链接和该版本的配置，因为内嵌脚本改变时 CSP 哈希也会改变。原 Weiss 域名的发布目录独立于这一站点。

可用同一个验证器检查本地预览或服务器上的 HTTPS 响应。以下命令在服务器执行，保留域名的 TLS SNI 和证书主机名校验，同时直连源站：

```sh
python3 /var/lib/notes-deploy/<release-id>/verify_portal.py \
  --release-dir /var/lib/notes-deploy/<release-id> \
  --origin https://notes.zzzping.top --connect-ip 127.0.0.1 \
  --output /var/lib/notes-deploy/<release-id>/origin-https.json
```

验证器逐一比较直接提供的文件响应内容、MIME、缓存和 CSP 头，并核对首页、六个书目入口的301及查询参数、HEAD 与 POST 行为、PDF 的 `206` 字节范围读取及静态路由。两个离线入口文件的字节随全部文件一起在服务器校验，HTTPS 请求由入口重定向覆盖。公网浏览器的显示与点击验收另存于 `deploy/reports/<release-id>/`，与源站验证分别记录。

证书存放在 `/etc/letsencrypt/live/notes.zzzping.top/`。当前公网 HTTP 的证书验证请求被阿里云备案页面拦截，首次申请使用 Certbot 手动 DNS-01：为 `zzzping.top` 下的 `_acme-challenge.notes` 增加指定 TXT 值后完成验证。手动 DNS 验证的续期同样需要新 TXT 值；运行 `certbot certonly --manual --preferred-challenges dns --cert-name notes.zzzping.top -d notes.zzzping.top`，续期成功后执行 `nginx -t` 与 `systemctl reload nginx`。检查证书实际到期时间后安排续期。

2026-10-11 首次统一发布版本为 `20261011T230300`。本次证书实际到期时间为 **2027-01-09 22:21:02（北京时间）**，手动 DNS 证书尚未配置自动续期。上线后已通过源站 HTTPS、62 个文件的公网浏览器指纹、44 次本地书页布局和10次公网代表页面布局检查；公网点击验证了两本书的进入与返回、手机目录、习题和代码展开，原书 PDF 链接在桌面浏览器实际定位到第10页。原三个站点的配置哈希、发布目录和首页状态与上线前一致。证据保存在 `deploy/reports/20261011T230300/`。

同日发布 `20261011T233659` 修复首页进入笔记时显示“进入全书地图”中间页的问题：首页两个按钮直接连到地图，六个书目入口由 Nginx 返回301。62个包内文件已在服务器校验；60个直接提供的文件通过源站 HTTPS 指纹检查，两个离线入口由重定向覆盖。本地与公网浏览器分别通过1440px及390px的首页、两本全书地图共6次布局检查，4次直接进入、4次浏览器后退、4次返回首页，以及2次旧入口的查询参数和章节锚点跳转。相对首次发布，包内只有首页字节改变；原三个站点的配置、发布目录及源站状态与更新前一致。证据保存在 `deploy/reports/20261011T233659/`；服务器的该版本发布材料中保存 `previous-current.txt` 和 `previous-nginx.conf`，可同时恢复上一版本链接与配置。

分享使用完整的 `https://notes.zzzping.top/`。源站 HTTP 返回301，但从本机直连服务器公网IP的 HTTP 请求仍返回阿里云备案拦截页403；浏览器可能直接升级到HTTPS，因此不能据此认定公网HTTP重定向已通过。

2026-10-12 发布 `20261012T010730`：22个阅读页加入顶部常驻导航和页尾首页入口，代码运行说明与三类复核记录生成统一排版的资料网页，并提供全部示例源码 ZIP。手机目录追踪阈值与新增导航偏移同步。34个页面通过1440px与390px的公网显示检查；194个目录项分别在桌面与手机宽度逐项点击并核对高亮。全站2849处内部链接、942个唯一锚点、28个下载目标、源文件与数学公式一致性均有记录。此前完成的完整锚点、下载及返回导航检查保存在 `deploy/reports/20261012T002814/`；归档对比证明最终版仅调整22页的目录追踪阈值，其余发布字节与链接保持一致，最终验证及证据关系见 `deploy/reports/20261012T010730/acceptance.json`。
