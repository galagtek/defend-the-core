# Kali Linux — Machine attaquant (Zone Bureautique)

## Rôle

Simule l'**attaquant** pour les démonstrations de l'entretien. Placée sur le
VLAN 10 (10.10.10.100), elle tente d'attaquer l'infrastructure pour démontrer
que la détection (Wazuh) et la segmentation (OPNsense) fonctionnent.

## Pré-requis

- VM Kali Linux (2 vCPU, 4 Go RAM, 30 Go disque)
- Réseau interne VirtualBox `vbox-vlan10`
- IP statique : 10.10.10.100 ou DHCP

## Scripts

| Script | Description |
|--------|-------------|
| `setup-kali.sh` | Configuration réseau VLAN 10 + outils |
| `attack-scenarios/01-nmap-recon.sh` | Scan Nmap (démo détection SIEM) |
| `attack-scenarios/02-ssh-bruteforce.sh` | Bruteforce SSH (démo active response) |
| `attack-scenarios/03-lateral-movement.sh` | Tentative mouvement latéral (démo segmentation) |

## Important — usage éthique

> ⚠️ Ces scripts sont conçus UNIQUEMENT pour démontrer l'efficacité des défenses
> dans un environnement de laboratoire contrôlé (votre VirtualBox). Ne JAMAIS
> les utiliser contre des systèmes que vous ne possédez pas ou sans autorisation.

## Scénarios de démonstration

Voir le dossier [`demos/`](../demos/) pour le déroulé complet de chaque scénario
de validation à présenter en entretien.
