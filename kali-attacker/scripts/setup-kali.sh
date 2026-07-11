#!/usr/bin/env bash
# ============================================================
# Kali Linux — Configuration réseau + outils (machine attaquant)
# ============================================================
# Configure l'IP statique sur le VLAN 10 et installe les outils
# nécessaires pour les démonstrations.
# ============================================================
set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }
[[ "$(id -u)" -eq 0 ]] || { echo "Exécuter en root (sudo)"; exit 1; }

KALI_IP="10.10.10.100"
GATEWAY="10.10.10.1"
DNS="10.10.30.20"

log "=== Configuration Kali (machine attaquant, VLAN 10) ==="

# --- 1. Configuration réseau ---
log "Configuration IP statique : $KALI_IP (VLAN 10)..."
cat > /etc/network/interfaces << EOF
auto eth0
iface eth0 inet static
    address $KALI_IP
    netmask 255.255.255.0
    gateway $GATEWAY
    dns-nameservers $DNS
EOF

# Application immédiate
ip addr flush dev eth0 2>/dev/null || true
ip addr add "$KALI_IP/24" dev eth0 2>/dev/null || true
ip route add default via "$GATEWAY" 2>/dev/null || true
echo "nameserver $DNS" > /etc/resolv.conf
log "Réseau configuré : $KALI_IP/24, GW $GATEWAY, DNS $DNS"

# --- 2. Mise à jour ---
log "Mise à jour du système..."
apt-get update -qq
apt-get upgrade -y -qq

# --- 3. Outils d'attaque (déjà présents sur Kali, on s'assure) ---
log "Installation/vérification des outils..."
apt-get install -y -qq nmap hydra sshpass curl

log "Outils installés :"
log "  - nmap     : scan réseau"
log "  - hydra    : bruteforce SSH"
log "  - sshpass  : authentification SSH automatisée"
log "  - curl     : requêtes HTTP"

# --- 4. Agent Wazuh (optionnel, pour surveiller aussi l'attaquant) ---
log ""
log "Optionnel : installer l'agent Wazuh sur Kali pour surveiller aussi cette machine."
log "  -> sudo WAZUH_MANAGER_IP=10.10.99.10 bash ../../wazuh/agents/deploy-agent-linux.sh kali-attacker"

log "=== Kali configurée ==="
log "Prochaine étape : exécuter les scénarios dans attack-scenarios/"
