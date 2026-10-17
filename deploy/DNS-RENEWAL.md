# Reading Notes 的 DNS 自动续期交接

本方案尚未在服务器安装。2026-10-17 实查 `zzzping.top` 的 NS 为 `dns15.hichina.com` / `dns16.hichina.com`，对应阿里云解析。现有 `notes.zzzping.top` 证书有效至 2027-01-09，Certbot 配置为手工 DNS-01；实际 webroot dry-run 被 CA 判定公网 HTTP 403，不能依靠现有 timer 自动续期。网站上线与证书迁移分别验收。

建议使用 acme.sh 的 `dns_ali` 插件，由 DNS API 自动添加并删除 `_acme-challenge.notes.zzzping.top` 的 TXT 记录。此方案不要求公网 HTTP 验证通畅。插件目前调用三个 API：DescribeDomainRecords、AddDomainRecord、DeleteDomainRecord，并将认证值保存在服务器私有 account.conf 中。[插件源码](https://github.com/acmesh-official/acme.sh/blob/master/dnsapi/dns_ali.sh)、[官方接入说明](https://github.com/acmesh-official/acme.sh/wiki/dnsapi#11-use-aliyun-domain-api-to-automatically-issue-cert)。

## 1. 准备受限身份

在阿里云 RAM 创建专用用户，使用其 AccessKey，不使用主账号 AccessKey。下面是权限起点；把 `<阿里云账号ID>` 替换为真实账号 ID，再在 RAM 控制台验证策略。

```json
{
  "Version": "1",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "alidns:DescribeDomainRecords",
      "alidns:AddDomainRecord",
      "alidns:DeleteDomainRecord"
    ],
    "Resource": "acs:alidns:*:<阿里云账号ID>:domain/zzzping.top"
  }]
}
```

这限制到 `zzzping.top` 的三个 DNS 操作，不能声称仅允许某一条 TXT。阿里云的该权限粒度是托管域；若需要进一步隔离，先规划独立验证域和 DNS alias，再授权那个域。权限不足时先按 API 错误查具体 action/resource，不直接扩大为管理员权限。[阿里云自定义策略](https://www.alibabacloud.com/help/en/dns/alibaba-cloud-dns-custom-permission-policy-reference-dns)、[API 授权表](https://www.alibabacloud.com/help/en/dns/api-alidns-2015-01-09-ram)。

## 2. 安装、验证和切换

以下操作留给持有 RAM 凭据的管理员，先替换尖括号占位值。保留原 Nginx 配置及 Certbot lineage 作为回滚材料，在 root 私有目录安装已审核版本的 acme.sh。安装会建立每日检查的 cron；先记录安装版本，并检查原有 cron 避免重复任务。[官方安装与证书部署说明](https://github.com/acmesh-official/acme.sh/blob/master/README.md)。

```bash
umask 077
git clone https://github.com/acmesh-official/acme.sh.git /root/acme.sh-source
cd /root/acme.sh-source
git checkout <已审核的发行标签或提交>
./acme.sh --install -m <接收证书通知的邮箱>
```

在自己的 Bash 终端静默输入凭据，不放入仓库、聊天、命令参数或终端录制；不要启用 shell tracing/debug。

```bash
set +x
read -r -s -p 'Aliyun AccessKey ID: ' Ali_Key; printf '\n'
read -r -s -p 'Aliyun AccessKey Secret: ' Ali_Secret; printf '\n'
export Ali_Key Ali_Secret
/root/.acme.sh/acme.sh --issue --server letsencrypt_test \
  --dns dns_ali -d notes.zzzping.top --keylength 2048
unset Ali_Key Ali_Secret
chmod 0600 /root/.acme.sh/account.conf
```

确认测试 CA 签发成功、TXT 清理成功后，再申请正式证书；测试证书不能安装到线上。插件会使用刚保存的私有凭据。若测试失败先排查域授权与 DNS 传播，不反复强制签发正式证书。

```bash
/root/.acme.sh/acme.sh --issue --server letsencrypt --force \
  --dns dns_ali -d notes.zzzping.top --keylength 2048
install -d -o root -g root -m 0750 /etc/nginx/tls/notes.zzzping.top
/root/.acme.sh/acme.sh --install-cert -d notes.zzzping.top \
  --key-file /etc/nginx/tls/notes.zzzping.top/privkey.pem \
  --fullchain-file /etc/nginx/tls/notes.zzzping.top/fullchain.pem \
  --reloadcmd '/usr/sbin/nginx -t && /bin/systemctl reload nginx'
chmod 0600 /etc/nginx/tls/notes.zzzping.top/privkey.pem
```

确认正式证书的 SAN、有效期及私钥匹配后，将**仅 Reading Notes vhost** 的 `ssl_certificate` / `ssl_certificate_key` 改成上面两条新路径，执行 `nginx -t && systemctl reload nginx`。公网读取实际服务的证书序列号、有效期与完整链；若失败，恢复原 vhost 的 `/etc/letsencrypt/live/notes.zzzping.top/` 路径并 reload。不要直接引用 acme.sh 内部工作目录的证书。

## 3. 验收定时续期

```bash
crontab -l
/root/.acme.sh/acme.sh --cron --home /root/.acme.sh
openssl s_client -connect notes.zzzping.top:443 -servername notes.zzzping.top \
  </dev/null 2>/dev/null | openssl x509 -noout -dates -serial -issuer
nginx -t
```

刚签发的证书运行 cron 通常显示尚未到期，这只证明调度入口能运行；DNS 自动签发能力以第 2 步测试 CA 实际成功为证。保存签发、TXT 清理、部署路径、reload 和公网证书读回结果，另外接入运维已有的到期告警。

切换验收成功后，把 **notes.zzzping.top 这一个** 旧 Certbot renewal 配置移到 root 私有备份目录，避免重复续期失败；保留其旧 live/archive 供短期回滚。服务器还有其他域名使用 Certbot，不停用整个 certbot.timer，也不删除其他证书。以后回滚至 Certbot 时恢复这份配置并重新验证续期方式。

本轮只提供这份可执行交接，没有创建 RAM 用户、读取 DNS 凭据、安装 acme.sh 或声称续期已通过。执行时需将实际客户端版本、证书路径和定时任务同步到环境登记。
