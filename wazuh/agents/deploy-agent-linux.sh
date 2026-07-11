#!/usr/bin/env bash
# ============================================================
# Wazuh — Déploiement de l'agent sur Linux
# ============================================================
# Installe et configure l'agent Wazuh sur un hôte Linux supervisé
# (Ubuntu, NixOS, Kali, etc.). Idempotent.
#
# Usage :
#   sudo WAZUH_MANAGER_IP=10.10.99.10 bash deploy-agent-linux.sh [nom_agent]
#
# Exemples :
#   sudo WAZUH_MANAGER_IP=10.10.99.10 bash deploy-agent-linux.sh ubuntu-web
#   sudo WAZUH_MANAGER_IP=10.10.99.10 bash deploy-agent-linux.sh bastion-nixos
#   sudo WAZUH_MANAGER_IP=10.10.99.10 bash deploy-agent-linux.sh kali-attacker
# ============================================================
set -euo pipefail

# --- Variables ---
WAZUH_VERSION="4.7.0"
WAZUH_MANAGER_IP="${WAZUH_MANAGER_IP:-10.10.99.10}"
AGENT_NAME="${1:-$(hostname)}"
AGENT_GROUP="${AGENT_GROUP:-linux}"

log() { echo "[$(date +%H:%M:%S)] $*"; }
err() { echo "[$(date +%H:%M:%S)] ERREUR: $*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || err "Exécuter en root (sudo)."

log "=== Déploiement agent Wazuh ($AGENT_NAME) ==="
log "Manager : $WAZUH_MANAGER_IP"

# --- Détection de l'OS / gestionnaire de paquets ---
detect_os() {
    if [[ -f /etc/debian_version ]]; then
        echo "debian"
    elif [[ -f /etc/nixos/configuration.nix ]]; then
        echo "nixos"
    elif [[ -f /etc/redhat-release ]]; then
        echo "rpm"
    else
        echo "unknown"
    fi
}

OS_TYPE=$(detect_os)
log "OS détecté : $OS_TYPE"

# --- 1. Installation de l'agent ---
install_debian() {
    log "Installation via APT (Debian/Ubuntu/Kali)..."
    apt-get update -qq
    apt-get install -y -qq curl gnupg2 apt-transport-https lsb-release
    curl -fsSL "https://packages.wazuh.com/key/GPG-KEY-WAZUH" | \
        gpg --dearmor -o /usr/share/keyrings/wazuh.gpg
    echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" \
        > /etc/apt/sources.list.d/wazuh.list
    apt-get update -qq
    apt-get install -y -qq wazuh-agent="${WAZUH_VERSION}-1"
}

install_rpm() {
    log "Installation via RPM (RHEL/CentOS/Fedora)..."
    rpm --import https://packages.wazuh.com/key/GPG-KEY-WAZUH
    cat > /etc/yum.repos.d/wazuh.repo << 'EOF'
[wazuh]
gpgcheck=1
gpgkey=https://packages.wazuh.com/key/GPG-KEY-WAZUH
enabled=1
name=Wazuh
baseurl=https://packages.wazuh.com/4.x/yum/
protect=1
EOF
    yum install -y wazuh-agent-"${WAZUH_VERSION}"
}

install_nixos() {
    log "Installation via NixOS (config déclarative)..."
    err "Sur NixOS, ajoutez wazuh-agent via configuration.nix (voir bastion-nixos/README.md)."
}

case "$OS_TYPE" in
    debian) install_debian ;;
    rpm)    install_rpm ;;
    nixos)  install_nixos ;;
    *)      err "OS non supporté par ce script." ;;
esac

# --- 2. Configuration de l'agent ---
log "Configuration de l'agent..."
AGENT_CONF="/var/ossec/etc/ossec.conf"
if [[ -f "$AGENT_CONF" ]]; then
    # Remplacer l'adresse du manager
    sed -i "s|<address>.*</address>|<address>${WAZUH_MANAGER_IP}</address>|" "$AGENT_CONF" || true
    # S'assurer que l'enregistrement automatique est activé
    if ! grep -q "<enrollment>" "$AGENT_CONF"; then
        python3 - "$AGENT_CONF" "$AGENT_NAME" "$AGENT_GROUP" <<'PYEOF'
import sys
conf_path, agent_name, agent_group = sys.argv[1], sys.argv[2], sys.argv[3]
with open(conf_path, 'r') as f:
    content = f.read()

enrollment = f"""  <enrollment>
    <agent_name>{agent_name}</agent_name>
    <agent_group>{agent_group}</agent_group>
    <manager_ip>REPLACED_BY_SED</manager_ip>
  </enrollment>
</ossec_config>"""
content = content.replace("</ossec_config>", enrollment, 1)
with open(conf_path, 'w') as f:
    f.write(content)
PYEOF
        sed -i "s|<manager_ip>REPLACED_BY_SED</manager_ip>|<manager_ip>${WAZUH_MANAGER_IP}</manager_ip>|" "$AGENT_CONF"
    fi
    log "Configuration appliquée (manager=${WAZUH_MANAGER_IP}, name=${AGENT_NAME}, group=${AGENT_GROUP})."
fi

# --- 3. Démarrage du service ---
log "Démarrage de l'agent..."
if systemctl list-unit-files | grep -q wazuh-agent; then
    systemctl daemon-reload
    systemctl enable --now wazuh-agent
    sleep 2
    if systemctl is-active --quiet wazuh-agent; then
        log "✅ Agent Wazuh actif."
    else
        log "❌ Agent inactif. Vérifiez : journalctl -u wazuh-agent"
    fi
fi

# --- 4. Vérification de l'enregistrement ---
log "Vérification de l'enregistrement auprès du manager..."
sleep 3
if [[ -f /var/ossec/logs/ossec.log ]]; then
    if grep -q "Connected to the manager" /var/ossec/logs/ossec.log 2>/dev/null; then
        log "✅ Agent enregistré et connecté au manager."
    else
        log "⏳ Enregistrement en cours... Vérifiez le dashboard Wazuh."
    fi
fi

log "=== Agent Wazuh déployé ($AGENT_NAME) ==="
log "Vérifiez sur le dashboard : Agents > ${AGENT_NAME}"
