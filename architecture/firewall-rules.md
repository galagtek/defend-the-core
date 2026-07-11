# Matrice des règles de pare-feu — OPNsense

## 1. Principe directeur : Default-Deny

OPNsense applique un **default-deny** : tout flux non explicitement autorisé est rejeté.
Chaque interface dispose d'une règle finale implicite `block any any`.

> La philosophie ANSSI du cloisonnement impose qu'un flux ne puisse traverser une zone
> que s'il est nécessaire, identifié et tracé.

## 2. Niveaux de confiance

| Zone | VLAN | Confiance | Exposition |
|------|------|-----------|------------|
| Bureautique | 10 | Faible (postes utilisateurs, vecteur d'attaque) | Aucune |
| DMZ | 20 | Moyenne (services publics) | Limitée |
| Critique | 30 | Haute (serveurs métier, BDD) | Aucune |
| Admin / SIEM | 99 | Maximale (surveillance, bastion) | Aucune |

**Règle d'or** : un flux ne peut aller que d'une confiance égale ou supérieure vers une
égale ou inférieure, et uniquement sur des ports métiers explicites. Le retour vers le
VLAN 10 est **jamais** initié.

## 3. Matrice des flux autorisés

| # | Interface source | Source | Destination | Port(s) | Proto | Action | Log | Justification |
|---|------------------|--------|-------------|---------|-------|--------|-----|---------------|
| 1 | vlan10 | net 10.10.10.0/24 | 10.10.20.10 | 80, 443 | TCP | allow | yes | Accès au reverse proxy uniquement |
| 2 | vlan10 | net 10.10.10.0/24 | 10.10.20.20 | 443 | UDP/TCP | allow | yes | Accès VPN (WireGuard/OpenVPN) |
| 3 | vlan10 | net 10.10.10.0/24 | 10.10.30.0/24 | any | any | **block** | yes | Isolation totale zone critique |
| 4 | vlan10 | net 10.10.10.0/24 | 10.10.99.0/24 | any | any | **block** | yes | Isolation totale zone admin |
| 5 | vlan10 | net 10.10.10.0/24 | WAN | 53, 80, 443 | TCP/UDP | allow | no | DNS + HTTP(S) sortant (via OPNsense) |
| 6 | vlan20 | 10.10.20.10 | 10.10.30.10 | 80, 443 | TCP | allow | yes | Reverse proxy → Web métier |
| 7 | vlan20 | 10.10.20.20 | 10.10.30.0/24 | any | any | **block** | yes | VPN ne doit pas atteindre la BDD directement |
| 8 | vlan30 | 10.10.30.10 | 10.10.30.20 | 53 | TCP/UDP | allow | no | Web → AD pour résolution DNS |
| 9 | vlan30 | net 10.10.30.0/24 | 10.10.99.10 | 1514, 1515 | TCP | allow | yes | Flux de logs des serveurs vers Wazuh |
| 10 | vlan30 | net 10.10.30.0/24 | 10.10.99.0/24 | any | any | **block** | yes | Aucun autre flux vers l'admin |
| 11 | vlan99 | 10.10.99.20 | 10.10.30.0/24 | 22 | TCP | allow | yes | SSH admin du bastion vers les serveurs |
| 12 | vlan99 | 10.10.99.0/24 | 10.10.30.0/24 | any | any | **block** | yes | Seul le bastion peut SSH, pas Wazuh |
| 13 | vlan99 | 10.10.99.0/24 | WAN | 123 | UDP | allow | no | NTP pour la synchronisation SIEM |
| 14 | vlan99 | 10.10.99.0/24 | WAN | 80, 443 | TCP | allow | no | MAJ Wazuh/Elastic (restrictif) |
| 15 | WAN | any | 10.10.20.20 | 443 | UDP/TCP | allow | yes | Accès VPN entrant depuis Internet |
| 16 | WAN | any | 10.10.20.10 | 443 | TCP | allow | yes | Accès public au reverse proxy |
| 17 | WAN | any | 10.10.30.0/24 | any | any | **block** | yes | Aucune exposition de la zone critique |
| 18 | WAN | any | 10.10.99.0/24 | any | any | **block** | yes | Aucune exposition de la zone admin |
| 19 | * | any | 10.10.99.10 | 514, 1514 | UDP/TCP | allow | yes | Tous les flux de logs vers Wazuh |
| 20 | * | any | any | any | any | **block** | yes | Règle finale implicite (default-deny) |

## 4. Tableau de synthèse inter-VLAN

```
                ┌─────────────────── Vers ───────────────────┐
                │  VLAN10  VLAN20  VLAN30  VLAN99   WAN       │
   ┌────────────┼─────────────────────────────────────────────┤
   │ VLAN 10    │   —     80/443  BLOCK  BLOCK   53/80/443    │
   │ VLAN 20    │   —      —     80/443 BLOCK   (nat out)    │
De│ VLAN 30    │   —      —      —     1514     (nat out)    │
   │ VLAN 99    │   —      —      22     —       123/443     │
   │ WAN        │   —     443    BLOCK  BLOCK     —          │
   └────────────┴─────────────────────────────────────────────┘
```

## 5. Active Response (intégration Wazuh)

En complément des règles statiques, Wazuh peut injecter dynamiquement des règles de
**blocage d'IP** sur OPNsense via l'API (`/api/firewall/alias_util`), lorsqu'une
corrélation détecte une attaque (bruteforce, scan, etc.).

Voir [`wazuh/rules/active-response/`](../wazuh/rules/active-response/).

## 6. Logging

Toutes les règles **block** et les règles **allow** sensibles (inter-zone) loggent
explicitement (`log = yes`). Les logs OPNsense sont :
1. consultables localement (Firewall → Log Files),
2. transférés vers Wazuh (syslog UDP 514) pour corrélation SIEM.

## 7. Ordre d'évaluation

Les règles sont évaluées **de haut en bas**, première correspondance gagne. L'ordre
ci-dessus reflète l'ordre de priorité dans OPNsense : les `block` spécifiques précèdent
les `allow`, et la règle finale implicite bloque le reste.
