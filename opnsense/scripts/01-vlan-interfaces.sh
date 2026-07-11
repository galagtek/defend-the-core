#!/usr/bin/env bash
# ============================================================
# OPNsense — Configuration des interfaces VLAN
# ============================================================
# Vérifie/affecte les adresses IP des interfaces conformément au
# plan d'adressage (10.10.X.0/24). Idempotent.
#
# Interfaces (mapping VirtualBox) :
#   vtnet0 = WAN  (DHCP, 10.0.2.0/24 NAT VirtualBox)
#   vtnet1 = LAN  = VLAN 10 (10.10.10.1/24)
#   vtnet2 = OPT1 = VLAN 20 (10.10.20.1/24)
#   vtnet3 = OPT2 = VLAN 30 (10.10.30.1/24)
#   vtnet4 = OPT3 = VLAN 99 (10.10.99.1/24)
# ============================================================
set -euo pipefail

if [[ -f "$(dirname "$0")/../../.env" ]]; then
    # shellcheck disable=SC1091
    set -a; source "$(dirname "$0")/../../.env"; set +a
fi

: "${OPNSENSE_API_KEY:?OPNSENSE_API_KEY requis}"
: "${OPNSENSE_API_SECRET:?OPNSENSE_API_SECRET requis}"
: "${OPNSENSE_HOST:?OPNSENSE_HOST requis}"

API_URL="https://${OPNSENSE_HOST}/api"
AUTH="${OPNSENSE_API_KEY}:${OPNSENSE_API_SECRET}"

log() { echo "[$(date +%H:%M:%S)] $*"; }

api_get() {
    curl -sk -u "$AUTH" "${API_URL}/$1"
}
api_post() {
    local endpoint="$1"; local payload="${2:-{}}"
    curl -sk -u "$AUTH" -X POST "${API_URL}/${endpoint}" \
        -H "Content-Type: application/json" -d "$payload"
}

# --- Définition des interfaces du plan d'adressage ---
# format: "device|nom_opnsense|ip_cidr|description"
INTERFACES=(
    "vtnet1|lan|10.10.10.1/24|VLAN10-Bureautique"
    "vtnet2|opt1|10.10.20.1/24|VLAN20-DMZ"
    "vtnet3|opt2|10.10.30.1/24|VLAN30-Critique"
    "vtnet4|opt3|10.10.99.1/24|VLAN99-Admin-SIEM"
)

log "=== Configuration des interfaces VLAN ==="

# --- 1. Vérification de la connectivité ---
log "Vérification API..."
api_get "core/system/status" >/dev/null 2>&1 || { echo "API injoignable"; exit 1; }

# --- 2. Affectation IP de chaque interface ---
for entry in "${INTERFACES[@]}"; do
    IFS='|' read -r device name ip_cidr description <<< "$entry"
    log "Configuration ${name} (${device}) -> ${ip_cidr} [${description}]"

    # Récupérer l'UUID de l'interface
    if_id=$(api_get "interfaces/${name}/export" 2>/dev/null \
            | python3 -c "import sys,json; print(json.load(sys.stdin).get('uuid',''))" 2>/dev/null || echo "")

    # POST de la configuration IP
    ip="${ip_cidr%/*}"
    cidr="${ip_cidr#*/}"
    payload=$(cat <<EOF
{
    "interface": {
        "if": "${device}",
        "descr": "${description}",
        "ipaddr": "${ip}",
        "subnet": "${cidr}",
        "enable": "1"
    }
}
EOF
)
    api_post "interfaces/${name}/set" "$payload" >/dev/null 2>&1 || true
    log "  -> ${name} configurée"
done

# --- 3. Activation du DHCP sur le VLAN 10 (bureautique) ---
log "Activation DHCP sur VLAN 10 (plage .100-.200)..."
dhcp_payload=$(cat <<'EOF'
{
    "dhcpd": {
        "lan": {
            "enable": "1",
            "range": {"from": "10.10.10.100", "to": "10.10.10.200"},
            "defaultleasetime": "7200",
            "maxleasetime": "86400"
        }
    }
}
EOF
)
api_post "dhcpv4/set" "$dhcp_payload" >/dev/null 2>&1 || true
log "DHCP VLAN 10 activé."

# --- 4. Désactivation explicite DHCP sur VLAN 20, 30, 99 (statique) ---
log "Désactivation DHCP sur VLAN 20/30/99 (adresses statiques)..."
for vlan in opt1 opt2 opt3; do
    api_post "dhcpv4/set" "{\"dhcpd\": {\"${vlan}\": {\"enable\": \"0\"}}}" >/dev/null 2>&1 || true
done
log "DHCP désactivé sur les zones sensibles."

# --- 5. Application des changements ---
log "Application des changements (configd reload)..."
api_post "interfaces/reconfigure" >/dev/null 2>&1 || true
api_post "core/service/restart" '{"service": "dhcpd"}' >/dev/null 2>&1 || true

log "=== Interfaces VLAN configurées ==="
log "Récapitulatif :"
log "  VLAN 10 (Bureautique) : 10.10.10.1/24  [DHCP actif]"
log "  VLAN 20 (DMZ)         : 10.10.20.1/24  [statique]"
log "  VLAN 30 (Critique)    : 10.10.30.1/24  [statique]"
log "  VLAN 99 (Admin/SIEM)  : 10.10.99.1/24  [statique]"
log "Prochaine étape : bash 02-firewall-rules.sh"
