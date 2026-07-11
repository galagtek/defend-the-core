#!/usr/bin/env bash
# ============================================================
# Ubuntu Server — Configuration de base
# ============================================================
# Mises à jour, utilisateur admin, sudoers, timezone, hostname.
# Idempotent. À exécuter en premier.
# ============================================================
set -euo pipefail

if [[ -f "$(dirname "$0")/../../.env" ]]; then
    # shellcheck disable=SC1091
    set -a; source "$(dirname "$0")/../../.env"; set +a
fi

ADMIN_USER="${UBUNTU_WEB_USER:-webadmin}"
HOSTNAME="ubuntu-web"

log() { echo "[$(date +%H:%M:%S)] $*"; }
[[ "$(id -u)" -eq 0 ]] || { echo "Exécuter en root (sudo)"; exit 1; }

log "=== Configuration de base Ubuntu Server ==="

# --- 1. Hostname ---
log "Configuration hostname : $HOSTNAME"
hostnamectl set-hostname "$HOSTNAME"

# --- 2. Timezone ---
log "Timezone : Europe/Paris"
timedatectl set-timezone Europe/Paris

# --- 3. Mises à jour ---
log "Mises à jour système..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq curl wget vim git ufw auditd unattended-upgrades

# --- 4. Utilisateur admin ---
if ! id "$ADMIN_USER" &>/dev/null; then
    log "Création utilisateur $ADMIN_USER"
    useradd -m -s /bin/bash "$ADMIN_USER"
    # Mot de passe temporaire (à changer au premier login)
    echo "${ADMIN_USER}:ChangerMoi!2026" | chpasswd
    usermod -aG sudo "$ADMIN_USER"
    log "Utilisateur $ADMIN_USER créé (groupe sudo)."
else
    log "Utilisateur $ADMIN_USER déjà existant."
fi

# --- 5. Sudoers : exigence mot de passe + log ---
log "Configuration sudoers..."
cat > /etc/sudoers.d/"${ADMIN_USER}" << EOF
# Sudo pour ${ADMIN_USER} - exige le mot de passe, log toutes les commandes
${ADMIN_USER} ALL=(ALL) ALL
Defaults:${ADMIN_USER} !requiretty
Defaults log_input, log_output
Defaults logfile="/var/log/sudo.log"
EOF
chmod 440 /etc/sudoers.d/"${ADMIN_USER}"
visudo -cf /etc/sudoers.d/"${ADMIN_USER}" >/dev/null

# --- 6. Mises à jour de sécurité automatiques ---
log "Activation mises à jour sécurité automatiques..."
cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "04:00";
EOF

cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

# --- 7. Dossier .ssh pour l'admin ---
log "Préparation dossier SSH pour $ADMIN_USER..."
SSH_DIR="/home/${ADMIN_USER}/.ssh"
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"
chown "${ADMIN_USER}:${ADMIN_USER}" "$SSH_DIR"
touch "$SSH_DIR/authorized_keys"
chmod 600 "$SSH_DIR/authorized_keys"
chown "${ADMIN_USER}:${ADMIN_USER}" "$SSH_DIR/authorized_keys"

log "=== Configuration de base terminée ==="
log "⚠️ Injectez la clé publique du bastion dans /home/${ADMIN_USER}/.ssh/authorized_keys"
log "Prochaine étape : bash 01-web-stack.sh"
