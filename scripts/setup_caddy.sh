#!/bin/sh
# Puts Caddy in front of the API with automatic HTTPS. Run as root on the VPS, after
# server_setup.sh and after the DNS A records below point at this server:
#   scp scripts/setup_caddy.sh root@<vps-ip>:/root/ && ssh root@<vps-ip> sh /root/setup_caddy.sh
#
#   https://api.duel-domain.com         -> production (127.0.0.1:8000)
#   https://staging-api.duel-domain.com -> staging    (127.0.0.1:8001)
#
# Safe to re-run (e.g. after editing the domains below).
set -e

PROD_DOMAIN="api.duel-domain.com"
STAGING_DOMAIN="staging-api.duel-domain.com"
CADDY_DIR="/opt/caddy"

echo "==> Checking DNS"
SERVER_IPS="$(hostname -I)"
for domain in "$PROD_DOMAIN" "$STAGING_DOMAIN"; do
    resolved="$(getent ahostsv4 "$domain" | awk 'NR==1 {print $1}')"
    case " $SERVER_IPS " in
        *" $resolved "*) echo "    $domain -> $resolved (this server)" ;;
        *)
            echo "    $domain resolves to '${resolved:-nothing}', not this server ($SERVER_IPS)."
            echo "    Add an A record for it pointing at this server, wait a few minutes, then re-run."
            exit 1
            ;;
    esac
done

echo "==> Writing $CADDY_DIR"
mkdir -p "$CADDY_DIR"

cat > "$CADDY_DIR/Caddyfile" <<EOF
$PROD_DOMAIN {
    encode gzip
    reverse_proxy 127.0.0.1:8000
}

$STAGING_DOMAIN {
    encode gzip
    reverse_proxy 127.0.0.1:8001
}
EOF

# Host networking lets Caddy reach the API on 127.0.0.1 and see real client IPs.
cat > "$CADDY_DIR/docker-compose.yml" <<'EOF'
services:
  caddy:
    image: caddy:2.10
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config

volumes:
  caddy_data:
  caddy_config:
EOF

echo "==> Firewall: open 80/443, close the raw API ports"
ufw allow 80/tcp
ufw allow 443/tcp
ufw delete allow 8000/tcp >/dev/null 2>&1 || true
ufw delete allow 8001/tcp >/dev/null 2>&1 || true

echo "==> Starting Caddy"
cd "$CADDY_DIR"
docker compose -p caddy up -d
docker compose -p caddy exec caddy caddy reload --config /etc/caddy/Caddyfile

echo
echo "Done. Certificates are issued on first request; give it a minute, then:"
echo "    curl https://$PROD_DOMAIN/health/"
echo "    curl https://$STAGING_DOMAIN/health/"
