#!/usr/bin/env bash
# ============================================================
# Ubuntu Server — Durcissement SSH
# ============================================================
# SSH clés uniquement, root interdit, algorithmes crypto forts,
# limites de connexion, bannière d'avertissement.
# ============================================================
set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }
[[ "$(id -u)" -eq 0 ]] || { echo "Exécuter en root (sudo)"; exit 1; }

SSHD_CONF="/etc/ssh/sshd_config"

log "=== Durcissement SSH ==="

# --- 1. Sauvegarde ---
cp "$SSHD_CONF" "${SSHD_CONF}.bak.$(date +%s)"

# --- 2. Configuration durcie (réécriture complète) ---
cat > "$SSHD_CONF" << 'EOF'
# ============================================================
# SSHD durci - Defend-The-Core (Ubuntu Server)
# ============================================================

Port 22
AddressFamily inet
ListenAddress 10.10.30.10

# --- Hôtes ---
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key

# --- Authentification ---
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes

# --- Restrictions ---
AllowAgentForwarding no
AllowTcpForwarding no
X11Forwarding no
PermitTunnel no
AllowUsers webadmin

# --- Limites ---
MaxAuthTries 3
MaxSessions 4
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 0

# --- Cryptographie (algorithmes modernes uniquement) ---
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes256-ctr
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
HostKeyAlgorithms ssh-ed25519,ssh-ed25519-cert-v01@openssh.com

# --- Logging ---
LogLevel VERBOSE
SyslogFacility AUTH
PrintMotd no
PrintLastLog yes

# --- Divers ---
StrictModes yes
UseDNS no
GSSAPIAuthentication no
Subsystem sftp /usr/lib/openssh/sftp-server
EOF

# --- 3. Bannière d'avertissement ---
cat > /etc/ssh/banner << 'EOF'
============================================================
ACCES RESERVE - Defend-The-Core (Zone Critique, VLAN 30)
============================================================
Toute connexion est journalisee et envoyee au SIEM (Wazuh).
Toute tentative d'acces non autorise sera poursuivie.
============================================================
EOF
echo "Banner /etc/ssh/banner" >> "$SSHD_CONF"

# --- 4. Génération clés hôtes ed25519 si absentes ---
if [[ ! -f /etc/ssh/ssh_host_ed25519_key ]]; then
    log "Génération clé hôte ed25519..."
    ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N "" -q
fi

# --- 5. Suppression clés hôtes faibles (DSA, RSA 1024) ---
rm -f /etc/ssh/ssh_host_dsa_key* /etc/ssh/ssh_host_ecdsa_key*
log "Clés hôtes faibles (DSA, ECDSA) supprimées."

# --- 6. Validation & redémarrage ---
log "Validation configuration SSH..."
if sshd -t; then
    systemctl restart sshd
    log "✅ SSH durci et redémarré."
else
    echo "ERREUR: configuration SSH invalide. Restauration..."
    cp "${SSHD_CONF}.bak.$(ls -t ${SSHD_CONF}.bak.* | head -1 | sed 's/.*bak\.//')" "$SSHD_CONF"
    exit 1
fi

log "=== SSH durci ==="
log "Récapitulatif :"
log "  - Root login : interdit"
log "  - Authentification : clés uniquement"
log "  - Utilisateur autorisé : webadmin"
log "  - Algorithmes : ed25519, chacha20-poly1305, sha2-512"
log "  - MaxAuthTries : 3"
log "⚠️ Assurez-vous que la clé publique du bastion est dans authorized_keys"
log "Prochaine étape : bash 03-install-wazuh-agent.sh"
