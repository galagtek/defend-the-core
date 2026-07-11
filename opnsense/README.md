# OPNsense — Pare-feu / routeur inter-VLAN

## Rôle

OPNsense est le **gardien** de l'infrastructure : il possède une interface dans chaque
VLAN et assure le routage inter-VLAN avec filtrage strict (**default-deny**).

## Pré-requis VirtualBox

1. Créer une VM OPNsense avec **5 interfaces réseau** :
   - **Adapter 1** : NAT (WAN, accès Internet)
   - **Adapter 2** : Réseau interne `vbox-vlan10` (zone bureautique)
   - **Adapter 3** : Réseau interne `vbox-vlan20` (DMZ)
   - **Adapter 4** : Réseau interne `vbox-vlan30` (zone critique)
   - **Adapter 5** : Réseau interne `vbox-vlan99` (admin / SIEM)
2. Installer OPNsense depuis l'ISO officielle (https://opnsense.org/download/).
3. Une fois l'installation terminée, assigner les interfaces via la console :
   - `vtnet0` → WAN (DHCP)
   - `vtnet1` → LAN / VLAN 10 (10.10.10.1/24)
   - `vtnet2` → OPT1 / VLAN 20 (10.10.20.1/24)
   - `vtnet3` → OPT2 / VLAN 30 (10.10.30.1/24)
   - `vtnet4` → OPT3 / VLAN 99 (10.10.99.1/24)

## Activation de l'API

Les scripts utilisent l'**API REST OPNsense**. Pour l'activer :

1. Interface web → **System → Settings → Administration**
2. Cocher **Enable API**
3. Créer une clé API + secret via **System → Access → Users → root → Edit**
   (onglet « API keys »)
4. Renseigner ces valeurs dans `.env` (cf. `../.env.example`) :
   ```
   OPNSENSE_API_KEY="..."
   OPNSENSE_API_SECRET="..."
   OPNSENSE_HOST="10.10.99.1"
   ```

## Scripts

| Script | Description |
|--------|-------------|
| `00-initial-setup.sh` | Configuration initiale : interfaces, mot de passe admin, HTTPS, hardening global |
| `01-vlan-interfaces.sh` | Affectation IP des interfaces (déjà faite en console, ce script vérifie/rend idempotent) |
| `02-firewall-rules.sh` | Application de la matrice default-deny (voir `../architecture/firewall-rules.md`) |
| `03-nat-gateway.sh` | NAT sortant, rules de port forwarding, hardening WAN |

## Ordre d'exécution

```bash
# Depuis la machine hôte ou le bastion (accès à l'API OPNsense)
export $(cat ../.env | xargs)
bash scripts/00-initial-setup.sh
bash scripts/01-vlan-interfaces.sh
bash scripts/02-firewall-rules.sh
bash scripts/03-nat-gateway.sh
```

## Export GitOps

Une fois la configuration validée, exporter la config complète :

```
Interface web → System → Configuration → Backups → Download configuration
```

Placer le fichier dans `export/config.xml` pour traçabilité GitOps.
