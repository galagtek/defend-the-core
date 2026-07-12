#!/usr/bin/env bash
# ============================================================
# Gitea — Installation automatisée sur Ubuntu 26.04 (VLAN 99)
# ============================================================
# Installe Gitea avec :
#   - Utilisateur système dédié (git)
#   - Base SQLite (suffisante pour un labo, PostgreSQL pour la prod)
#   - Service systemd
#   - Durcissement de base
#
# Pré-requis : Ubuntu 26.04, VM sur VLAN 99 (10.10.99.30)
# ============================================================
set -euo pipefail

GITEA_VERSION="1.22.0"
GITEA_HOME="/var/lib/gitea"
GITEA_USER="git"

log() { echo "[$(date +%H:%M:%S)] $*"; }
[[ "$(id -u)" -eq 0 ]] || { echo "Exécuter en root (sudo)"; exit 1; }

log "=== Installation de Gitea $GITEA_VERSION ==="

# --- 1. Mises à jour + pré-requis ---
log "Installation des pré-requis..."
apt-get update -qq
apt-get install -y -qq git sqlite3 curl

# --- 2. Utilisateur système git ---
if ! id "$GITEA_USER" &>/dev/null; then
    log "Création utilisateur $GITEA_USER..."
    useradd --system --shell /bin/bash --create-home --home-dir "/home/$GITEA_USER" "$GITEA_USER"
fi

# --- 3. Structure de répertoires ---
log "Création des répertoires..."
mkdir -p "$GITEA_HOME"/{custom,data,log}
mkdir -p /etc/gitea
chown -R "$GITEA_USER:$GITEA_USER" "$GITEA_HOME"
chmod 750 "$GITEA_HOME"
chmod 770 /etc/gitea
chown root:"$GITEA_USER" /etc/gitea

# --- 4. Téléchargement du binaire ---
log "Téléchargement de Gitea $GITEA_VERSION..."
GITEA_ARCH="gitea-${GITEA_VERSION}-linux-amd64"
curl -sL "https://dl.gitea.io/gitea/${GITEA_VERSION}/${GITEA_ARCH}" -o /usr/local/bin/gitea
chmod +x /usr/local/bin/gitea
log "Binaire installé : $(/usr/local/bin/gitea --version)"

# --- 5. Configuration ---
log "Création de la configuration..."
cat > /etc/gitea/app.ini << EOF
APP_NAME = Defend-The-Core Git
RUN_USER = $GITEA_USER
RUN_MODE = prod

[server]
HTTP_ADDR = 10.10.99.30
HTTP_PORT = 3000
DOMAIN = 10.10.99.30
ROOT_URL = http://10.10.99.30:3000/
DISABLE_SSH = false
SSH_DOMAIN = 10.10.99.30
SSH_PORT = 22
LFS_START_SERVER = true

[database]
DB_TYPE = sqlite3
PATH = $GITEA_HOME/data/gitea.db

[security]
INSTALL_LOCK = true
SECRET_KEY = CHANGEZ_MOI_POUR_UNE_CLE_ALEATOIRE
INTERNAL_TOKEN = CHANGEZ_MOI_AUSSI

[service]
DISABLE_REGISTRATION = true
REQUIRE_SIGNIN_VIEW = true
DEFAULT_ALLOW_CREATE_ORGANIZATION = false

[log]
LEVEL = Info
MODE = console

[other]
SHOW_FOOTER_VERSION = false
SHOW_FOOTER_TEMPLATE_LOAD_TIME = false
EOF
chown "$GITEA_USER:$GITEA_USER" /etc/gitea/app.ini
chmod 640 /etc/gitea/app.ini

# --- 6. Service systemd ---
log "Création du service systemd..."
cat > /etc/systemd/system/gitea.service << EOF
[Unit]
Description=Gitea (Git with a cup of tea)
After=syslog.target
After=network.target
After=mysqld.service
After=postgresql.service

[Service]
User=$GITEA_USER
Group=$GITEA_USER
WorkingDirectory=$GITEA_HOME
Environment=GITEA_WORK_DIR=$GITEA_HOME
Environment=GITEA_CUSTOM=$GITEA_HOME/custom
ExecStart=/usr/local/bin/gitea web --config /etc/gitea/app.ini
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now gitea
sleep 2

if systemctl is-active --quiet gitea; then
    log "✅ Gitea démarré et actif."
else
    log "❌ Gitea n'a pas démarré. Vérifiez : journalctl -u gitea"
    exit 1
fi

# --- 7. Pare-feu local (UFW) ---
log "Configuration UFW..."
if command -v ufw >/dev/null; then
    ufw allow 3000/tcp comment 'Gitea web'
    ufw allow 22/tcp comment 'SSH (git push)'
fi

# --- 8. Durcissement de base ---
log "Durcissement de base..."
# Désactiver l'enregistrement public (déjà dans app.ini, on s'assure)
# Restreindre les permissions
chmod 750 "$GITEA_HOME"
chmod 640 "$GITEA_HOME/data/gitea.db" 2>/dev/null || true

log "=== Installation terminée ==="
log ""
log "Gitea est accessible sur : http://10.10.99.30:3000"
log "⚠️ Premier accès : créez le compte administrateur immédiatement."
log "⚠️ Puis configurez l'authentification LDAP (configure-ldap.sh)."
log "⚠️ Générez un SECRET_KEY et INTERNAL_TOKEN aléatoires :"
log "   openssl rand -hex 32"
