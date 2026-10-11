# 静态站点打包与服务器部署

本项目的部署单位是完整站点包。保留目录关系：

```text
index.html                         # 进入全书地图
notes/                             # 序言、六章、附录与复核记录
code/                              # 六章源文件、运行说明、Makefile
assets/essentials-of-stochastic-processes.pdf
```

网页中的源书链接统一使用 `../assets/essentials-of-stochastic-processes.pdf#page=N`，其中 N 是 PDF 实际页序。该相对路径在本地离线打开和 HTTP/HTTPS 中都按当前页面的位置解析，站点无需固定域名；完整目录也可以挂载在某个子路径下。

## 本地构建

在项目根目录执行：

```sh
python3 tools/sync_code.py
python3 tools/check_notes.py
python3 deploy/build_release.py
```

构建需要 Python 3、clang（完整程序检查）、Poppler/pdftotext（原书编号页码检查）和 Node.js（内嵌脚本语法检查），均为本地工具。网页服务器只需提供静态文件。发布程序会检查十四份源码与网页的一致性、九页结构、全部本地链接、PDF 哈希和内嵌脚本，随后输出独立版本目录 `deploy/releases/YYYYMMDDTHHMMSS/`：

- `site.tar.gz`：正式站点文件。
- `SHA256SUMS`：解包后逐文件核对。
- `release.json`、`archive.sha256`：版本清单和压缩包哈希。
- `nginx-static.inc`：供 HTTPS 虚拟主机包含的静态路由配置，附本次脚本 CSP 哈希。

可以用 `--web-root /var/www/你的站点/current` 指定生成的 Nginx 文档根目录。发布程序只在本地打包。

## 上传与生效

沿用独立 release 加 `current` 符号链接的方式：先将包上传到新版本目录，解包，运行 `sha256sum -c SHA256SUMS`，验证 Nginx 配置与页面响应，再原子切换 `current`。旧版本目录作为回滚点保留。`SHA256SUMS` 和部署元数据应放在站点文档根目录之外。

Nginx 的 `root` 必须指向包含 `index.html`、`notes`、`code` 和 `assets` 的那一级目录。HTTPS 虚拟主机内使用生成的 `nginx-static.inc`；域名、证书、端口和账号认证按实际部署配置。更新内嵌脚本时同步更新对应 CSP 哈希，并执行 `nginx -t` 后 reload。

示例中的 C/Python 是供读者下载后在自己电脑上运行的程序。Nginx 将 `.c`／`.py` 返回为 `text/plain`，网页提供下载入口；`.pdf` 返回为 `application/pdf`，保留浏览器内阅读和页码定位。

## PDF 页码定位与验证

`#page=N` 由浏览器的 PDF 阅读器解释，Nginx 收到的请求只包含 PDF 路径。支持这一参数的阅读器会打开对应页；部分手机浏览器会下载或交给外部应用，此时需要按笔记标出的“PDF 第 N 页”定位。如果后续需要统一阅读器，可增加自托管 PDF.js；它明确支持 [page 参数](https://github.com/mozilla/pdf.js/wiki/Viewer-options)。

上线后分别验证首页、九个页面、十四个代码下载和 PDF。PDF 要检查正确的 MIME 类型、文件哈希、字节范围请求（206）以及浏览器中打开链接后的页码。若启用登录，PDF 和源码路径也应处在同一个服务端认证范围内。

Nginx 官方说明：[MIME 类型映射](https://nginx.org/en/docs/http/ngx_http_core_module.html#types)、[静态文件路径检查](https://nginx.org/en/docs/http/ngx_http_core_module.html#try_files)、[响应头与继承规则](https://nginx.org/en/docs/http/ngx_http_headers_module.html#add_header)。

构建同时扫描外部 CSS 导入、CSS URL、base、异常 meta-refresh、独立资源和元数据中的本机路径；SVG 的 `url(#arrow)` 是页面内引用。仅允许生成的首页跳转到全书地图。gzip 的时间和文件名字段、tar 的排序／权限／用户／时间均固定，相同站点字节在同一构建环境下生成相同压缩包。临时版本目录全部完成后以一次 rename 发布，避免暴露半成品。

本次修订的内容、源码与浏览器证据见 notes/audit_fix_review.json；新版本HTTP、源码下载、PDF Range和两次打包一致性记录保存在 deploy/reports/，独立于包内文件，避免自引用哈希。历史版本继续保留为检查点。

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

书的内容仍在各自项目维护。统一打包在两套原有结构检查通过后执行；发布时在每个书页已有页头导航中插入一个相对路径的“笔记首页”链接，其他页面字节、公式、程序和原有链接保持一致。两本书都保留 `notes/` 这一层，Weiss 的 `../c/ch8.c` 因而仍指向本书的源码目录。

在本项目运行：

```sh
python3 deploy/build_portal.py --weiss-root /path/to/WEISS_2ED_C
```

输出位于 `deploy/portal-releases/<release-id>/`，含统一站点包、逐文件 SHA-256、版本清单、静态路由 include 与完整 Nginx 域名配置。构建核对全部本地资源与 HTML 锚点，检查内嵌脚本并生成其 CSP 哈希。`release.json` 与 `SHA256SUMS` 留在站点目录之外；页面引用的复核 JSON 随原有笔记发布。

服务器约定：网页位于 `/var/www/notes.zzzping.top/releases/<release-id>/`，`current` 指向当前版本；发布材料位于 `/var/lib/notes-deploy/<release-id>/`。域名配置为 `/etc/nginx/sites-available/notes.zzzping.top`，其中 include 必须对应本次版本的 `nginx-static.inc`。

更新时上传新版本，先校验压缩包和解包后的全部文件，保存当前 `current` 目标与 Nginx 配置，再原子切换 `current`、安装本次配置，运行 `nginx -t` 后 reload。若配置检查失败，立即恢复原配置及原链接。回滚同样要同时恢复版本链接和该版本的配置，因为内嵌脚本改变时 CSP 哈希也会改变。原 Weiss 域名的发布目录独立于这一站点。

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
