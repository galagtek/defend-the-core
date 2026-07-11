# Wazuh — SIEM / XDR

## Rôle

Wazuh est le **cœur de surveillance** de l'infrastructure. Il collecte les logs de
toutes les VMs, corrèle les événements, génère des alertes et peut **réagir
automatiquement** (active response) en bloquant une IP malveillante.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Wazuh Manager (VLAN 99)               │
│                  10.10.99.10  (Ubuntu 26.04)            │
│                                                          │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────┐ │
│  │  Wazuh   │  │ Indexer   │  │  Dashboard (Kibana)  │ │
│  │ Manager  │  │ (Elastic) │  │   UI 5601 / 443      │ │
│  └────┬─────┘  └─────┬─────┘  └──────────┬───────────┘ │
│       │              │                    │             │
│       │   Corrélation │  Stockage          │  Visualisation│
│       │   règles      │  index             │  dashboards   │
│       └──────────────┴────────────────────┘             │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │          Active Response (blocage IP)            │   │
│  │  → API OPNsense → alias wazuh_blocked_ips        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
        ▲            ▲            ▲            ▲
        │ logs 514   │ logs 1514  │ logs 1514  │ agent
        │            │            │            │
   ┌────┴────┐  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐
   │ OPNsense│  │ Ubuntu  │  │ Win Srv │  │ Win10   │
   │ VLAN all│  │ VLAN 30 │  │ VLAN 30 │  │ VLAN 10 │
   └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

## Pré-requis

- VM Ubuntu 26.04 LTS (8 Go RAM min, 4 vCPU, 50 Go disque)
- Sur le réseau interne VirtualBox `vbox-vlan99` (IP 10.10.99.10)
- Accès Internet (pour télécharger les paquets) via OPNsense NAT

## Installation

```bash
# Sur la VM Wazuh (Ubuntu 26.04, VLAN 99)
export WAZUH_ADMIN_PASSWORD="votre_mot_de_passe_fort"  # cf. .env
sudo bash install/install-wazuh-manager.sh
```

Le script installe :
- **Wazuh Indexer** (Elasticsearch fork) — stockage des événements
- **Wazuh Manager** — corrélation, règles, active response
- **Wazuh Dashboard** (Kibana fork) — interface de visualisation

> Installation via le script officiel `wazuh-install.sh` (apt repository).

## Déploiement des agents

Chaque VM supervisée reçoit un agent Wazuh :

| Machine | OS | Script |
|---------|----|----|
| Ubuntu Server | Linux | `agents/deploy-agent-linux.sh` |
| Bastion NixOS | Linux | `agents/deploy-agent-linux.sh` |
| Kali | Linux | `agents/deploy-agent-linux.sh` |
| Windows Server | Windows | `agents/deploy-agent-windows.ps1` |
| Windows 10 | Windows | `agents/deploy-agent-windows.ps1` |

```bash
# Sur un hôte Linux supervisé
sudo WAZUH_MANAGER_IP=10.10.99.10 bash agents/deploy-agent-linux.sh
```

## Règles de corrélation personnalisées

Les règles par défaut de Wazuh couvrent de nombreux cas. Nous ajoutons des règles
métier dans `rules/custom-rules.xml` :

- Détectection de **bruteforce SSH** (seuil 5 échecs / 1 min)
- Détection de **scan Nmap** (règle OPNsense)
- Détection de **mouvement latéral** (connexion SSH inhabituelle)
- Détection de **modification de configuration** (auditd)

## Active Response (blocage automatique)

Lorsqu'une alerte critique est déclenchée (ex : bruteforce), Wazuh exécute
automatiquement un script `rules/active-response/block-attacker.sh` qui :

1. Extrait l'IP attaquante de l'alerte
2. L'ajoute à l'alias `wazuh_blocked_ips` sur OPNsense via l'API
3. L'IP est alors bloquée par la règle de pare-feu correspondante

→ **Réaction en temps réel, sans intervention humaine.**

## Accès au dashboard

- URL : `https://10.10.99.10:5601` (ou 443 après reverse proxy)
- Identifiants : définis dans `.env` (`WAZUH_ADMIN_PASSWORD`)

## Dashboards

Les dashboards personnalisés sont exportés en JSON dans `dashboard/` :
- Sécurité SSH (connexions, échecs, origine géographique)
- Alertes OPNsense (blocs, scans)
- Auditd (modifications système)
- Vue d'ensemble (synthèse toutes VMs)
