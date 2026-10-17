# Ubuntu 静态发布

构建主机使用 Node 24.21.0、pnpm 11.21.0、Python 3.10+、C/Make/Poppler；Web 主机只运行 Nginx。两台主机可以分开：Web 主机安装 Python、rsync 和 util-linux 仅用于一次性发布脚本，不启动 Node、Python HTTP 或数据库服务。下面是安装模板；本次只在 macOS 的临时目录执行了发布及 Nginx 验收，尚未在 Ubuntu/systemd 或生产证书上执行。

## 安装、目录与权限

Web 主机管理员安装 `nginx python3 rsync util-linux openssl certbot`，创建 `reading-notes` 系统组及同名无登录系统用户。独立构建主机另建 `reading-notes-build` 用户，加入 `reading-notes` 组；安装锁定 Node/pnpm 和 `clang make poppler-utils`，检出已审核提交至 `/opt/reading-notes-builder`。先执行 `python3 tools/project.py doctor`，不要用不匹配的 Node/pnpm 继续构建。

将 `deploy/scripts/`、`deploy/public_policy.py`、`deploy/publish-allowlist.json`、`deploy/nginx/` 与 `tools/release_support.py` 按仓库相对结构安装到 `/usr/local/lib/reading-notes/`，由 root 拥有、目录 0755、普通文件 0644、脚本 0755。此安装目录不可由发布用户修改。将 `reading-notes-nginx` 安装到 `/usr/local/sbin/`，root:root 0755。将 `reading-notes.sudoers` 用 `visudo -cf` 校验后安装到 `/etc/sudoers.d/reading-notes`，root:root 0440；它只允许固定的 test/reload 两个动作。

`reading-notes.tmpfiles.conf` 安装到 `/etc/tmpfiles.d/` 并执行 `systemd-tmpfiles --create`。Web 主机若没有构建用户，删去最后一条构建锁目录声明后安装；其余目录必须按文件中的属主和权限创建。运行目录为：

```text
/srv/reading-notes/releases/<release-id>/site/
/srv/reading-notes/releases/<release-id>/SHA256SUMS
/srv/reading-notes/releases/<release-id>/release.json
/srv/reading-notes/current -> releases/<release-id>
/var/spool/reading-notes/{ready,done}/
```

发布脚本把新目录改为目录 0555、文件 0444；拒绝重用版本号。`current` 与 release 位于同一文件系统。没有自动删除 release 或旧证据的任务，回滚版本由运维明确保留。

## 构建、证书与首次上线

在构建主机执行：

```sh
pnpm install --frozen-lockfile
python3 tools/project.py check
python3 tools/project.py build
python3 tools/project.py verify-release --release-id YYYYMMDDTHHMMSS
```

`deploy/portal-releases/<id>/` 是传输单元，包含确定性的 `site.tar.gz`、逐文件 `SHA256SUMS`、`release.json` 和 Nginx 模板。SHA256SUMS 相对 `site/`，位于 web root 外。相同输入两次构建的清单和 tar.gz 均应相同；版本号与本地计时不进入网页。

在部署前完成域名及证书。HTTP vhost 先只安装 `notes.conf.template` 的 80 端口部分，创建 `/var/lib/letsencrypt`，使用 `certbot certonly --webroot -w /var/lib/letsencrypt -d notes.zzzping.top` 取得证书，再安装完整 vhost。证书私钥留在 `/etc/letsencrypt`，不要复制进仓库或 release。

管理员审查本版 `nginx-static.inc` 后将其安装到 `/etc/nginx/snippets/reading-notes-static.inc`，root:root 0644；完整 vhost 引用这份固定配置。发布用户不能写 Nginx 配置。脚本在切换前检查新版本所有脚本 CSP 哈希都已登记；未来新增脚本时必须先按变更控制审查并更新这份 snippet。发布目录中的同名文件仅用于审核和回退参考，不直接作为 root Nginx 的 include。

`disable_symlinks on from=$document_root` 允许管理员指定的 `current` 入口，但拒绝站点内部的符号链接。发布器本身同时拒绝归档内链接、路径穿越、白名单外文件和原始审阅数据。静态模板开启 UTF-8、gzip、ETag、CSP、HSTS、PDF Range、正确 MIME，关闭目录枚举，仅接受 GET/HEAD。HSTS 只在 HTTPS vhost 使用。

将审核后的包复制到 Web 主机私有队列，使用发布用户运行：

```sh
sudo -u reading-notes /usr/local/lib/reading-notes/deploy/scripts/publish.sh \
  --release-dir /var/spool/reading-notes/ready/YYYYMMDDTHHMMSS
```

脚本使用 `flock` 排他锁；在临时目录解包并检查 SHA256SUMS、元数据和精确 allowlist，用 rsync 写入新的 release，先创建临时 symlink，再用 POSIX rename 原子替换 `current`，随后执行受限的 `nginx -t` 和 `systemctl reload nginx`。任何正常异常或 TERM/INT 导致恢复原链接并重载旧配置；失败候选保留在 current 以外供检查。首次部署失败时移除新 current。

## 服务、回滚与验收

`reading-notes-build.service/.timer` 仅安装在构建主机；固定执行已检出的提交，不自动拉取远端。该主机需要 `/opt/node/bin` 中匹配版本的 node/pnpm，以及已经具备来源 PDF 的受控工作目录。构建任务完成完整 Python 检查后把包原子移入 ready 队列。Web 主机只安装 `reading-notes-deploy.service/.timer`；队列可以通过已有受控传输流程从构建主机送达。两个 timer 默认不因复制文件而启用；安装验证完成后管理员执行 `systemctl daemon-reload` 及相应 `enable --now`。日志见 `journalctl -u reading-notes-build -u reading-notes-deploy`。

Nginx 日志可沿用发行版 logrotate；若安装提供的 `reading-notes.logrotate`，先从发行版通配规则排除同名日志，避免重复轮转。tmpfiles 只创建目录，不清理版本。

回滚仍需持锁、验证旧版哈希，并实际 test/reload：

```sh
sudo -u reading-notes /usr/local/lib/reading-notes/deploy/scripts/publish.sh --rollback YYYYMMDDTHHMMSS
```

因断电或 SIGKILL 留下 `.publish-transaction.json` 时，新发布会拒绝继续；检查日志后执行 `publish.sh --recover` 恢复日志记载的原版本。若旧版服务重载也失败，日志和事务记录保留，先排查配置再恢复。显式 rollback 只要求目标旧版本验证通过，因此当前版本的文件损坏不会阻断恢复。队列进程在成功发布后、移动回执前中断时，下次会校验已生效的同版身份后完成回执，不重复覆盖。构建被强杀时同理检查 `tmp/reading-notes-migration/build.lock/owner.json` 的进程是否已退出，然后只移除这个失效锁目录，不删除构建基线。

本地演练使用 `tools/test_static_publish.py --release-dir deploy/portal-releases/<id>`，真实执行 SHA、rsync、锁、原子 rename、临时 Nginx HTTPS/HTTP 和故障回滚。`publish.sh --dry-run --root <临时目录>` 也实际写入临时 release，但没有 service hook 时明确跳过服务动作，不代表生产验收。完整线上验收用 `deploy/verify_portal.py --release-dir <本地包> --origin https://notes.zzzping.top --output <私有报告>`，并实际检查桌面/手机页面、深链及公式。此任务没有执行远端发布、DNS、证书安装或生产回滚。
