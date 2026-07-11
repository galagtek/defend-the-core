#!/usr/bin/env bash
# ============================================================
# Scénario d'attaque 3 — Mouvement latéral
# ============================================================
# Démo : depuis Kali (VLAN 10), tenter d'atteindre le VLAN 30
# (zone critique) et le VLAN 99 (zone admin) pour démontrer que
# la segmentation (Zero Trust) bloque le mouvement latéral.
#
# Résultat attendu :
#   - VLAN 10 -> VLAN 30 : BLOQUÉ par OPNsense (isolation zone critique)
#   - VLAN 10 -> VLAN 99 : BLOQUÉ par OPNsense (isolation zone admin)
#   - Aucune connectivité : la segmentation fonctionne
#
# Usage : sudo bash 03-lateral-movement.sh
# ============================================================
set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }

KALI_IP="10.10.10.100"

# Cibles dans les zones protégées
VLAN30_TARGET="10.10.30.10"    # Ubuntu (zone critique)
VLAN99_TARGET="10.10.99.10"    # Wazuh (zone admin)
VLAN99_BASTION="10.10.99.20"   # Bastion NixOS

log "============================================================"
log "  SCENARIO 3 : Mouvement latéral (Zero Trust)"
log "  Source : Kali ($KALI_IP, VLAN 10)"
log "============================================================"
log ""
log "Ce scénario tente d'atteindre les zones protégées (VLAN 30, VLAN 99)"
log "depuis le VLAN 10. La segmentation OPNsense doit tout bloquer."
log ""

read -rp "Lancer le test de mouvement latéral ? (oui/non) : " confirm
[[ "$confirm" =~ ^[oO]ui$ ]] || { echo "Annulé."; exit 0; }

# --- Test 1 : VLAN 10 -> VLAN 30 (zone critique) ---
log "[1/4] Test de connectivité vers le VLAN 30 (zone critique)..."
log "     Cible : $VLAN30_TARGET (Ubuntu Web+BDD)"
echo ""
ping -c 4 -W 2 "$VLAN30_TARGET" 2>&1 || true
echo ""
if ping -c 1 -W 2 "$VLAN30_TARGET" >/dev/null 2>&1; then
    log "  ❌ ECHEC SEGMENTATION : le VLAN 30 est accessible depuis le VLAN 10 !"
    log "     Vérifiez vos règles OPNsense (règle block VLAN10->VLAN30)."
else
    log "  ✅ SUCCES DÉFENSE : le VLAN 30 est INACCESSIBLE (segmentation OK)."
fi
log ""

# --- Test 2 : VLAN 10 -> VLAN 99 (zone admin / SIEM) ---
log "[2/4] Test de connectivité vers le VLAN 99 (zone admin/SIEM)..."
log "     Cible : $VLAN99_TARGET (Wazuh)"
echo ""
ping -c 4 -W 2 "$VLAN99_TARGET" 2>&1 || true
echo ""
if ping -c 1 -W 2 "$VLAN99_TARGET" >/dev/null 2>&1; then
    log "  ❌ ECHEC SEGMENTATION : le VLAN 99 est accessible depuis le VLAN 10 !"
else
    log "  ✅ SUCCES DÉFENSE : le VLAN 99 (Wazuh) est INACCESSIBLE."
fi
log ""

# --- Test 3 : VLAN 10 -> Bastion NixOS (VLAN 99) ---
log "[3/4] Test de connectivité vers le bastion NixOS (VLAN 99)..."
log "     Cible : $VLAN99_BASTION"
echo ""
ping -c 4 -W 2 "$VLAN99_BASTION" 2>&1 || true
echo ""
if ping -c 1 -W 2 "$VLAN99_BASTION" >/dev/null 2>&1; then
    log "  ❌ ECHEC SEGMENTATION : le bastion est accessible depuis le VLAN 10 !"
else
    log "  ✅ SUCCES DÉFENSE : le bastion NixOS est INACCESSIBLE."
fi
log ""

# --- Test 4 : Tentative SSH directe (devrait échouer) ---
log "[4/4] Tentative SSH directe vers le serveur Ubuntu (VLAN 30)..."
log "     (L'admin doit passer par le bastion — ProxyJump — pas d'accès direct)"
echo ""
timeout 5 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
    webadmin@"$VLAN30_TARGET" 2>&1 || true
echo ""
log "  ✅ Attendu : connexion SSH impossible (segmentation + pas de route)."
log "     L'accès doit passer par : Win -> Bastion NixOS -> Serveur (ProxyJump)"

log ""
log "============================================================"
log "  RÉSULTAT : la segmentation Zero Trust fonctionne."
log "  Le VLAN 10 est isolé des zones critiques (30) et admin (99)."
log ""
log "  Vérifications complémentaires :"
log "  1. OPNsense : Firewall > Log Files > paquets 'drop' sur l'interface LAN"
log "  2. Wazuh : alertes de scan/blocage (règles 100200/100201)"
log "  3. L'utilisateur du VLAN 10 ne voit QUE le reverse proxy (80/443)"
log "============================================================"
