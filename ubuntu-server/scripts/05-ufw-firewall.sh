#!/usr/bin/env bash
# ============================================================
# Ubuntu Server — Pare-feu UFW (défense en profondeur)
# ============================================================
# Même si OPNsense filtre déjà, UFW ajoute une couche locale.
# Règle : default deny, seuls les flux nécessaires sont autorisés.
# ============================================================
set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }
[[ "$(id -u)" -eq 0 ]] || { echo "Exécuter en root (sudo)"; exit 1; }

log "=== Configuration pare-feu UFW ==="

# --- 1. Reset ---
ufw --force reset

# --- 2. Politique par défaut : deny ---
ufw default deny incoming
ufw default allow outgoing

# --- 3. Règles ---
# SSH : uniquement depuis le bastion (10.10.99.20)
log "Autorisation SSH uniquement depuis le bastion (10.10.99.20)..."
ufw allow from 10.10.99.20 to any port 22 proto tcp comment 'Bastion SSH'

# HTTP/HTTPS : uniquement depuis le reverse proxy DMZ (10.10.20.10)
log "Autorisation HTTP/HTTPS uniquement depuis le reverse proxy (10.10.20.10)..."
ufw allow from 10.10.20.10 to any port 80 proto tcp comment 'Reverse proxy HTTP'
ufw allow from 10.10.20.10 to any port 443 proto tcp comment 'Reverse proxy HTTPS'

# DNS : depuis le Windows Server AD (10.10.30.20)
log "Autorisation DNS vers l'AD (10.10.30.20)..."
# (le serveur interroge l'AD pour la résolution, c'est du sortant — déjà allow)

# Wazuh : flux de logs sortant vers le SIEM (déjà allow par défaut outgoing)
# Mais on explicite pour la documentation
log "Flux logs vers Wazuh (10.10.99.10:1514) — sortant autorisé par défaut."

# PostgreSQL : accès local uniquement (pas d'écoute réseau)
# (déjà configuré dans 01-web-stack.sh : listen_addresses = localhost)

# --- 4. Logging ---
ufw logging on
ufw logging medium

# --- 5. Activation ---
log "Activation UFW..."
ufw --force enable

# --- 6. Affichage du statut ---
log "Statut UFW :"
ufw status verbose

log "=== Pare-feu UFW configuré (défense en profondeur) ==="
log "Récapitulatif :"
log "  - Default : deny incoming / allow outgoing"
log "  - SSH (22/tcp) : uniquement depuis 10.10.99.20 (bastion)"
log "  - HTTP (80/tcp) : uniquement depuis 10.10.20.10 (reverse proxy)"
log "  - HTTPS (443/tcp) : uniquement depuis 10.10.20.10 (reverse proxy)"
log "Prochaine étape : bash 06-cis-hardening.sh"
