# Bastion NixOS — PAW (Privileged Access Workstation)

## Rôle : la star du projet

Le bastion NixOS est le point d'administration **unique** vers les serveurs critiques
(VLAN 30). L'administrateur ne se connecte **jamais** directement aux serveurs depuis
son poste Windows : il transite par le bastion (concept **PAW** — Privileged Access
Workstation).

## Pourquoi NixOS ?

NixOS offre une caractéristique unique pour la sécurité : la **configuration déclarative
et immuable**.

- Toute la configuration système est décrite dans `configuration.nix`.
- Toute modification manuelle d'un fichier de configuration (ex : `/etc/ssh/sshd_config`)
  est **écrasée** au prochain `nixos-rebuild switch`.
- Il est impossible pour un attaquant de persister une backdoor dans un fichier de config
  système : elle disparaîtra au prochain déploiement.
- L'état du système est versionnable dans Git → reproductibilité totale.

C'est l'argument « Waouh » de l'entretien : **immuabilité = résilience à la persistance**.

## Architecture d'administration (ProxyJump)

```
Poste admin (Windows)
    │
    │ SSH (clé FIDO2)
    ▼
Bastion NixOS (VLAN 99, 10.10.99.20)
    │
    │ SSH (clé, ProxyJump)
    ▼
Serveurs critiques (VLAN 30)
```

L'admin lance une seule commande :
```bash
ssh -J bastion ubuntu@10.10.30.10
```

OPNsense autorise **uniquement** le bastion (10.10.99.20) à joindre le port 22 du
VLAN 30. Aucun autre chemin n'existe.

## Fichiers

| Fichier | Description |
|---------|-------------|
| `configuration.nix` | Configuration NixOS complète et durcie (commentée en français) |
| `hardware-configuration.nix` | Configuration matériel VM VirtualBox |
| `ssh/sshd_config.nix` | Module SSH serveur durci (réutilisable) |
| `ssh/ssh_config` | Configuration client SSH avec ProxyJump |
| `docs/hardening-checklist.md` | Checklist des durcissements appliqués |

## Déploiement

1. Installer NixOS minimal sur une VM VirtualBox (1 interface sur `vbox-vlan99`).
2. Copier `configuration.nix` et `hardware-configuration.nix` dans `/etc/nixos/`.
3. Injecter la clé publique admin (FIDO2) dans `configuration.nix`
   (variable `users.users.opsadmin.openssh.authorizedKeys.keys`).
4. Appliquer :
   ```bash
   sudo nixos-rebuild switch
   ```
5. Vérifier le durcissement avec `docs/hardening-checklist.md`.

## Points clés à montrer en entretien

- `PermitRootLogin = "no"` → root ne peut pas se connecter en SSH
- `PasswordAuthentication = false` → uniquement des clés
- `services.openssh.settings.KbdInteractiveAuthentication = false`
- Clé FIDO2 (`ssh-ed25519-sk`) → facteur matériel, résistante au phishing
- `boot.readOnlyNixStore = true` → le store Nix est en lecture seule
- `security.auditd.enable = true` → traçabilité des actions
- `networking.firewall` → pare-feu local (défense en profondeur)
- Si un attaquant modifie `/etc/ssh/sshd_config` à la main → écrasé au prochain `switch`
