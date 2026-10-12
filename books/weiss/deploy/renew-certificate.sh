#!/usr/bin/env bash
# Run interactively on the server; add the fresh TXT value before continuing.
set -euo pipefail
certbot certonly --manual --preferred-challenges dns \
    --cert-name weiss.zzzping.top --domain weiss.zzzping.top \
    --force-renewal --agree-tos --manual-public-ip-logging-ok \
    --deploy-hook 'nginx -t && systemctl reload nginx'
