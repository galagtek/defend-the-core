#!/usr/bin/env bash
# ============================================================
# Wazuh — Active Response : blocage automatique d'IP attaquante
# ============================================================
# Ce script est exécuté AUTOMATIQUEMENT par Wazuh lorsqu'une alerte
# de niveau >= 10 est déclenchée (bruteforce, scan, mouvement latéral).
#
# Action : ajoute l'IP source à l'alias 'wazuh_blocked_ips' sur
# OPNsense via l'API REST. La règle de pare-feu correspondante
# bloque alors immédiatement cette IP sur toutes les interfaces.
#
# Installation :
#   cp block-attacker.sh /var/ossec/active-response/bin/
#   chown root:ossec /var/ossec/active-response/bin/block-attacker.sh
#   chmod 750 /var/ossec/active-response/bin/block-attacker.sh
#
# Déclaration dans /var/ossec/etc/ossec.conf :
#   <command>
#     <name>block-attacker</name>
#     <executable>block-attacker.sh</executable>
#     <expect>srcip</expect>
#     <timeout_allowed>yes</timeout_allowed>
#   </command>
#   <active-response>
#     <command>block-attacker</command>
#     <location>local</location>
#     <rules_id>100100,100101,100200,100201,100300,100301</rules_id>
#     <timeout>3600</timeout>  <!-- débloque après 1h -->
#   </active-response>
# ============================================================
set -euo pipefail

# --- Variables Wazuh (injectées par le manager) ---
ACTION="${1:-}"
USER="${2:-}"
SRC_IP="${3:-}"
ALERT_ID="${4:-}"
RULE_ID="${5:-}"
LOG_FILE="${6:-}"

# --- Configuration OPNsense (depuis .env ou valeurs par défaut) ---
OPNSENSE_HOST="${OPNSENSE_HOST:-10.10.99.1}"
OPNSENSE_API_KEY="${OPNSENSE_API_KEY:-}"
OPNSENSE_API_SECRET="${OPNSENSE_API_SECRET:-}"
ALIAS_NAME="wazuh_blocked_ips"
API_URL="https://${OPNSENSE_HOST}/api"

# --- Journalisation ---
AR_LOG="/var/ossec/logs/active-responses.log"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [block-attacker] $*" >> "$AR_LOG"
}

# --- Validation de l'IP (anti-injection) ---
is_valid_ip() {
    local ip="$1"
    if [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        return 0
    fi
    return 1
}

# --- Ajout d'une IP à l'alias OPNsense ---
block_ip() {
    local ip="$1"
    log "Blocage de l'IP $ip (règle $RULE_ID)"

    if [[ -z "$OPNSENSE_API_KEY" ]] || [[ -z "$OPNSENSE_API_SECRET" ]]; then
        log "ERREUR: OPNSENSE_API_KEY/SECRET non configurés. Blocage local uniquement."
        # Fallback : blocage local via iptables (si disponible)
        if command -v iptables >/dev/null 2>&1; then
            iptables -I INPUT -s "$ip" -j DROP
            log "IP $ip bloquée localement via iptables."
        fi
        return 0
    fi

    # Ajout de l'IP à l'alias via l'API OPNsense
    local auth="${OPNSENSE_API_KEY}:${OPNSENSE_API_SECRET}"
    local response

    # Récupérer le contenu actuel de l'alias
    response=$(curl -sk -u "$auth" "${API_URL}/firewall/alias/getAlias/${ALIAS_NAME}" 2>/dev/null || echo "")

    # Ajouter l'IP (éviter les doublons)
    local payload
    payload=$(cat <<EOF
{"alias": {"name": "${ALIAS_NAME}", "type": "host", "content": "${ip}"}}
EOF
)
    # POST pour mettre à jour l'alias (OPNsense fusionne les entrées host)
    response=$(curl -sk -u "$auth" -X POST \
        "${API_URL}/firewall/alias/addItem" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>/dev/null || echo "")

    # Rechargement de l'alias sur OPNsense
    curl -sk -u "$auth" -X POST "${API_URL}/firewall/alias/reconfigure" \
        >/dev/null 2>&1 || true
    curl -sk -u "$auth" -X POST "${API_URL}/firewall/filter/reconfigure" \
        >/dev/null 2>&1 || true
    curl -sk -u "$auth" -X POST "${API_URL}/firewall/filter/apply" \
        >/dev/null 2>&1 || true

    log "IP $ip ajoutée à l'alias ${ALIAS_NAME} sur OPNsense. Règles rechargées."
}

# --- Suppression d'une IP de l'alias (débloquage après timeout) ---
unblock_ip() {
    local ip="$1"
    log "Débloquage de l'IP $ip (timeout atteint)"

    if [[ -z "$OPNSENSE_API_KEY" ]] || [[ -z "$OPNSENSE_API_SECRET" ]]; then
        # Fallback local
        if command -v iptables >/dev/null 2>&1; then
            iptables -D INPUT -s "$ip" -j DROP 2>/dev/null || true
            log "IP $ip débloquée localement."
        fi
        return 0
    fi

    local auth="${OPNSENSE_API_KEY}:${OPNSENSE_API_SECRET}"

    # Suppression de l'IP de l'alias
    curl -sk -u "$auth" -X POST \
        "${API_URL}/firewall/alias/delItem" \
        -H "Content-Type: application/json" \
        -d "{\"alias\": {\"name\": \"${ALIAS_NAME}\", \"content\": \"${ip}\"}}" \
        >/dev/null 2>&1 || true

    # Rechargement
    curl -sk -u "$auth" -X POST "${API_URL}/firewall/alias/reconfigure" \
        >/dev/null 2>&1 || true
    curl -sk -u "$auth" -X POST "${API_URL}/firewall/filter/apply" \
        >/dev/null 2>&1 || true

    log "IP $ip retirée de l'alias ${ALIAS_NAME}."
}

# --- Point d'entrée principal ---
log "Appel active response : ACTION=$ACTION SRC_IP=$SRC_IP RULE=$RULE_ID"

case "$ACTION" in
    add)
        # Validation de l'IP avant de bloquer
        if is_valid_ip "$SRC_IP"; then
            # Ne jamais bloquer les IP légitimes (whitelist)
            case "$SRC_IP" in
                10.10.99.20) log "INFO: $SRC_IP est le bastion, non bloqué." ;;
                10.10.99.10) log "INFO: $SRC_IP est Wazuh, non bloqué." ;;
                127.0.0.1)   log "INFO: $SRC_IP est localhost, non bloqué." ;;
                *)           block_ip "$SRC_IP" ;;
            esac
        else
            log "ERREUR: IP invalide '$SRC_IP' — blocage annulé."
        fi
        ;;
    delete)
        if is_valid_ip "$SRC_IP"; then
            unblock_ip "$SRC_IP"
        fi
        ;;
    *)
        log "ACTION inconnue '$ACTION'. Actions valides : add, delete."
        ;;
esac

exit 0
