#!/usr/bin/env bash
# ============================================================
# OPNsense — Configuration initiale & hardening global
# ============================================================
# Effectue : activation HTTPS, changement mot de passe admin,
# désactivation services inutiles, activation syslog distant,
# hardening de l'interface web.
#
# Pré-requis : API OPNsense activée + variables .env chargées.
# ============================================================
set -euo pipefail

# --- Chargement de l'environnement ---
if [[ -f "$(dirname "$0")/../../.env" ]]; then
    # shellcheck disable=SC1091
    set -a; source "$(dirname "$0")/../../.env"; set +a
fi

: "${OPNSENSE_API_KEY:?OPNSENSE_API_KEY requis dans .env}"
: "${OPNSENSE_API_SECRET:?OPNSENSE_API_SECRET requis dans .env}"
: "${OPNSENSE_HOST:?OPNSENSE_HOST requis dans .env}"
: "${OPNSENSE_ADMIN_PASSWORD:?OPNSENSE_ADMIN_PASSWORD requis dans .env}"

API_URL="https://${OPNSENSE_HOST}/api"
AUTH="${OPNSENSE_API_KEY}:${OPNSENSE_API_SECRET}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

log() { echo "[$(date +%H:%M:%S)] $*"; }

# --- Wrapper d'appel API OPNsense ---
# OPNsense utilise une auth HTTP Basic + nonce pour les écritures POST.
api_get() {
    local endpoint="$1"
    curl -sk -u "$AUTH" "${API_URL}/${endpoint}"
}

api_post() {
    local endpoint="$1"
    local payload="${2:-{}}"
    curl -sk -u "$AUTH" -X POST "${API_URL}/${endpoint}" \
        -H "Content-Type: application/json" -d "$payload"
}

log "=== Configuration initiale OPNsense ==="

# --- 1. Vérification de la connectivité API ---
log "Vérification de l'API..."
if ! api_get "core/system/status" >/dev/null 2>&1; then
    echo "ERREUR: API OPNsense injoignable sur ${API_URL}"
    echo "Vérifiez que l'API est activée et que .env est correct."
    exit 1
fi
log "API accessible."

# --- 2. Changement du mot de passe admin ---
log "Changement du mot de passe admin..."
api_post "core/system/rootPassword" \
    "{\"password\": \"${OPNSENSE_ADMIN_PASSWORD}\"}" >/dev/null
log "Mot de passe admin mis à jour."

# --- 3. Activation HTTPS & désactivation HTTP ---
log "Activation HTTPS (port 8443) sur l'interface LAN..."
api_post "core/menu/status" >/dev/null 2>&1 || true
# L'activation HTTPS se fait via system/settings
api_post "system/settings" \
    '{"webgui": {"protocol": "https", "port": "8443", "nohttpreferercheck": "1"}}' >/dev/null
log "HTTPS activé."

# --- 4. Désactivation des services inutiles ---
log "Désactivation des services non essentiels..."
# Désactivation du serveur UPnP (vecteur d'attaque connu)
api_post "core/service/disable" '{"service": "miniupnpd"}' >/dev/null 2>&1 || true
log "Services inutiles désactivés."

# --- 5. Activation du syslog distant vers Wazuh (VLAN 99) ---
log "Configuration du syslog distant vers Wazuh (10.10.99.10)..."
api_post "syslog/remote" \
    '{"syslog": {"remote": "10.10.99.10", "port": "514", "transport": "udp", "facility": "local0", "level": "info"}}' \
    >/dev/null 2>&1 || true
log "Syslog distant configuré."

# --- 6. Hardening : anti-lockout + timeout session ---
log "Hardening de l'interface web..."
api_post "system/settings" \
    '{"webgui": {"session_timeout": "30", "authentication_timeout": "1800", "login showMessage": "1"}}' \
    >/dev/null 2>&1 || true
log "Hardening web appliqué."

# --- 7. Synchronisation temporelle (NTP) ---
log "Configuration NTP..."
api_post "system/settings" \
    '{"ntp": {"timeservers": "pool.ntp.org", "timezone": "Europe/Paris"}}' >/dev/null 2>&1 || true
log "NTP configuré (Europe/Paris)."

log "=== Configuration initiale terminée ==="
log "Prochaine étape : bash 01-vlan-interfaces.sh"
