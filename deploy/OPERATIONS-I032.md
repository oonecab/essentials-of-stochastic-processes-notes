# I032 运维应用与验收

这是交给用户/运维执行的工作单。Codex 未登录修改本轮生产权限、SSH、防火墙、FTP、fail2ban 或证书续期。I029–I031 保留为历史实机事实；新本地测试包和验证记录不能代替下面的服务器验收。全过程在服务器私有目录保存配置与回滚文件，仓库与报告只记录结果及非秘密哈希。

## SSH、FTP、防火墙与证书

先保留现有 SSH 会话。在自己的终端创建或选用 SSH key，通过 `ssh-copy-id -i <公钥文件.pub> root@39.106.147.77` 安装**公钥**。再开独立会话，强制禁用客户端密码回退确认 key 可用：

```sh
ssh -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no root@39.106.147.77
```

只有该连接成功后，才在服务器执行下列步骤。`passwd root` 由用户交互输入新值，终端录制与命令回显不应记录该输入。

```sh
umask 077
ops_backup="/root/reading-notes-ops-$(date +%Y%m%dT%H%M%S)"
mkdir -p "$ops_backup"
cp -a /etc/ssh /etc/ufw "$ops_backup/"
sshd -T > "$ops_backup/sshd-effective-before.txt"
ufw status numbered > "$ops_backup/ufw-before.txt"
ss -ltnp > "$ops_backup/listeners-before.txt"
passwd root
cat > /etc/ssh/sshd_config.d/00-reading-notes-hardening.conf <<'EOF'
PubkeyAuthentication yes
PermitRootLogin prohibit-password
PasswordAuthentication no
KbdInteractiveAuthentication no
AuthenticationMethods publickey
EOF
sshd -t
sshd -T -C user=root,host=39.106.147.77,addr=<你的实际管理IP> | grep -E 'permitrootlogin|passwordauthentication|kbdinteractiveauthentication|authenticationmethods|pubkeyauthentication'
```

把 `<你的实际管理IP>` 替换为真实连接地址；该占位行需编辑后执行。确认有效设置为 root 仅公钥、密码及交互认证均关闭、authenticationmethods publickey，再 `systemctl reload ssh`，在第三个终端重复 key 连接。OpenSSH 使用先匹配的设置，不能只看新文件推断已生效；如输出不符，先检查已有 Include/Match。失败时留在原会话恢复备份 `/etc/ssh`，`sshd -t` 后 reload。

读取 `systemctl status pure-ftpd`、`ss -ltnp`、`ufw status numbered`，确认 FTP 及旧管理口已无业务使用后：

```sh
systemctl disable --now pure-ftpd
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw status numbered
```

按实际规则编号从大到小执行 `ufw delete <编号>`，删除 20、21、3306、888、29005、39000:40000 的 IPv4/IPv6 规则，以及其他未确认用途的宽规则。若 SSH 实际端口不是 22，先保留该明确管理口；禁止盲目 ufw reset。只保留 22/80/443（及已记录的必要管理口），再次用新会话测试 SSH/HTTPS。需要回滚时用私有备份恢复 `/etc/ufw` 后 `ufw reload`，不要关闭现有会话。

```sh
apt-get update
apt-get install fail2ban
install -m 0644 /dev/stdin /etc/fail2ban/jail.d/reading-notes-sshd.local <<'EOF'
[sshd]
enabled = true
backend = systemd
maxretry = 5
findtime = 10m
bantime = 1h
EOF
fail2ban-client -t
systemctl enable --now fail2ban
fail2ban-client status sshd
ss -ltnp
ufw status verbose
nginx -t
certbot certificates
systemctl list-timers --all | grep certbot
certbot renew --dry-run
```

