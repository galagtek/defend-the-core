# Scénario 1 — Détection SIEM (bruteforce → active response)

## Objectif

Démontrer que le SIEM (Wazuh) détecte une attaque en temps réel et réagit
automatiquement en bloquant l'IP attaquante.

## Pré-requis

- Kali Linux connectée au VLAN 10 (10.10.10.100)
- Wazuh opérationnel (manager + dashboard)
- Agent Wazuh installé sur la cible (reverse proxy DMZ ou serveur Ubuntu)
- Active response configurée (script `block-attacker.sh`)

## Déroulé

### Étape 1 — Annoncer
> « Je vais lancer un bruteforce SSH depuis la machine attaquante (Kali, VLAN 10)
> vers le serveur. Le SIEM doit détecter 5 échecs en 60 secondes et bloquer
> automatiquement l'IP. »

### Étape 2 — Exécuter l'attaque

Sur Kali :
```bash
cd kali-attacker/scripts/attack-scenarios/
sudo bash 02-ssh-bruteforce.sh
```

### Étape 3 — Montrer la détection

Dashboard Wazuh (`https://10.10.99.10:5601`) :
1. Onglet **Security Events**
2. L'alerte **« SSH bruteforce détecté »** (règle 100100) apparaît
3. Niveau : 10 (critique), source IP : 10.10.10.100 (Kali)

### Étape 4 — Montrer la réaction

1. Onglet **Active Response** : le script `block-attacker.sh` a été exécuté
2. Sur OPNsense : **Firewall → Aliases → wazuh_blocked_ips** contient désormais
   `10.10.10.100`
3. La règle de pare-feu block correspondante bloque cette IP

### Étape 5 — Vérifier le blocage

Depuis Kali, tenter une nouvelle connexion :
```bash
ssh webadmin@10.10.20.10
# Connection timed out (l'IP est bloquée)
```

## Argument à développer

> « La détection est AUTOMATIQUE et la réaction IMMÉDIATE. Aucune intervention
> humaine n'est nécessaire. L'IP est bloquée pour 1 heure (timeout configurable).
> Wazuh corrèle les logs de toutes les VMs, pas seulement SSH : scan Nmap,
> mouvement latéral, modification de configuration… »

## Règles Wazuh concernées

| Règle | Niveau | Déclencheur |
|-------|--------|-------------|
| 100100 | 10 | 5 échecs SSH en 60s (même IP) |
| 100101 | 12 | 10 échecs SSH en 120s (critique) |
| 100200 | 10 | 15 paquets bloqués en 60s (scan) |
| 100201 | 12 | 30 drops en 30s (scan Nmap SYN) |
