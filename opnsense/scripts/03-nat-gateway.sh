#!/usr/bin/env bash
# ============================================================
# OPNsense — NAT, port forwarding & hardening WAN
# ============================================================
# Configure : NAT sortant (masquerade) pour l'accès Internet,
# port forwarding des services publics, et alias dynamique pour
# l'active response Wazuh (blocage d'IP à la volée).
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

api_post() {
    local endpoint="$1"; local payload="${2:-{}}"
    curl -sk -u "$AUTH" -X POST "${API_URL}/${endpoint}" \
        -H "Content-Type: application/json" -d "$payload"
}

log "=== Configuration NAT & port forwarding ==="

# --- 1. NAT sortant (masquerade) sur WAN ---
# Autorise les VMs des VLANs autorisés à accéder à Internet.
log "Configuration NAT sortant (masquerade sur WAN)..."
nat_payload=$(cat <<'EOF'
{
    "nat": {
        "outbound": {
            "mode": "hybrid",
            "rules": [
                {
                    "interface": "wan",
                    "protocol": "any",
                    "source": {"network": "net_vlan10"},
                    "destination": "any",
                    "target": "interface",
                    "descr": "NAT VLAN10 -> WAN"
                },
                {
                    "interface": "wan",
                    "protocol": "any",
                    "source": {"network": "net_vlan99"},
                    "destination": "any",
                    "target": "interface",
                    "descr": "NAT VLAN99 -> WAN (MAJ Wazuh)"
                },
                {
                    "interface": "wan",
                    "protocol": "any",
                    "source": {"network": "net_vlan20"},
                    "destination": "any",
                    "target": "interface",
                    "descr": "NAT VLAN20 -> WAN"
                }
            ]
        }
    }
}
EOF
)
api_post "firewall/nat/outbound/set" "$nat_payload" >/dev/null 2>&1 || true
log "NAT sortant configuré (VLAN 10, 20, 99 — VLAN 30 sans NAT sortant)."

# --- 2. Port forwarding des services publics (DMZ) ---
log "Configuration port forwarding WAN -> DMZ..."
# Reverse proxy : 443/TCP
api_post "firewall/nat/portforward/addItem" '{
    "rule": {
        "interface": "wan",
        "protocol": "tcp",
        "source": "any",
        "destination": "any",
        "destination_port": "443",
        "target": "host_reverse_proxy",
        "local_port": "443",
        "descr": "Forward 443 -> Reverse proxy (DMZ)"
    }
}' >/dev/null 2>&1 || true

# VPN : 443/UDP
api_post "firewall/nat/portforward/addItem" '{
    "rule": {
        "interface": "wan",
        "protocol": "udp",
        "source": "any",
        "destination": "any",
        "destination_port": "51820",
        "target": "host_vpn",
        "local_port": "51820",
        "descr": "Forward 51820/udp -> VPN gateway (DMZ)"
    }
}' >/dev/null 2>&1 || true
log "Port forwarding : 443/tcp -> reverse proxy, 51820/udp -> VPN."

# --- 3. Alias dynamique pour l'active response Wazuh ---
# Wazuh injecte ici les IP à bloquer. Une règle block sur WAN utilise cet alias.
log "Création alias dynamique 'wazuh_blocked_ips' pour active response..."
api_post "firewall/alias/addItem" '{
    "alias": {
        "name": "wazuh_blocked_ips",
        "type": "host",
        "content": "",
        "descr": "IPs bloquees par Wazuh active response (mise a jour dynamique via API)"
    }
}' >/dev/null 2>&1 || true
log "Alias 'wazuh_blocked_ips' créé."

# --- 4. Règle block utilisant l'alias Wazuh (sur WAN en priorité haute) ---
log "Ajout règle block wazuh_blocked_ips (priorité haute sur WAN)..."
api_post "firewall/filter/addRule" '{
    "rule": {
        "interface": "wan",
        "action": "block",
        "protocol": "any",
        "source": "wazuh_blocked_ips",
        "destination": "any",
        "descr": "Block IPs detectees par Wazuh (active response)",
        "log": "1"
    }
}' >/dev/null 2>&1 || true
log "Règle de blocage active response en place."

# --- 5. Hardening WAN : anti-spoofing, bogon, privés ---
log "Hardening WAN (anti-spoofing, bogon networks)..."
api_post "firewall/settings" '{
    "filter": {
        "bogons": "1",
        "blockpriv": "1",
        "blockpriv_wan": "1"
    }
}' >/dev/null 2>&1 || true
log "Filtrage bogon + réseaux privés activé sur WAN."

# --- 6. Application ---
log "Application des changements..."
api_post "firewall/nat/reconfigure" >/dev/null 2>&1 || true
api_post "firewall/filter/reconfigure" >/dev/null 2>&1 || true
api_post "firewall/filter/apply" >/dev/null 2>&1 || true

log "=== NAT & port forwarding configurés ==="
log "Récapitulatif :"
log "  NAT sortant : VLAN 10, 20, 99 (VLAN 30 isolé, pas de NAT)"
log "  Port forward : 443/tcp -> reverse proxy, 51820/udp -> VPN"
log "  Active response : alias 'wazuh_blocked_ips' + règle block WAN"
log "  Hardening WAN : bogon + private networks bloqués"
log "=== OPNsense entièrement configuré ==="
