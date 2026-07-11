#!/usr/bin/env bash
# ============================================================
# Wazuh — Installation du manager + indexer + dashboard
# ============================================================
# Installe la stack Wazuh complète sur Ubuntu 22.04 (VLAN 99).
# Utilise le script d'installation officiel wazuh-install.sh.
#
# Composants installés :
#   - Wazuh Indexer (stockage, fork Elasticsearch)
#   - Wazuh Manager  (corrélation, règles, active response)
#   - Wazuh Dashboard (UI, fork Kibana)
#
# Pré-requis : Ubuntu 22.04, 8Go RAM min, accès Internet
# ============================================================
set -euo pipefail

# --- Variables ---
WAZUH_VERSION="4.7.0"
WAZUH_PKG_REPO="https://packages.wazuh.com/4.x"
WAZUH_INSTALL_SCRIPT="wazuh-install.sh"

# Charger .env si présent
if [[ -f "$(dirname "$0")/../../.env" ]]; then
    # shellcheck disable=SC1091
    set -a; source "$(dirname "$0")/../../.env"; set +a
fi

: "${WAZUH_ADMIN_PASSWORD:?WAZUH_ADMIN_PASSWORD requis dans .env}"
: "${WAZUH_API_USER:=wazuh}"
: "${WAZUH_API_PASSWORD:?WAZUH_API_PASSWORD requis dans .env}"

log() { echo "[$(date +%H:%M:%S)] $*"; }
err() { echo "[$(date +%H:%M:%S)] ERREUR: $*" >&2; exit 1; }

# --- Vérification root ---
[[ "$(id -u)" -eq 0 ]] || err "Ce script doit être exécuté en root (sudo)."

# --- Vérification OS ---
[[ -f /etc/os-release ]] || err "OS non supporté (Ubuntu 22.04 requis)."
. /etc/os-release
log "OS détecté : $PRETTY_NAME"

log "=== Installation de Wazuh $WAZUH_VERSION ==="

# --- 1. Pré-requis système ---
log "Installation des pré-requis..."
apt-get update -qq
apt-get install -y -qq curl gnupg2 apt-transport-https lsb-release

# --- 2. Téléchargement du script officiel ---
log "Téléchargement du script d'installation officiel..."
curl -sO "https://packages.wazuh.com/4.x/${WAZUH_INSTALL_SCRIPT}"
chmod +x "${WAZUH_INSTALL_SCRIPT}"

# --- 3. Génération du fichier de config (wazuh-install-files/) ---
log "Génération des certificats et configuration..."
# Le script officiel crée wazuh-install-files/ avec les certifs
WAZUH_ADMIN_PASSWORD="${WAZUH_ADMIN_PASSWORD}" \
WAZUH_API_USER="${WAZUH_API_USER}" \
WAZUH_API_PASSWORD="${WAZUH_API_PASSWORD}" \
bash "${WAZUH_INSTALL_SCRIPT}" --generate-config-files

# --- 4. Installation des trois composants ---
log "Installation de Wazuh Indexer + Manager + Dashboard..."
bash "${WAZUH_INSTALL_SCRIPT}" -a

# --- 5. Vérification des services ---
log "Vérification des services..."
SERVICES=("wazuh-indexer" "wazuh-manager" "wazuh-dashboard")
for svc in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc"; then
        log "  ✅ $svc : actif"
    else
        log "  ❌ $svc : inactif (vérifiez les logs : journalctl -u $svc)"
    fi
done

# --- 6. Configuration du syslog entrant (UDP 514) ---
log "Configuration de la réception syslog (UDP 514)..."
# Wazuh écoute déjà sur 1514 pour les agents. On configure le syslog distant (514)
# pour réceptionner les logs OPNsense.
OSSEC_CONF="/var/ossec/etc/ossec.conf"
if [[ -f "$OSSEC_CONF" ]]; then
    # Ajouter une configuration de syslog remote si absente
    if ! grep -q "remote" "$OSSEC_CONF" 2>/dev/null; then
        python3 - "$OSSEC_CONF" <<'PYEOF'
import sys
conf_path = sys.argv[1]
with open(conf_path, 'r') as f:
    content = f.read()

# Insertion de la config syslog remote avant </ossec_config>
syslog_block = """  <remote>
    <connection>syslog</connection>
    <port>514</port>
    <protocol>udp</protocol>
    <allowed-ips>10.10.10.0/24</allowed-ips>
    <allowed-ips>10.10.20.0/24</allowed-ips>
    <allowed-ips>10.10.30.0/24</allowed-ips>
    <allowed-ips>10.10.99.0/24</allowed-ips>
    <local_ip>10.10.99.10</local_ip>
  </remote>
</ossec_config>"""

content = content.replace("</ossec_config>", syslog_block, 1)
with open(conf_path, 'w') as f:
    f.write(content)
print("Configuration syslog ajoutée.")
PYEOF
        systemctl restart wazuh-manager
        log "Réception syslog (UDP 514) configurée pour tous les VLANs."
    else
        log "Configuration syslog déjà présente."
    fi
fi

# --- 7. Ouverture du pare-feu local (si UFW actif) ---
if command -v ufw >/dev/null && ufw status | grep -q "active"; then
    log "Configuration UFW pour Wazuh..."
    ufw allow 1514/udp   # Agents Wazuh
    ufw allow 1514/tcp   # Agents Wazuh (TCP)
    ufw allow 514/udp    # Syslog distant (OPNsense)
    ufw allow 5601/tcp   # Dashboard (accès admin local)
    ufw allow 55000/tcp  # API Wazuh
    log "Règles UFW ajoutées."
fi

# --- 8. Affichage des informations de connexion ---
log ""
log "=== Installation Wazuh terminée ==="
log ""
log "Dashboard : https://10.10.99.10:5601"
log "Utilisateur : admin"
log "Mot de passe : (cf. .env / wazuh-install-files/wazuh-passwords.txt)"
log ""
log "API Wazuh : https://10.10.99.10:55000"
log "Étapes suivantes :"
log "  1. Déployer les agents sur les VMs (agents/deploy-agent-*.sh)"
log "  2. Importer les règles custom (rules/custom-rules.xml)"
log "  3. Importer les dashboards (dashboard/*.json)"
log "  4. Configurer l'active response (rules/active-response/)"
