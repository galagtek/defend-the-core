#!/usr/bin/env bash
# ============================================================
# Scénario d'attaque 1 — Reconnaissance Nmap
# ============================================================
# Démo : depuis Kali (VLAN 10), scan Nmap du réseau.
#
# Résultat attendu :
#   - Le scan génère de nombreux paquets bloqués par OPNsense
#   - Wazuh détecte le pattern (règle 100200/100201)
#   - Active response : l'IP de Kali est bloquée automatiquement
#
# Usage : sudo bash 01-nmap-recon.sh
# ============================================================
set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }

KALI_IP="10.10.10.100"

log "============================================================"
log "  SCENARIO 1 : Reconnaissance Nmap"
log "  Source : Kali ($KALI_IP, VLAN 10)"
log "============================================================"
log ""
log "Ce scan va tenter de découvrir les hôtes et services du réseau."
log "OPNsense doit bloquer les flux interdits, et Wazuh détecter le scan."
log ""

read -rp "Lancer le scan ? (oui/non) : " confirm
[[ "$confirm" =~ ^[oO]ui$ ]] || { echo "Annulé."; exit 0; }

# --- Scan 1 : découverte d'hôtes sur le VLAN 30 (interdit) ---
log "[1/3] Scan de découverte du VLAN 30 (10.10.30.0/24)..."
log "     (OPNsense doit bloquer — le VLAN 10 ne peut pas joindre le VLAN 30)"
nmap -sn 10.10.30.0/24 -T4 2>&1 | head -20 || true
log ""

# --- Scan 2 : scan de ports sur le reverse proxy DMZ (autorisé 80/443) ---
log "[2/3] Scan de ports du reverse proxy DMZ (10.10.20.10)..."
log "     (OPNsense autorise 80/443, bloque le reste)"
nmap -sS -p 1-1000 10.10.20.10 -T4 2>&1 | head -30 || true
log ""

# --- Scan 3 : scan intensif (déclenche l'active response) ---
log "[3/3] Scan intensif SYN du VLAN 20 (10.10.20.0/24)..."
log "     (Doit déclencher la détection Wazuh + blocage active response)"
nmap -sS -p 1-1000 10.10.20.0/24 -T4 --min-rate 100 2>&1 | head -30 || true
log ""

log "============================================================"
log "  Vérifications :"
log "  1. Dashboard Wazuh : alerte 'Scan réseau détecté' (règle 100200)"
log "  2. OPNsense : Firewall > Log Files > paquets bloqués"
log "  3. Active response : Kali ($KALI_IP) bloqué dans l'alias"
log "     wazuh_blocked_ips sur OPNsense"
log "============================================================"
log ""
log "⚠️ Après ce scan, votre IP est probablement bloquée (active response)."
log "   Pour la débloquer : retirer 10.10.10.100 de l'alias sur OPNsense."
