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
