#!/usr/bin/env bash
# ============================================================
# OPNsense — Règles de pare-feu (matrice default-deny)
# ============================================================
# Applique la matrice des flux autorisés décrite dans
# ../../architecture/firewall-rules.md
#
# Principe : default-deny. Les règles 'block' sont placées en
# priorité haute, les 'allow' ensuite, puis un block final
# implicite bloque tout le reste.
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

api_get()  { curl -sk -u "$AUTH" "${API_URL}/$1"; }
api_post() {
    local endpoint="$1"; local payload="${2:-{}}"
    curl -sk -u "$AUTH" -X POST "${API_URL}/${endpoint}" \
        -H "Content-Type: application/json" -d "$payload"
}

# --- Définition des alias (réseaux) ---
# Les alias centralisent les objets réseau pour des règles lisibles & maintenables.
declare -A ALIASES=(
    ["net_vlan10"]="10.10.10.0/24"
    ["net_vlan20"]="10.10.20.0/24"
    ["net_vlan30"]="10.10.30.0/24"
    ["net_vlan99"]="10.10.99.0/24"
    ["host_wazuh"]="10.10.99.10"
    ["host_bastion"]="10.10.99.20"
    ["host_reverse_proxy"]="10.10.20.10"
    ["host_vpn"]="10.10.20.20"
    ["host_ubuntu_web"]="10.10.30.10"
    ["host_win_server"]="10.10.30.20"
    ["host_win10"]="10.10.10.50"
)

# --- Définition des règles de pare-feu ---
# Format: "interface|action|protocol|source|src_port|destination|dst_port|descr|log"
# action: allow | block
# source/destination: alias name, IP, ou "any"
FIREWALL_RULES=(
    # === Règles BLOCK prioritaires (isolation des zones sensibles) ===
    "lan|block|any|net_vlan10||net_vlan30||Block VLAN10->VLAN30 (isolation critique)|1"
    "lan|block|any|net_vlan10||net_vlan99||Block VLAN10->VLAN99 (isolation admin)|1"
    "opt1|block|any|net_vlan20||net_vlan30||Block VPN->VLAN30 (pas d'acces direct BDD)|1"
    "opt2|block|any|net_vlan30||net_vlan99||Block VLAN30->VLAN99 sauf logs|1"

    # === Règles ALLOW (flux métier explicites) ===
    "lan|allow|tcp|net_vlan10||host_reverse_proxy|80,443|VLAN10 -> Reverse proxy HTTP(S)|1"
    "lan|allow|udp|net_vlan10||host_vpn|443|VLAN10 -> VPN gateway|1"
    "lan|allow|tcp|net_vlan10||host_vpn|443|VLAN10 -> VPN gateway TCP|1"
    "lan|allow|any|net_vlan10||WAN|53,80,443|VLAN10 -> WAN (DNS+HTTP(S) sortant)|0"

    "opt1|allow|tcp|host_reverse_proxy||host_ubuntu_web|80,443|Reverse proxy -> Web metier|1"

    "opt2|allow|any|net_vlan30||host_win_server|53|VLAN30 -> AD DNS|0"
    "opt2|allow|tcp|net_vlan30||host_wazuh|1514,1515|VLAN30 -> Wazuh (logs)|1"

    # === Administration : seul le bastion SSH vers les serveurs ===
    "opt3|allow|tcp|host_bastion||net_vlan30|22|Bastion -> SSH serveurs critiques|1"
    "opt3|block|any|net_vlan99||net_vlan30||Block Wazuh->VLAN30 (seul bastion admin)|1"
    "opt3|allow|udp|net_vlan99||WAN|123|Admin -> NTP|0"
    "opt3|allow|tcp|net_vlan99||WAN|80,443|Admin -> MAJ Wazuh/Elastic|0"

    # === Flux entrant WAN (services publics) ===
    "wan|allow|udp|any||host_vpn|443|WAN -> VPN (WireGuard/OpenVPN)|1"
    "wan|allow|tcp|any||host_reverse_proxy|443|WAN -> Reverse proxy public|1"
    "wan|block|any|any||net_vlan30||Block WAN -> VLAN30|1"
    "wan|block|any|any||net_vlan99||Block WAN -> VLAN99|1"

    # === Logs SIEM (toutes zones vers Wazuh) ===
    "lan|allow|udp|net_vlan10||host_wazuh|514|VLAN10 -> Wazuh syslog|1"
    "opt1|allow|udp|net_vlan20||host_wazuh|514|VLAN20 -> Wazuh syslog|1"

    # === Règle finale : block all + log (default-deny explicite) ===
    "lan|block|any|any||any||Default deny VLAN10|1"
    "opt1|block|any|any||any||Default deny VLAN20|1"
    "opt2|block|any|any||any||Default deny VLAN30|1"
    "opt3|block|any|any||any||Default deny VLAN99|1"
    "wan|block|any|any||any||Default deny WAN|1"
)

log "=== Application des règles de pare-feu (default-deny) ==="

# --- 1. Création des alias réseau ---
log "Création des alias réseau..."
for alias_name in "${!ALIASES[@]}"; do
    alias_val="${ALIASES[$alias_name]}"
    payload=$(cat <<EOF
{"alias": {"name": "${alias_name}", "type": "network", "content": "${alias_val}", "descr": "Alias ${alias_name}"}}
EOF
)
    api_post "firewall/alias/addItem" "$payload" >/dev/null 2>&1 || true
    log "  alias ${alias_name} = ${alias_val}"
done
api_post "firewall/alias/reconfigure" >/dev/null 2>&1 || true

# --- 2. Application des règles ---
log "Application des règles de filtrage..."
rule_count=0
for rule in "${FIREWALL_RULES[@]}"; do
    IFS='|' read -r interface action protocol source src_port destination dst_port descr log_flag <<< "$rule"

    # Construction du payload JSON
    src_port_json="${src_port:+\"${src_port}\"}"
    dst_port_json="${dst_port:+\"${dst_port}\"}"
    [[ -z "$src_port" ]] && src_port_json="null"
    [[ -z "$dst_port" ]] && dst_port_json="null"

    payload=$(cat <<EOF
{
    "rule": {
        "interface": "${interface}",
        "action": "${action}",
        "protocol": "${protocol}",
        "source": "${source}",
        "source_port": ${src_port_json},
        "destination": "${destination}",
        "destination_port": ${dst_port_json},
        "descr": "${descr}",
        "log": "${log_flag}"
    }
}
EOF
)
    api_post "firewall/filter/addRule" "$payload" >/dev/null 2>&1 || true
    rule_count=$((rule_count + 1))
done
log "${rule_count} règles appliquées."

# --- 3. Application des changements ---
log "Rechargement du filtre..."
api_post "firewall/filter/reconfigure" >/dev/null 2>&1 || true
api_post "firewall/filter/apply" >/dev/null 2>&1 || true

log "=== Règles de pare-feu appliquées (default-deny) ==="
log "Vérification : System -> Firewall -> Rules sur l'interface web OPNsense"
log "Prochaine étape : bash 03-nat-gateway.sh"
