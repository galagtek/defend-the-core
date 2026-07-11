# 🏗️ Defend-The-Core — Infrastructure PME critique sécurisée

> Projet d'infrastructure réseau segmentée, surveillée et administrée de façon sécurisée,
> conçu selon les recommandations de l'**ANSSI** et présenté en **Infrastructure as Code**.
> Idéal pour démontrer une posture DevSecOps en entretien.

---

## 🎯 Le problème adressé

Dans la plupart des PME, le réseau est « plat » : si un poste utilisateur est compromis
par un phishing, l'attaquant peut se propager latéralement jusqu'aux serveurs de bases
de données. Ce projet répond à ce risque par **trois piliers** :

1. **Zoning & segmentation** — le réseau est découpé en VLANs cloisonnés par un pare-feu
   en *default-deny*. Un poste compromis ne voit que ce qu'il doit voir.
2. **Surveillance & détection** — un SIEM (Wazuh) corrèle les logs de toutes les machines
   et réagit automatiquement (blocage d'IP en temps réel).
3. **Administration sécurisée** — un **bastion NixOS** (PAW) garantit l'immuabilité de la
   configuration : aucune dérive possible, aucune persistance d'un attaquant.

---

## 🗺️ Architecture réseau

```
                            ┌─────────────┐
                            │   Internet  │
                            └──────┬──────┘
                                   │ WAN (NAT VirtualBox)
                          ┌────────┴────────┐
                          │   OPNsense      │  Pare-feu / routeur inter-VLAN
                          │  (default-deny) │  Règles strictes, NAT, DHCP relay
                          └──┬─────┬────┬───┘
             ┌────────────────┘     │    └─────────────────┐
             │                      │                      │
   ┌─────────┴──────────┐ ┌─────────┴──────────┐ ┌─────────┴──────────┐
   │ VLAN 10            │ │ VLAN 20            │ │ VLAN 30            │
   │ ZONE BUREAUTIQUE   │ │ ZONE DMZ           │ │ ZONE CRITIQUE      │
   │ 10.10.10.0/24      │ │ 10.10.20.0/24      │ │ 10.10.30.0/24      │
   │ Non fiable         │ │ Publique           │ │ Serveurs métier    │
   │                    │ │                    │ │                    │
   │ • Win10 (employé)  │ │ • Reverse proxy    │ │ • Ubuntu (Web+BDD) │
   │ • Kali (attaquant) │ │ • VPN gateway      │ │ • Win Server (AD)  │
   └────────────────────┘ └────────────────────┘ └────────────────────┘
                                     │
                          ┌──────────┴──────────┐
                          │ VLAN 99             │
                          │ ZONE ADMIN / SIEM   │
                          │ 10.10.99.0/24       │
                          │ Très restreint      │
                          │                     │
                          │ • Wazuh (SIEM/XDR)  │
                          │ • Bastion NixOS     │
                          └─────────────────────┘
```

Le **plan d'adressage complet** et la **matrice des flux autorisés** sont dans
[`architecture/`](architecture/).

---

## 🧩 Composants & piles techniques

| VM | Rôle | Technologie | VLAN |
|----|------|-------------|------|
| **OPNsense** | Pare-feu / routeur inter-VLAN | OPNsense (API + XML) | tous |
| **Wazuh** | SIEM / XDR, corrélation, active response | Wazuh + Elastic/Kibana | 99 |
| **Bastion** | PAW, administration sécurisée, immuable | NixOS (config déclarative) | 99 |
| **Windows Server** | AD, DNS, DHCP | Windows Server 2022 | 30 |
| **Ubuntu Server** | Serveur Web + BDD | Ubuntu 22.04, Nginx, PostgreSQL | 30 |
| **Windows 10** | Poste employé | Windows 10 + agent Wazuh | 10 |
| **Kali Linux** | Simule l'attaquant | Kali + scénarios d'attaque | 10 |

---

## 📁 Structure du dépôt

```
defend-the-core/
├── architecture/        # Topologie réseau, plan d'adressage, matrice de flux
├── opnsense/            # Scripts de config du pare-feu (API + XML export)
├── wazuh/               # Installation manager, agents, règles, active response
├── bastion-nixos/       # configuration.nix durci (la star du projet)
├── windows-server/      # AD, DNS, DHCP, durcissement, GPO (PowerShell)
├── ubuntu-server/       # Durcissement CIS, auditd, UFW, SSH clés (shell)
├── windows-client/      # Agent Wazuh + durcissement Win10
├── kali-attacker/       # Scénarios d'attaque reproductibles (démos)
├── docs/                # Documentation PDF (maître + annexes par domaine)
├── demos/               # Scénarios de validation pour l'entretien
└── README.md
```

---

## 🚀 Déploiement rapide

Chaque sous-dossier contient son propre `README.md` avec les instructions détaillées.
L'ordre recommandé :

1. **OPNsense** — déployer le pare-feu et le zoning ([`opnsense/`](opnsense/))
2. **Wazuh** — installer le SIEM ([`wazuh/`](wazuh/))
3. **Bastion NixOS** — configurer le PAW ([`bastion-nixos/`](bastion-nixos/))
4. **Serveurs métier** — Ubuntu + Windows Server ([`ubuntu-server/`](ubuntu-server/), [`windows-server/`](windows-server/))
5. **Postes clients** — Win10 + Kali ([`windows-client/`](windows-client/), [`kali-attacker/`](kali-attacker/))

> ⚠️ Aucun secret n'est versionné. Copiez `.env.example` → `.env` et renseignez vos
> valeurs (mots de passe, clés) avant d'exécuter les scripts.

---

## 🎬 Scénarios de démonstration (pour l'entretien)

| # | Scénario | Ce que ça démontre |
|---|----------|--------------------|
| 1 | [Détection SIEM](demos/scenario-1-detection.md) | Bruteforce SSH détecté → IP bloquée automatiquement par active response |
| 2 | [Zéro Trust / segmentation](demos/scenario-2-zero-trust.md) | Win10 ne peut pas pinguer le VLAN 30 ni le VLAN 99 |
| 3 | [Administration sécurisée (PAW)](demos/scenario-3-paw-nixos.md) | SSH via ProxyJump : Win → Bastion NixOS → Serveur ; immuabilité |

---

## 🛡️ Conformité & références

- Recommandations **ANSSI** : zoning, cloisonnement, moindre privilège
- Durcissement **CIS Benchmark** (Ubuntu, Windows Server)
- **Zero Trust** : aucun flux par défaut, authentification forte (clés SSH + FIDO2)
- **Immuabilité** : configuration déclarative NixOS, traçabilité Git

---

## 📄 Documentation

La documentation complète est générée en PDF dans [`docs/`](docs/) :

- `00_architecture_maitre.pdf` — synthèse d'architecture et justification des choix
- `01_reseau_opnsense.pdf` — zoning, VLANs, pare-feu
- `02_securite_wazuh.pdf` — SIEM, détection, active response
- `03_durcissement_serveurs.pdf` — durcissement Linux & Windows
- `04_admin_bastion_nixos.pdf` — PAW, ProxyJump, immuabilité NixOS

---

## 📜 Licence

Distribué sous licence MIT. Voir [`LICENSE`](LICENSE).
