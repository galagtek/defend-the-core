#!/usr/bin/env bash
# ============================================================
# Ubuntu Server — Configuration Auditd
# ============================================================
# Active auditd et configure les règles de surveillance :
# - Fichiers de configuration système
# - Identité (passwd, group, shadow)
# - Commandes sensibles
# - Accès sudo
# ============================================================
set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }
[[ "$(id -u)" -eq 0 ]] || { echo "Exécuter en root (sudo)"; exit 1; }

log "=== Configuration Auditd ==="

# --- 1. Installation ---
apt-get install -y -qq auditd audispd-plugins
systemctl enable auditd

# --- 2. Règles de surveillance ---
RULES_FILE="/etc/audit/rules.d/hardening.rules"

cat > "$RULES_FILE" << 'EOF'
# ============================================================
# Règles Auditd - Defend-The-Core (Ubuntu Server)
# ============================================================

# --- Surveillance des fichiers d'identité ---
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

# --- Surveillance de la configuration système ---
-w /etc/ssh/sshd_config -p wa -k config_changes
-w /etc/sudoers -p wa -k sudo_changes
-w /etc/sudoers.d/ -p wa -k sudo_changes
-w /etc/ufw/ -p wa -k firewall_changes
-w /etc/nginx/ -p wa -k web_config
-w /etc/postgresql/ -p wa -k db_config
-w /etc/crontab -p wa -k cron_changes
-w /etc/cron.d/ -p wa -k cron_changes
-w /etc/cron.daily/ -p wa -k cron_changes
-w /etc/cron.hourly/ -p wa -k cron_changes
-w /etc/cron.weekly/ -p wa -k cron_changes
-w /etc/cron.monthly/ -p wa -k cron_changes

# --- Surveillance des commandes sensibles ---
-w /bin/su -p x -k privileged
-w /usr/bin/sudo -p x -k privileged
-w /usr/bin/passwd -p x -k privileged
-w /usr/bin/chage -p x -k privileged
-w /usr/bin/usermod -p x -k privileged
-w /usr/bin/useradd -p x -k privileged
-w /usr/bin/userdel -p x -k privileged
-w /usr/bin/groupadd -p x -k privileged
-w /usr/bin/groupmod -p x -k privileged
-w /usr/bin/groupdel -p x -k privileged
-w /usr/bin/visudo -p x -k privileged
-w /usr/bin/crontab -p x -k privileged
-w /bin/mount -p x -k privileged
-w /bin/umount -p x -k privileged
-w /usr/bin/systemctl -p x -k system_control
-w /usr/bin/apt -p x -k package_management
-w /usr/bin/dpkg -p x -k package_management

# --- Surveillance réseau ---
-w /etc/hosts -p wa -k network_config
-w /etc/resolv.conf -p wa -k network_config
-w /etc/network/interfaces -p wa -k network_config
-w /etc/netplan/ -p wa -k network_config

# --- Paramètres système ---
# Arrêter le système
-w /sbin/shutdown -p x -k system_shutdown
-w /sbin/poweroff -p x -k system_shutdown
-w /sbin/reboot -p x -k system_shutdown
-w /sbin/halt -p x -k system_shutdown

# --- Paramètres d'audit eux-mêmes ---
-w /etc/audit/ -p wa -k audit_config
-w /etc/audit/rules.d/ -p wa -k audit_config

# --- Configuration de la capacité d'audit ---
-b 8192        # Buffer max
--backlog_wait_time 0
-f 1           # Panic sur erreur d'audit (sécurité maximale)
-e 2           # Règles immuables (ne peuvent pas être supprimées sans reboot)
EOF

# --- 3. Application des règles ---
log "Application des règles..."
augenrules --load
systemctl restart auditd

# --- 4. Configuration du forward des logs vers Wazuh ---
# auditd → syslog → Wazuh
cat > /etc/audisp/audispd.conf << 'EOF'
active = yes
direction = out
path = /sbin/audispd
type = always
args = /sbin/audisp-syslog
format = string
EOF

cat > /etc/audisp/plugins.d/syslog.conf << 'EOF'
active = yes
direction = out
path = /sbin/audisp-syslog
type = always
args = /var/log/audit/audit.log
format = string
EOF

systemctl restart audispd 2>/dev/null || systemctl restart auditd

log "=== Auditd configuré ==="
log "Règles appliquées :"
log "  - Surveillance identité (passwd, group, shadow)"
log "  - Surveillance config (sshd, sudoers, nginx, postgresql)"
log "  - Commandes sensibles (su, sudo, useradd, systemctl)"
log "  - Règles immuables (-e 2 : non supprimables sans reboot)"
log "Prochaine étape : bash 05-ufw-firewall.sh"
