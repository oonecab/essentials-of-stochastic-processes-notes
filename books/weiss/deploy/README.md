> 此目录保留原独立 Weiss 站点的工具与历史说明。Reading Notes 的日常发布以 [统一部署说明](../../../deploy/README.md) 为准；下面的证书与线上状态属于原部署记录，执行前必须读取实际环境。

# Weiss 静态站点部署

站点入口为 <https://weiss.zzzping.top/>，使用服务器 `39.106.147.77` 上的原生 Nginx，按站点所有者的选择公开访问。首页由 Nginx 的 `index book_overview.html` 指令提供，页面内容以现有 `notes/` HTML 为准。

## 发布内容与目录

发布包包含全书总览、十二章 HTML，以及页面直接引用的三个辅助文件：`notes/README.md`、`notes/tools/check_notes.py`、`c/ch8.c`。辅助文件作为静态文件返回；Python、C 程序在读者本地执行。

- 网页目录：`/var/www/weiss.zzzping.top/releases/<release-id>`。
- 当前版本链接：`/var/www/weiss.zzzping.top/current`。
- 上传包、文件清单、配置与验证记录：`/var/lib/weiss-deploy/<release-id>`，与网页目录分开保存。
- Nginx 配置：`/etc/nginx/sites-available/weiss.zzzping.top`。
- 证书：`/etc/letsencrypt/live/weiss.zzzping.top/`。
- 专用日志：`/var/log/nginx/weiss.zzzping.top.access.log` 和同目录下的 `.error.log`。

首次上线版本为 `20261004T223552`。详细结果见 [部署报告](reports/20261004T223552/部署报告.md)。

## 更新页面

在本地执行：

```bash
cd books/weiss
python3 deploy/build_release.py
```

脚本检查全部 HTML 的结构和链接、内嵌脚本语法及资源依赖，然后生成 `deploy/releases/<release-id>/` 下的压缩包、文件 SHA-256 清单、发布元数据和 Nginx 配置。它会重新计算内嵌脚本的 CSP 哈希，并同步更新 `deploy/nginx-weiss.zzzping.top.conf`。网页仍来自原来的正式 HTML。

上传时使用 SSH 交互认证或用户自行配置的 SSH 密钥。账号密码由登录工具处理，部署文件不保存认证秘密。发布顺序为：

1. 在服务器建立新的 `/var/lib/weiss-deploy/<release-id>`，上传 `site.tar.gz`、`archive.sha256`、`SHA256SUMS`、`release.json`、该版本 Nginx 配置和 `verify_http.py`。
2. 在元数据目录执行 `sha256sum -c archive.sha256`，核对归档成员与 `release.json` 一致，将它解压到新的 `releases/<release-id>`，在新目录执行 `sha256sum -c /var/lib/weiss-deploy/<release-id>/SHA256SUMS`。目录权限为 `0755`，文件为 `0644`。
3. 保存当前链接目标和 Nginx 配置，安装对应的新配置并执行 `nginx -t`。测试通过后，以临时符号链接加 `mv -Tf` 切换 `current`，再执行 `systemctl reload nginx`，使新 CSP 哈希同时生效。
4. 等待 HTTPS 返回新内容，再在服务器执行下面的验证命令，核对所有响应体的指纹。通过后保留旧版本作为回滚目标。

```bash
python3 /var/lib/weiss-deploy/<release-id>/verify_http.py \
  /var/lib/weiss-deploy/<release-id>/release.json \
  /var/lib/weiss-deploy/<release-id>/origin-http.json \
  --address 127.0.0.1
```

在真实浏览器中再检查首页、章节导航和本次变更的交互。源站指纹校验与公网浏览器验证的结果分别记录。

## HTTPS 与续期

本次证书的有效期至 **2027 年 1 月 2 日 21:44:12（北京时间）**。公网 HTTP 验证请求被阿里云的备案拦截页返回 `403`，因此证书使用 `dns-01` 手动验证签发。

当前证书的 `authenticator = manual`，没有配置 DNS API 认证钩子，**不能依赖 `certbot.timer` 自动续期**。到期前，在服务器交互执行：

```bash
bash /var/lib/weiss-deploy/20261004T223552/renew-certificate.sh
```

Certbot 会提供新的 TXT 值。在阿里云 `zzzping.top` 的解析设置中，更新或新增 `_acme-challenge.weiss` 的 TXT 记录，确认新值已经传播后再按回车。每次续期都会生成新的验证值。续期脚本设置了部署钩子，证书签发成功后先检查 Nginx 配置，再 reload 使新证书生效。

本地也保存了相同的 [续期脚本](renew-certificate.sh)。如要实现全自动 DNS 续期，需要另行配置限定 DNS 权限的 API 凭据和认证钩子。

源站 HTTP 已配置 `301` 到 HTTPS；本次实测的公网 HTTP 仍被阿里云在到达源站前返回备案 `403`。对外分享使用完整的 `https://weiss.zzzping.top/` 地址。HTTPS 公网访问和内容指纹已通过浏览器验证。

## 回滚

这是首次部署，没有更早的 Weiss 线上版本。后续更新时可以将 `current` 原子切回保留的发布目录，同时恢复该版本的 Nginx 配置并执行 `nginx -t`、reload；配置中的 CSP 哈希必须与该版本的脚本一致。

例如，在后续版本上线后恢复本次版本：

```bash
WEISS_TARGET=20261004T223552
cp "/var/lib/weiss-deploy/$WEISS_TARGET/nginx-weiss.zzzping.top.conf" \
   /etc/nginx/sites-available/weiss.zzzping.top
nginx -t
ln -s "releases/$WEISS_TARGET" "/var/www/weiss.zzzping.top/current.rollback-$WEISS_TARGET"
mv -Tf "/var/www/weiss.zzzping.top/current.rollback-$WEISS_TARGET" \
       /var/www/weiss.zzzping.top/current
systemctl reload nginx
```

执行前确认目标目录和对应元数据都存在，并记录当前版本；恢复后再验证 HTTPS 内容。
