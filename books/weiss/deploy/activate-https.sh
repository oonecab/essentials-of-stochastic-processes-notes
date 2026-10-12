#!/usr/bin/env bash
# Run on the server after the DNS certificate challenge has succeeded.
set -euo pipefail
release_id=${1:?usage: activate-https.sh YYYYMMDDTHHMMSS}
[[ "$release_id" =~ ^[0-9]{8}T[0-9]{6}$ ]]
metadata=/var/lib/weiss-deploy/$release_id
config=/etc/nginx/sites-available/weiss.zzzping.top
certificate=/etc/letsencrypt/live/weiss.zzzping.top/fullchain.pem

test -f "$certificate"
openssl x509 -in "$certificate" -noout -checkend 86400
openssl x509 -in "$certificate" -noout -checkhost weiss.zzzping.top
test "$(readlink -f /var/www/weiss.zzzping.top/current)" = "/var/www/weiss.zzzping.top/releases/$release_id"
(cd "/var/www/weiss.zzzping.top/releases/$release_id" && sha256sum -c "$metadata/SHA256SUMS")

cp -a "$config" "$metadata/nginx-before-https.conf"
install -o root -g root -m 0644 "$metadata/nginx-weiss.zzzping.top.conf" "$config.next"
mv -Tf "$config.next" "$config"
if ! nginx -t; then
    cp -a "$metadata/nginx-before-https.conf" "$config"
    exit 1
fi
systemctl reload nginx
# Reload is asynchronous; wait for the new HTTPS virtual host to answer.
status=0
redirect_status=0
for attempt in $(seq 1 15); do
    status=$(curl --noproxy '*' --resolve weiss.zzzping.top:443:127.0.0.1 --max-time 3 --silent --output /dev/null --write-out '%{http_code}' https://weiss.zzzping.top/ || true)
    redirect_status=$(curl --noproxy '*' --resolve weiss.zzzping.top:80:127.0.0.1 --max-time 3 --silent --output /dev/null --write-out '%{http_code}' http://weiss.zzzping.top/ || true)
    if test "$status" = 200 && test "$redirect_status" = 301; then break; fi
    sleep 0.2
done
test "$status" = 200
test "$redirect_status" = 301
printf 'HTTPS root: %s\n' "$status"
printf 'HTTP redirect: '
curl --noproxy '*' --resolve weiss.zzzping.top:80:127.0.0.1 --max-time 5 -sS -o /dev/null -w '%{http_code} %{redirect_url}\n' http://weiss.zzzping.top/
openssl x509 -in "$certificate" -noout -dates -issuer -ext subjectAltName
printf 'NGINX: '; systemctl is-active nginx
printf 'CURRENT: '; readlink -f /var/www/weiss.zzzping.top/current
