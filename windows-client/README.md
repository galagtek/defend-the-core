# Windows 10 — Poste employé (Zone Bureautique)

## Rôle

Poste utilisateur standard sur le **VLAN 10** (10.10.10.50). Simule un employé
classique de la PME. C'est le **vecteur d'attaque principal** (phishing, malware).

## Pré-requis

- VM Windows 10/11 (2 vCPU, 4 Go RAM, 40 Go disque)
- Réseau interne VirtualBox `vbox-vlan10`
- IP via DHCP (10.10.10.x) ou statique 10.10.10.50

## Scripts

| Script | Description |
|--------|-------------|
| `Install-WazuhAgent.ps1` | Déploiement agent Wazuh (surveillance du poste) |
| `Harden-Win10.ps1` | Durcissement base + Windows Defender + pare-feu |

## Objectif pour l'entretien

Ce poste sert à démontrer le **scénario 2 (Zéro Trust)** : depuis Win10 (VLAN 10),
tenter de pinguer le VLAN 30 ou le VLAN 99 doit échouer (default-deny OPNsense).

L'agent Wazuh surveille ce poste : toute activité suspecte (malware, anomalie)
remonte au SIEM.
