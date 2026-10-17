# 统一笔记站点的构建与部署

Reading Notes 从 `books/catalog.json` 登记的 stochastic、weiss、csapp、visual-group-theory、measure-probability 子项目读取正式内容，为 `notes.zzzping.top` 构建统一书架。部署单位是完整静态站点包，C/Python 示例供读者下载后在自己的电脑运行。日常发布使用这里的统一入口；各书 `deploy/` 中的工具用于保留原单书发布能力与历史资料。

## 构建与预览

在仓库根目录执行：

```sh
python3 tools/project.py doctor
python3 tools/project.py check
python3 tools/project.py build
```

构建可以指定 `--release-id YYYYMMDDTHHMMSS`；已存在的版本目录拒绝覆盖。它调用已登记书籍的结构检查，校验源码与 HTML 同步及原书身份，再扫描全部发布页面的资源、唯一锚点、内链与内嵌 JavaScript，生成对应 CSP 哈希。完整数值/功能验证是单独的 `check` 门禁，不能仅以构建成功替代。

输出目录为 `deploy/portal-releases/<release-id>/`：

| 文件 | 用途 |
|---|---|
| `site.tar.gz` | 全部正式站点文件；gzip/tar 元数据固定，便于重复构建对比 |
| `archive.sha256` | 归档文件的 SHA-256 |
| `SHA256SUMS` | 解包后逐文件校验 |
| `release.json` | 本版文件身份、来源目录、检查结果、CSP 与路由 |
| `navigation.json` | 本版链接及下载清单 |
| `nginx-static.inc` | 本版静态服务配置与脚本 CSP 哈希 |
| `nginx-notes.zzzping.top.conf` | 统一域名的 Nginx 虚拟主机配置 |

构建在临时目录完成后一次 rename 发布。元数据和校验清单置于网页根目录之外，只有 `site.tar.gz` 的成员进入站点。构建从当前仓库取源，不使用旧的 `--weiss-root` 参数。

```text
index.html、styles.css、reader.css、favicon.svg
stochastic/notes/                 # 九个阅读页面、原始记录及其资料网页
stochastic/code/                  # 源码、运行说明、资料页及 examples.zip
stochastic/assets/                # 正文引用的原书 PDF
weiss/notes/                      # 全书总览、十二章、说明及资料网页
weiss/c/ch8.c                     # 第八章引用的共享源码
csapp/notes/                      # 全书地图、序言、第 1—12 章和来源清单
csapp/code/                       # 按程序索引收录源码、汇编、基准与运行说明
csapp/csapp.pdf                   # 原书；按来源清单启用，保留章节/习题页序链接
visual-group-theory/notes/        # 全书地图、序言、第 1—10 章及来源/习题清单
visual-group-theory/code/         # 十组 C/Python 源码、运行说明及资料网页
measure-probability/notes/        # 全书总览、序言与前言、前四章及来源/习题清单
measure-probability/code/         # 三组 C/Python 源码、运行说明及资料网页
<book>/index.html                # 每本已登记书籍的离线入口
```

注册书籍的三个入口 `/<book>`、`/<book>/`、`/<book>/index.html` 由 Nginx 返回 301 到本书全书地图，并保留查询参数。当前模板包含上述五本书；章节锚点由浏览器保留和解释。CS:APP 来源清单的 `publication.include_source_pdf` 当前为 `true`，构建收录 `/csapp/csapp.pdf`，章首、来源和习题链接保留 `#page=N`，N 为从 1 开始的 PDF 页序。将该字段设为 `false` 时，构建不收录原书并把相应链接转为页码文字。本地接入与线上生效分别验收，记录见 [T011](../test/T011-csapp-pdf-navigation.md)。视觉群论与测度概率的该字段均为 `false`，原 PDF 位于忽略目录，仅作本地对照；构建保留印刷页/PDF 页序文字及来源说明链接，收录笔记、登记源码和元数据。

`portal/` 维护书架与共享阅读样式，`deploy/reader_views.py` 在发布阶段增加首页导航、资料网页和源码 ZIP，不回写正式笔记。原有章节结构、公式与实现保留。可用下面的命令预览已构建版本：

```sh
python3 tools/project.py serve --release-id YYYYMMDDTHHMMSS --port 8000
```

预览仅监听 `127.0.0.1`，提供发布字节和 CSP，不具备 Nginx 的完整 HTTPS/Range 验收语义。完整本地响应检查使用 `verify-release`，需要 Nginx 与 OpenSSL；它建立临时自签名证书，只让本次 Python 验证进程信任，结束后停止临时 Nginx，不改系统配置或证书信任：

```sh
python3 tools/project.py verify-release --release-id YYYYMMDDTHHMMSS
```

## 服务器布局与生效步骤

以下为现有站点的部署约定，执行前核对服务器实际配置、证书、当前版本及恢复点，完成后在发布记录中登记实际结果。

| 位置 | 作用 |
|---|---|
| `/var/www/notes.zzzping.top/releases/<release-id>/` | 不可覆盖的网页版本目录 |
| `/var/www/notes.zzzping.top/current` | 指向生效版本的符号链接 |
| `/var/lib/notes-deploy/<release-id>/` | 包、清单、配置、验证器和验收证据 |
| `/etc/nginx/sites-available/notes.zzzping.top` | 当前域名配置；include 对应本版元数据目录 |
| `/etc/letsencrypt/live/notes.zzzping.top/` | 当前证书与私钥，由服务器管理 |

先完成本地检查并获得本次生产发布授权，再上传；服务器账号、密码与 SSH/DNS 凭据通过现有认证渠道提供，不写入仓库。不要直接编辑当前版本目录。具体操作顺序：

