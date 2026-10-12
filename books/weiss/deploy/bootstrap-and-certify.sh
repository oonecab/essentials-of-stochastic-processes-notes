#!/usr/bin/env bash
# Run on the server with the uploaded release ID as the only argument.
set -euo pipefail
release_id=${1:?usage: bootstrap-and-certify.sh YYYYMMDDTHHMMSS}
[[ "$release_id" =~ ^[0-9]{8}T[0-9]{6}$ ]]
metadata=/var/lib/weiss-deploy/$release_id
site=/var/www/weiss.zzzping.top
config=/etc/nginx/sites-available/weiss.zzzping.top
enabled=/etc/nginx/sites-enabled/weiss.zzzping.top

test ! -e "$config"
test ! -e "$enabled"
test ! -e "$site/current"
cd "$metadata"
sha256sum -c archive.sha256
python3 - <<'PY'
import json, tarfile
metadata = json.load(open('release.json'))
with tarfile.open('site.tar.gz') as archive:
    members = archive.getmembers()
    assert sorted(m.name for m in members) == sorted(f['path'] for f in metadata['files'])
    assert all(m.isfile() and not m.name.startswith('/') and '..' not in m.name.split('/') for m in members)
print('Archive member allowlist: passed')
PY
mkdir "$site/releases/$release_id"
tar --no-same-owner --no-same-permissions -xzf site.tar.gz -C "$site/releases/$release_id"
find "$site/releases/$release_id" -type d -exec chmod 0755 {} +
find "$site/releases/$release_id" -type f -exec chmod 0644 {} +
(cd "$site/releases/$release_id" && sha256sum -c "$metadata/SHA256SUMS")
ln -s "releases/$release_id" "$site/current.$release_id"
mv -Tf "$site/current.$release_id" "$site/current"

install -o root -g root -m 0644 nginx-weiss-bootstrap.conf "$config"
ln -s "$config" "$enabled"
if ! nginx -t; then
    unlink "$enabled"
    mv "$config" "$metadata/bootstrap-rejected.conf"
    exit 1
fi
systemctl reload nginx
token=weiss-preflight-$release_id
challenge=/var/www/letsencrypt/.well-known/acme-challenge/$token
printf '%s\n' "$release_id" > "$challenge"
trap 'rm -f "$challenge"' EXIT
body=''
for attempt in $(seq 1 15); do
    body=$(curl --noproxy '*' --fail --silent --max-time 3 "http://weiss.zzzping.top/.well-known/acme-challenge/$token" || true)
    test "$body" = "$release_id" && break
    sleep 0.2
done
test "$body" = "$release_id"
printf 'HTTP-01 public preflight: passed\n'

certbot certonly --webroot --webroot-path /var/www/letsencrypt \
    --domain weiss.zzzping.top --cert-name weiss.zzzping.top \
    --non-interactive --agree-tos --keep-until-expiring
printf 'Certificate issued; final HTTPS configuration is ready to install.\n'
