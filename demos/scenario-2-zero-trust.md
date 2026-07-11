# Scénario 2 — Zero Trust / segmentation

## Objectif

Démontrer que la segmentation réseau (zoning VLAN + default-deny OPNsense) empêche
le mouvement latéral : un poste compromis du VLAN 10 ne peut pas atteindre les
zones critiques (VLAN 30) ni admin (VLAN 99).

## Pré-requis

- Windows 10 (10.10.10.50) ou Kali (10.10.10.100) sur le VLAN 10
- OPNsense configuré avec les règles default-deny

## Déroulé

### Étape 1 — Annoncer
> « Depuis un poste utilisateur du VLAN 10, je vais tenter d'atteindre les
> serveurs critiques (VLAN 30) et la zone d'administration (VLAN 99).
> Aucune de ces destinations ne doit être accessible. »

### Étape 2 — Exécuter les tests

Sur Kali (ou Win10 avec PowerShell) :
```bash
cd kali-attacker/scripts/attack-scenarios/
sudo bash 03-lateral-movement.sh
```

Ou manuellement :
```bash
# Test VLAN 30 (zone critique) — doit échouer
ping -c 4 10.10.30.10

# Test VLAN 99 (zone admin/SIEM) — doit échouer
ping -c 4 10.10.99.10

# Test bastion NixOS — doit échouer
ping -c 4 10.10.99.20
```

### Étape 3 — Montrer les logs OPNsense

Sur OPNsense : **Firewall → Log Files → Normal View**
- Filtre : Action = **Block**
- On voit les paquets du VLAN 10 (10.10.10.x) vers le VLAN 30 et 99 **droppés**

### Étape 4 — Montrer ce qui EST accessible

Depuis le VLAN 10, le seul service autorisé est le reverse proxy (VLAN 20) :
```bash
curl -k https://10.10.20.10    # ✅ Fonctionne (443 autorisé)
ping 10.10.30.10                # ❌ Échec (bloqué)
```

## Argument à développer

> « L'utilisateur du VLAN 10 ne voit QUE ce qu'il doit voir : le reverse proxy
> sur les ports 80/443. Tout le reste est bloqué par défaut. C'est le principe
> du Zero Trust et du cloisonnement ANSSI : même si ce poste est compromis par
> un phishing, l'attaquant ne peut pas se propager vers les serveurs ou la zone
> d'administration. »

## Matrice de flux (rappel)

```
Depuis \ Vers   VLAN10   VLAN20     VLAN30     VLAN99
VLAN 10           —     80/443     BLOQUÉ     BLOQUÉ
VLAN 30           —       —          —        1514 (logs)
VLAN 99           —       —         22 (SSH)    —
```

## Règles OPNsense concernées

| Règle | Action | Source | Destination | Justification |
|-------|--------|--------|-------------|---------------|
| Block | deny | VLAN 10 | VLAN 30 | Isolation zone critique |
| Block | deny | VLAN 10 | VLAN 99 | Isolation zone admin |
| Allow | pass | VLAN 10 | 10.10.20.10:80,443 | Reverse proxy uniquement |