1. 上传整个版本材料和仓库中的 `deploy/verify_portal.py` 到新的元数据目录。确认新网页目录和新元数据目录均不存在或是本次刚创建的目标，记录实际版本 ID。
2. 执行 `sha256sum -c archive.sha256`，核对归档成员与 `release.json` 的清单一致，且成员是安全相对路径和普通文件；解包到新的网页版本目录，在该目录执行 `sha256sum -c /var/lib/notes-deploy/<release-id>/SHA256SUMS`。
3. 保存原 `current` 的实际目标、当前 Nginx 配置与证书身份；记录到本版 `previous-current.txt`、`previous-nginx.conf` 和发布记录中。确认恢复点可读。
4. 安装本版配置并执行 `nginx -t`；通过后原子切换 `current`，再执行 `systemctl reload nginx`。仅在明确授权的服务器目标执行下面的 Linux 命令。

```sh
NOTES_RELEASE=YYYYMMDDTHHMMSS
NOTES_META="/var/lib/notes-deploy/$NOTES_RELEASE"
NOTES_WEB=/var/www/notes.zzzping.top

readlink "$NOTES_WEB/current" > "$NOTES_META/previous-current.txt"
cp /etc/nginx/sites-available/notes.zzzping.top "$NOTES_META/previous-nginx.conf"
cp "$NOTES_META/nginx-notes.zzzping.top.conf" /etc/nginx/sites-available/notes.zzzping.top
nginx -t
# 上一步成功后再执行；临时链接必须不存在。
ln -s "releases/$NOTES_RELEASE" "$NOTES_WEB/current.next-$NOTES_RELEASE"
mv -Tf "$NOTES_WEB/current.next-$NOTES_RELEASE" "$NOTES_WEB/current"
systemctl reload nginx
```

5. 新建 HTTPS 连接，等待响应的 CSP 包含本版全部脚本哈希；Nginx 重载期间旧进程可能短暂继续响应。随后运行逐文件源站验证，失败则停止并恢复原链接及配置。

```sh
python3 /var/lib/notes-deploy/YYYYMMDDTHHMMSS/verify_portal.py \
  --release-dir /var/lib/notes-deploy/YYYYMMDDTHHMMSS \
  --origin https://notes.zzzping.top --connect-ip 127.0.0.1 \
  --output /var/lib/notes-deploy/YYYYMMDDTHHMMSS/origin-https.json
```

6. 在真实公网浏览器中检查书架、全部已登记书籍入口、受影响章节、目录高亮与手机折叠、习题/代码展开、返回首页、资料页、下载与已收录 PDF 的页码定位。源站响应校验与公网显示验收分别记录，完成后保留旧版本作为回滚点。

静态模板设置 `.c/.py/.md` 为 `text/plain`、PDF 为 `application/pdf`，使用 `no-cache`、`nosniff` 与本版 CSP；点路径返回 404，修改方法返回 403。服务器不执行示例源码。保留现有站点的访问控制与安全配置，不因为本地构建而修改其他虚拟主机。

## 回滚、证书与证据

链接与 CSP 必须同时恢复。出现配置校验失败、文件哈希不符、页面脚本被 CSP 拦截、关键路径失效时，恢复本次记录的旧配置和旧 `current` 目标，运行 `nginx -t` 后 reload，再验证恢复版本。

```sh
NOTES_FAILED_RELEASE=YYYYMMDDTHHMMSS
NOTES_FAILED_META="/var/lib/notes-deploy/$NOTES_FAILED_RELEASE"
NOTES_WEB=/var/www/notes.zzzping.top
NOTES_PREVIOUS_TARGET="$(cat "$NOTES_FAILED_META/previous-current.txt")"

# 先核对旧目录、配置和实际目标；以下临时链接必须不存在。
cp "$NOTES_FAILED_META/previous-nginx.conf" /etc/nginx/sites-available/notes.zzzping.top
nginx -t
ln -s "$NOTES_PREVIOUS_TARGET" "$NOTES_WEB/current.rollback-$NOTES_FAILED_RELEASE"
mv -Tf "$NOTES_WEB/current.rollback-$NOTES_FAILED_RELEASE" "$NOTES_WEB/current"
systemctl reload nginx
```

`#page=N` 是浏览器 PDF 阅读器参数，N 为真实 PDF 页序。响应校验器检查 PDF 哈希、MIME 和 `206` 范围内容，实际页码定位仍需浏览器验收；部分手机会下载或使用外部阅读器。

现有部署历史记载使用手动 DNS-01，公网 HTTP 曾被备案页拦截；这不是本次对当前环境的确认。发布前查看 `certbot certificates`、实际 renewal 配置及证书到期时间。若仍使用未配置自动钩子的手动 DNS 验证，续期需要新的 TXT 值，不能仅依赖 `certbot.timer`。续期成功后执行配置检查及 reload。对外分享完整 HTTPS 地址，HTTP 行为需要另行实测。

发布历史和原验收范围见[合并前部署记录](../docs/history/two-book-deployment-before-merge.md)。每次新发布把源版本、归档/文件哈希、审批来源、备份目标、实际命令、响应校验、浏览器证据及回滚结果保存到 `deploy/reports/<release-id>/`；临时日志不纳入 Git。元数据只记录相对源码路径，不写认证秘密或本机用户目录。

技术边界见 [TECH.md](../TECH.md)，发布门禁见 [发布治理](../docs/governance/RELEASE.md)，本次本地验证范围见[迁移记录](../docs/migration-20261012.md)。