验收：无 21/3306 监听；规则面符合保留清单；新 key 会话成功，`sshd -T -C ...` 确认密码认证关闭；fail2ban jail 正常。证书续期必须以 dry-run 成功为证，timer 存在本身不够。如果仍使用无 hook 的手工 DNS-01，需要运维按 DNS 服务商配置受限自动化凭据或适用的 webroot 验证，再重跑 dry-run；凭据只放服务器 root 私有配置。

## 发布权限迁移

新模板采用 [ADR-005](../docs/decisions/ADR-005-root-release-installer.md)。先停用 deploy timer 并确认没有构建/发布进程，备份 `/usr/local/lib/reading-notes`、两个 root helper、sudoers、deploy unit、tmpfiles 配置及 `/srv/reading-notes` 的属主/模式清单。保留在线 current 与 `/var/www/notes.zzzping.top` 的首次迁移回滚材料。

把已审核提交的 deploy/scripts、public_policy.py、publish-allowlist.json、deploy/nginx 和 tools/release_support.py 按原相对布局安装为 root 拥有。`reading-notes-publish`、`reading-notes-nginx` 安装至 `/usr/local/sbin/`，root:root 0755。所有辅助 Python 文件也必须安装，包含 durability.py、retention.py。新 sudoers 先 `visudo -cf <待安装文件>`，再以 0440 安装。

在确认目录树无意外符号链接/挂载、当前及回滚 SHA256SUMS 均通过后，把 `/srv/reading-notes`、`releases` 和版本树递归设为 root:root，顶层及 releases 为 0755，版本目录/文件仍为 0555/0444；`.publish.lock` 与事务记录为 root:root 0600。`current` 仅 chown 链接本身。队列的 reading-notes 权限保持。不要改变证书目录权限。

安装仓库中的 deploy unit 与 tmpfiles 文件，`systemctl daemon-reload`；timer 仍保持停用。新 helper 只接受如下固定命令：

```sh
sudo -u reading-notes sudo -n /usr/local/sbin/reading-notes-publish status
sudo -u reading-notes sudo -n /usr/local/sbin/reading-notes-publish publish YYYYMMDDTHHMMSS
sudo -u reading-notes sudo -n /usr/local/sbin/reading-notes-publish rollback YYYYMMDDTHHMMSS
sudo -u reading-notes sudo -n /usr/local/sbin/reading-notes-publish recover
# journal 损坏时，先检查目标版本再显式选择：
sudo -u reading-notes sudo -n /usr/local/sbin/reading-notes-publish recover YYYYMMDDTHHMMSS
sudo -u reading-notes sudo -n /usr/local/sbin/reading-notes-publish cleanup
# 检查上一步精确清单后才执行：
sudo -u reading-notes sudo -n /usr/local/sbin/reading-notes-publish cleanup apply
```

publish 的 ID 必须是 ready 队列中的包名。上线前先由管理员安装审核后的新 CSP snippet，并保留当前及待回滚版本所需 hash 的并集。下面应返回失败，表明发布身份无法写文件或自行 chmod：

```sh
sudo -u reading-notes test -w /srv/reading-notes/current/site/index.html
sudo -u reading-notes chmod u+w /srv/reading-notes/current/site/index.html
```

另外验证 root helper 的 test/reload、真实 systemd deploy unit、回滚、证书续期，以及所有文件清单。发布前默认需要候选展开大小三倍加 512 MiB 余量，inode 需要条目数三倍加 10000；空间失败不切 current。无 journal 时自动清理超过 24 小时的精确临时名前缀；cleanup 默认仅列计划，保留最近三个版本、七天内版本、current、上次成功发布前版和 journal 引用。status 输出可用字节与 inode，供既有监控采集；本轮没有暗中启用新定时任务。

迁移失败时恢复私有备份的 helper、unit、sudoers、目录属主/模式，daemon-reload 后验证旧发布流程。发布包回滚仍使用已验证的旧 release；不要为了验证权限而修改在线正文。最终实机报告记录日期、release ID、SHA256SUMS、current、unit、ss/UFW、证书续期结果，不记录认证内容。
