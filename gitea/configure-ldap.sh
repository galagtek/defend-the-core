#!/usr/bin/env bash
# ============================================================
# Gitea — Configuration de l'authentification LDAP (AD)
# ============================================================
# Configure Gitea pour authentifier les utilisateurs via
# l'Active Directory (10.10.50.20) en LDAPS.
#
# Le compte de service svc_gitea_auth doit exister dans l'AD
# avec des droits de lecture sur l'OU des utilisateurs.
# ============================================================
set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }

# --- Variables à adapter ---
AD_SERVER="10.10.50.20"
AD_PORT="636"
AD_DOMAIN="defendcore.internal"
AD_BIND_DN="svc_gitea_auth@${AD_DOMAIN}"
AD_BIND_PASSWORD="${1:-CHANGEZ_MOI}"
AD_SEARCH_BASE="DC=defendcore,DC=internal"

log "=== Configuration LDAP pour Gitea ==="
log "Serveur AD : ${AD_SERVER}:${AD_PORT}"
log "Compte de service : ${AD_BIND_DN}"
log "Base de recherche : ${AD_SEARCH_BASE}"
log ""
log "⚠️  Cette configuration se fait via l'interface web Gitea :"
log "    Administration → Authentication Sources → Add Source"
log ""
log "Paramètres à saisir :"
log ""
log "  Name:               AD-LDAPS"
log "  Type:               LDAP (via BindDN)"
log "  Security Protocol:  LDAPS"
log "  Host:               ${AD_SERVER}:${AD_PORT}"
log "  Bind DN:            ${AD_BIND_DN}"
log "  Bind Password:      (le mot de passe du compte de service)"
log "  User Search Base:   ${AD_SEARCH_BASE}"
log "  User Filter:        (&(objectClass=user)(sAMAccountName=%s)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
log "  Username Attribute: sAMAccountName"
log "  Email Attribute:    mail"
log "  Firstname Attribute:givenName"
log "  Surname Attribute:  sn"
log "  Enable TLS:         coché"
log ""
log "Le filtre user exclut les comptes désactivés (userAccountControl bit 2)."

# --- Test de connexion LDAP ---
log ""
log "=== Test de connexion LDAP ==="
if command -v ldapsearch >/dev/null 2>&1; then
    log "Test de bind LDAPS..."
    ldapsearch -x -H "ldaps://${AD_SERVER}:${AD_PORT}" \
        -D "${AD_BIND_DN}" -w "${AD_BIND_PASSWORD}" \
        -b "${AD_SEARCH_BASE}" "(sAMAccountName=Administrator)" dn 2>&1 | head -10
    log ""
    log "Si vous voyez des résultats, la connexion LDAP fonctionne."
else
    log "ldap-utils non installé. Installez : apt install ldap-utils"
    log "Puis relancez ce script pour tester la connexion."
fi
