#!/usr/bin/env bash
# ============================================================
# Ubuntu Server — Installation agent Wazuh
# ============================================================
# Installe l'agent Wazuh et l'enrôle auprès du manager.
# Réutilise le script commun du dossier wazuh/.
# ============================================================
set -euo pipefail

if [[ -f "$(dirname "$0")/../../.env" ]]; then
    # shellcheck disable=SC1091
    set -a; source "$(dirname "$0")/../../.env"; set +a
fi

WAZUH_MANAGER_IP="${WAZUH_MANAGER_IP:-10.10.99.10}"
AGENT_NAME="${1:-ubuntu-web}"
AGENT_GROUP="critical"

log() { echo "[$(date +%H:%M:%S)] $*"; }
[[ "$(id -u)" -eq 0 ]] || { echo "Exécuter en root (sudo)"; exit 1; }

log "=== Installation agent Wazuh ($AGENT_NAME, groupe=$AGENT_GROUP) ==="

# --- Délégation au script commun ---
DEPLOY_SCRIPT="$(dirname "$0")/../../wazuh/agents/deploy-agent-linux.sh"
if [[ -f "$DEPLOY_SCRIPT" ]]; then
    log "Utilisation du script commun de déploiement..."
    AGENT_GROUP="$AGENT_GROUP" WAZUH_MANAGER_IP="$WAZUH_MANAGER_IP" \
        bash "$DEPLOY_SCRIPT" "$AGENT_NAME"
else
    log "Script commun introuvable, installation directe..."
    # Fallback : installation minimale
    curl -fsSL https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --dearmor -o /usr/share/keyrings/wazuh.gpg
    echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" \
        > /etc/apt/sources.list.d/wazuh.list
    apt-get update -qq
    apt-get install -y -qq wazuh-agent
    sed -i "s|<address>.*</address>|<address>${WAZUH_MANAGER_IP}</address>|" /var/ossec/etc/ossec.conf
    systemctl enable --now wazuh-agent
fi

log "=== Agent Wazuh installé ($AGENT_NAME) ==="
log "Prochaine étape : bash 04-configure-auditd.sh"
