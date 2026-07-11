# Topologie réseau — Defend-The-Core

## 1. Vue d'ensemble

L'infrastructure repose sur un cloisonnement en **quatre zones** (VLANs), cloisonnées
par un pare-feu OPNsense en **default-deny**. Chaque zone a un niveau de confiance
décroissant et des règles de flux strictes.

Le référentiel d'adressage est `10.10.X.0/24` où `X` identifie le VLAN.

## 2. Schéma logique

```
                              Internet
                                 │
                                 │ WAN (NAT VirtualBox, 10.0.2.0/24)
                          ┌──────┴───────┐
                          │   OPNsense   │   .1 de chaque VLAN (gateway)
                          │  10.10.10.1  │   Routeur inter-VLAN + filtrage
                          │  10.10.20.1  │
                          │  10.10.30.1  │
                          │  10.10.99.1  │
                          └──┬───┬──┬───┘
                             │   │  │
            ┌────────────────┘   │  └─────────────────┐
            │                    │                    │
   ┌────────┴─────────┐ ┌────────┴─────────┐ ┌────────┴─────────┐
   │ VLAN 10          │ │ VLAN 20          │ │ VLAN 30          │
   │ BUREAUTIQUE      │ │ DMZ              │ │ CRITIQUE         │
   │ 10.10.10.0/24    │ │ 10.10.20.0/24    │ │ 10.10.30.0/24    │
   │ Confiance : faible│ │ Confiance : moy. │ │ Confiance : haute│
   │                  │ │                  │ │                  │
   │ .50 Win10        │ │ .10 Reverse prox │ │ .10 Ubuntu Web   │
   │ .100 Kali        │ │ .20 VPN gateway  │ │ .20 Win Server AD│
   └──────────────────┘ └──────────────────┘ └──────────────────┘
                                                 │
                                                 │ (flux logs + SSH admin uniquement)
                                          ┌──────┴───────────┐
                                          │ VLAN 99          │
                                          │ ADMIN / SIEM     │
                                          │ 10.10.99.0/24    │
                                          │ Confiance : max  │
                                          │                  │
                                          │ .10 Wazuh        │
                                          │ .20 Bastion NixOS│
                                          └──────────────────┘
```

## 3. Cartographie VirtualBox

Chaque VLAN correspond à un **réseau interne VirtualBox** distinct (Internal Network),
ce qui simule le zoning physique/VLAN 802.1Q sans équipement actif.

| Réseau interne VirtualBox | VLAN | Rôle | OPNsense (patte) |
|---------------------------|------|------|------------------|
| `vbox-wan` | — | Accès Internet (NAT) | vtnet0 (WAN) |
| `vbox-vlan10` | 10 | Zone bureautique | vtnet1 |
| `vbox-vlan20` | 20 | Zone DMZ | vtnet2 |
| `vbox-vlan30` | 30 | Zone critique | vtnet3 |
| `vbox-vlan99` | 99 | Zone admin / SIEM | vtnet4 |

> OPNsense possède **5 interfaces réseau** dans VirtualBox : 1 NAT + 4 réseaux internes.

## 4. Plan d'adressage

Voir le fichier tabulaire [`addressing-plan.csv`](addressing-plan.csv).

### Récapitulatif

| VLAN | Réseau | Gateway | Masque | Plage hosts | Broadcast |
|------|--------|---------|--------|-------------|-----------|
| 10 | 10.10.10.0/24 | 10.10.10.1 | 255.255.255.0 | .10–.200 | .255 |
| 20 | 10.10.20.0/24 | 10.10.20.1 | 255.255.255.0 | .10–.100 | .255 |
| 30 | 10.10.30.0/24 | 10.10.30.1 | 255.255.255.0 | .10–.100 | .255 |
| 99 | 10.10.99.0/24 | 10.10.99.1 | 255.255.255.0 | .10–.50 | .255 |

## 5. Affectation des hôtes

| Hôte | VLAN | IP | Rôle | OS |
|------|------|----|----|-----|
| OPNsense | tous | .1 (par VLAN) | Pare-feu / routeur | OPNsense |
| Win10 (employé) | 10 | 10.10.10.50 | Poste utilisateur | Windows 10 |
| Kali (attaquant) | 10 | 10.10.10.100 | Simulation attaque | Kali Linux |
| Reverse proxy | 20 | 10.10.20.10 | Proxy inverse (DMZ) | Ubuntu 26.04 |
| VPN gateway | 20 | 10.10.20.20 | Accès distant | Ubuntu 26.04 |
| Ubuntu (Web+BDD) | 30 | 10.10.30.10 | Serveur métier | Ubuntu 26.04 |
| Windows Server (AD) | 30 | 10.10.50.20 | AD/DNS/DHCP | Windows Server 2022 |
| Wazuh (SIEM) | 99 | 10.10.99.10 | SIEM/XDR | Ubuntu 26.04 |
| Bastion NixOS (PAW) | 99 | 10.10.99.20 | Administration | NixOS |

## 6. Routage

- OPNsense assure le **routage inter-VLAN** (no router advertisement ; chaque hôte
  utilise l'IP `.1` de son VLAN comme passerelle par défaut).
- Aucun hôte ne possède de route statique vers un autre VLAN : tout passe par OPNsense,
  qui filtre chaque flux.
- **NAT sortant** sur l'interface WAN pour l'accès Internet des VMs autorisées.

## 7. Flux autorisés (synthèse)

La matrice complète des règles est dans [`firewall-rules.md`](firewall-rules.md).

Principe directeur : **default-deny**. Tout est interdit sauf explicitement autorisé.

| Source | Destination | Port | Action | Justification |
|--------|-------------|------|--------|---------------|
| VLAN 10 | VLAN 20 | 80, 443 | allow | Accès au reverse proxy uniquement |
| VLAN 10 | VLAN 30 | * | **deny** | Isolation totale zone critique |
| VLAN 10 | VLAN 99 | * | **deny** | Isolation zone admin |
| VLAN 99 | VLAN 30 | 22 | allow | SSH admin via bastion |
| Tous | VLAN 99 | 514, 1514 | allow | Flux de logs vers Wazuh (UDP/TCP) |
| WAN | VLAN 20 | 443 | allow | Accès VPN / services publics |
| VLAN 99 | WAN | 123 | allow | NTP (synchronisation SIEM) |

## 8. DHCP

- **VLAN 10** : DHCP actif sur OPNsense (plage `.100–.200`) pour les postes clients.
- **VLAN 30** : DHCP géré par Windows Server (AD) pour la zone critique.
- **VLAN 20 / 99** : adresses **statiques** uniquement (pas de DHCP, moindre privilège).
