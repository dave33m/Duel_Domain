#!/bin/sh
# One-time setup for a fresh Ubuntu VPS. Run as root:
#   scp scripts/server_setup.sh root@<vps-ip>:/root/ && ssh root@<vps-ip> sh /root/server_setup.sh
#
# Installs Docker, creates a non-root "deploy" user that GitHub Actions logs in as,
# clones production (~/Duel_Domain, port 8000) and staging (~/Duel_Domain-staging,
# port 8001) and writes a .env for each. Safe to re-run: existing pieces are skipped.
set -e

REPO_SSH="git@github.com:dave33m/Duel_Domain.git"
DEPLOY_USER="deploy"
DEPLOY_HOME="/home/$DEPLOY_USER"

echo "==> Installing Docker, git and firewall"
apt-get update -y
apt-get install -y docker.io docker-compose-v2 git ufw openssl
systemctl enable --now docker

echo "==> Creating $DEPLOY_USER user"
if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" "$DEPLOY_USER"
fi
usermod -aG docker "$DEPLOY_USER"

as_deploy() { su - "$DEPLOY_USER" -c "$1"; }

as_deploy 'mkdir -p ~/.ssh && chmod 700 ~/.ssh'

# Key GitHub Actions uses to SSH in as the deploy user.
if [ ! -f "$DEPLOY_HOME/.ssh/actions_key" ]; then
    as_deploy 'ssh-keygen -t ed25519 -N "" -C "github-actions" -f ~/.ssh/actions_key -q'
    as_deploy 'cat ~/.ssh/actions_key.pub >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
fi

# Key the server uses to pull the repo from GitHub (add as a read-only deploy key).
if [ ! -f "$DEPLOY_HOME/.ssh/id_ed25519" ]; then
    as_deploy 'ssh-keygen -t ed25519 -N "" -C "duel-domain-vps" -f ~/.ssh/id_ed25519 -q'
fi
as_deploy 'ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null; sort -u -o ~/.ssh/known_hosts ~/.ssh/known_hosts'

# The API ports stay on localhost; scripts/setup_caddy.sh serves them over HTTPS on 80/443.
echo "==> Opening firewall: SSH, HTTP, HTTPS"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

if ! as_deploy "git ls-remote $REPO_SSH >/dev/null 2>&1"; then
    echo
    echo "================================================================"
    echo "The server can't read the repo yet. Two things to do on GitHub:"
    echo
    echo "1) Add this as a read-only Deploy key"
    echo "   (repo Settings > Deploy keys > Add deploy key):"
    echo
    cat "$DEPLOY_HOME/.ssh/id_ed25519.pub"
    echo
    echo "2) Add these Actions secrets (Settings > Secrets and variables > Actions):"
    echo "   VPS_HOST    = this server's IP"
    echo "   VPS_USER    = $DEPLOY_USER"
    echo "   VPS_SSH_KEY = the private key below (all lines, including BEGIN/END)"
    echo
    cat "$DEPLOY_HOME/.ssh/actions_key"
    echo
    echo "Then re-run this script to clone and start both environments."
    echo "================================================================"
    exit 0
fi

# setup_env <dir> <branch> <port> <compose project>
setup_env() {
    if [ ! -d "$1/.git" ]; then
        as_deploy "git clone -b $2 $REPO_SSH $1"
    fi
    if [ ! -f "$1/.env" ]; then
        cat > "$1/.env" <<EOF
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
ALLOWED_HOSTS=
APP_PORT=$3
EOF
        chown "$DEPLOY_USER:$DEPLOY_USER" "$1/.env"
        chmod 600 "$1/.env"
    fi
    echo "==> Starting $4 on port $3"
    as_deploy "cd $1 && docker compose -p $4 up -d --build"
}
setup_env "$DEPLOY_HOME/Duel_Domain" main 8000 duel-domain
setup_env "$DEPLOY_HOME/Duel_Domain-staging" staging 8001 duel-domain-staging

echo
echo "Done. Check: curl http://localhost:8000/health/ and http://localhost:8001/health/"
echo "Next: point the API domains at this server and run scripts/setup_caddy.sh for HTTPS."
