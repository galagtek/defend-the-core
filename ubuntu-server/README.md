# Ubuntu Server 22.04 — Serveur Web + BDD (Zone Critique)

## Rôle

Serveur métier de la **zone critique** (VLAN 30, 10.10.30.10). Héberge la pile
Web (Nginx) et la base de données (PostgreSQL). Aucun accès direct depuis la zone
bureautique : seule l'administration passe par le bastion (ProxyJump).

## Pré-requis

- VM Ubuntu 22.04 LTS (2 vCPU, 4 Go RAM, 30 Go disque)
- Réseau interne VirtualBox `vbox-vlan30`
- IP statique : 10.10.30.10 / Passerelle : 10.10.30.1

## Durcissement appliqué

| Domaine | Mesure |
|---------|--------|
| SSH | Clés uniquement, root interdit, port par défaut |
| Auditd | Surveillance fichiers sensibles + commandes |
| Pare-feu | UFW : uniquement 22 (bastion) + 80/443 (reverse proxy) |
| sysctl | ASLR, anti-spoofing, SYN flood, restrictions kernel |
| CIS | Durcissement essentiel (CIS Benchmark Ubuntu 22.04) |
| Wazuh | Agent installé + SCA (Security Configuration Assessment) |

## Scripts

| Script | Description |
|--------|-------------|
| `00-base-setup.sh` | Mises à jour, utilisateur admin, sudoers, timezone |
| `01-web-stack.sh` | Nginx + PostgreSQL + durcissement applicatif |
| `02-harden-ssh.sh` | SSH clés uniquement, root interdit, algo crypto forts |
| `03-install-wazuh-agent.sh` | Déploiement agent Wazuh |
| `04-configure-auditd.sh` | Auditd + règles de surveillance |
| `05-ufw-firewall.sh` | Pare-feu UFW (défense en profondeur) |
| `06-cis-hardening.sh` | Durcissement CIS essentiel |

## Ordre d'exécution

```bash
sudo bash scripts/00-base-setup.sh
sudo bash scripts/01-web-stack.sh
sudo bash scripts/02-harden-ssh.sh
sudo bash scripts/03-install-wazuh-agent.sh
sudo bash scripts/04-configure-auditd.sh
sudo bash scripts/05-ufw-firewall.sh
sudo bash scripts/06-cis-hardening.sh
```

## Administration

Connexion **uniquement** via le bastion (ProxyJump) :
```bash
# Depuis le poste admin, à travers le bastion
ssh -J bastion webadmin@10.10.30.10
```

Aucun accès direct depuis le VLAN 10 ou Internet n'est possible (règles OPNsense).
