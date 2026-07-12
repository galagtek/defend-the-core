# Gitea — Serveur Git interne (Zone Admin)

## Rôle

Gitea est le **dépôt Git interne** de l'infrastructure. Il héberge la version "production"
de l'Infrastructure as Code — avec les IPs réelles, les configurations complètes et les
valeurs effectives. Contrairement au dépôt GitHub public (portfolio), ce dépôt n'est
JAMAIS exposé à l'extérieur.

## Pourquoi un Git interne ?

| Problème avec GitHub | Solution avec Gitea |
|---------------------|---------------------|
| Plan d'adressage exposé | ✅ Interne, jamais accessible depuis Internet |
| Règles de pare-feu publiques | ✅ Configuration réelle protégée |
| Pas d'intégration AD | ✅ Auth LDAP via l'AD (10.10.50.20) |
| Données chez un tiers | ✅ Souveraineté totale des données |
| Pas de CI/CD sur réseau interne | ✅ Gitea Actions pour déploiement automatisé |

## Placement réseau

| Attribut | Valeur |
|----------|--------|
| VLAN | 99 (Admin/SIEM) |
| IP | 10.10.99.30 |
| OS | Ubuntu 26.04 LTS |
| RAM | 512 Mo minimum (Gitea est léger, écrit en Go) |
| Disque | 10 Go |
| Accès | Uniquement depuis la zone admin (bastion) |

## Authentification

Gitea s'authentifie via **LDAP** auprès de l'Active Directory (10.10.50.20) :

```
Utilisateur → Gitea (10.10.99.30:3000) → LDAP → AD (10.10.50.20:636)
```

- Bind DN : `svc_gitea_auth@defendcore.internal` (compte de service à privilèges minimaux)
- Port : 636 (LDAPS, jamais 389 non chiffré)
- Filtre : recherche dans `DC=defendcore,DC=internal`

## Déploiement

### 1. Créer la VM

```bash
virt-install \
  --name gitea \
  --memory 1024 \
  --vcpus 1 \
  --disk path=/var/lib/libvirt/images/gitea.qcow2,size=10,bus=scsi \
  --controller type=scsi,model=virtio-scsi \
  --cdrom /var/lib/libvirt/images/iso/ubuntu-26.04-live-server-amd64.iso \
  --os-variant ubuntu26.04 \
  --network network=vlan99 \
  --graphics spice \
  --noautoconsole
```

### 2. Installation de Gitea

```bash
# Sur la VM Gitea (Ubuntu 26.04, VLAN 99)
# Voir scripts/install-gitea.sh pour l'installation automatisée
sudo bash install-gitea.sh
```

### 3. Configuration LDAP

Dans l'interface web Gitea (http://10.10.99.30:3000) :
- **Administration → Authentication Sources → +**
- Type : LDAP
- Voir scripts/configure-ldap.sh

## Règles de pare-feu

| Interface | Source | Destination | Port | Action | Raison |
|-----------|--------|-------------|------|--------|--------|
| admin | `admin net` | `10.10.99.30` | `3000` | Pass | Accès web Gitea |
| admin | `admin net` | `10.10.99.30` | `22` | Pass | SSH pour git push |
| admin | `10.10.99.30` | `10.10.50.20` | `636` | Pass | Gitea → AD (LDAP auth) |
| admin | `10.10.99.30` | `WAN net` | `80, 443` | Pass | MAJ Gitea + packages |

## Workflow GitOps interne

```
1. Admin modifie configuration.nix sur le bastion
2. git commit + push → Gitea (10.10.99.30)
3. Gitea webhook → Gitea Actions (CI/CD)
4. CI/CD déploie : nixos-rebuild switch sur le bastion
5. De même pour OPNsense (API), Ubuntu (Ansible), etc.
```

## Backups

Gitea stocke ses données dans `/var/lib/gitea/`. Sauvegarde recommandée :
- Dump base SQLite/PostgreSQL : `gitea dump`
- Sauvegarde du dossier `/var/lib/gitea/repositories/`
- Fréquence : quotidienne, rétention 30 jours
