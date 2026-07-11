# Scénario 3 — Administration sécurisée (PAW NixOS)

## Objectif

Démontrer que l'administration des serveurs critiques passe **uniquement** par
le bastion NixOS (ProxyJump), et que la configuration du bastion est **immuable**
(écrasée à chaque déploiement).

C'est le « Waouh effect » du projet.

## Pré-requis

- Bastion NixOS opérationnel (10.10.99.20, VLAN 99)
- Poste admin (Windows) avec clé SSH FIDO2
- Serveur Ubuntu (10.10.30.10, VLAN 30) accessible via bastion

## Déroulé

### Étape 1 — Annoncer
> « L'administrateur ne se connecte jamais directement aux serveurs critiques.
> Il transite par un bastion NixOS, lui-même dans une zone isolée. De plus, la
> configuration de ce bastion est déclarative et immuable : si un attaquant la
> modifie, NixOS l'écrasera au prochain déploiement. »

### Étape 2 — Montrer l'impossibilité d'un accès direct

Depuis le poste admin (Windows) :
```bash
# Tentative d'accès direct au serveur Ubuntu (doit échouer)
ssh webadmin@10.10.30.10
# Connection timed out (OPNsense bloque, pas de route)
```

### Étape 3 — Démontrer la connexion sécurisée (ProxyJump)

```bash
# Connexion via le bastion (ProxyJump) : Win -> Bastion -> Serveur
ssh -J opsadmin@10.10.99.20 webadmin@10.10.30.10
```

Explication : la commande SSH se connecte d'abord au bastion (10.10.99.20), puis
depuis le bastion établit une seconde connexion vers le serveur (10.10.30.10).
OPNsense autorise uniquement le bastion à joindre le port 22 du VLAN 30.

### Étape 4 — Le « Waouh » : ouvrir configuration.nix

Sur le bastion, ouvrir `/etc/nixos/configuration.nix` et montrer les lignes clés :

```nix
services.openssh.settings = {
  PasswordAuthentication = false;        # ❌ Jamais de mots de passe
  PermitRootLogin = "no";                # ❌ Root interdit
  KbdInteractiveAuthentication = false;
  PubkeyAuthentication = true;           # ✅ Clés uniquement
};
```

Puis expliquer :
> « Ces paramètres ne sont pas dans un fichier texte modifiable à la main.
> Ils sont déclarés dans la configuration NixOS. Si quelqu'un modifie
> `/etc/ssh/sshd_config` directement, NixOS l'écrasera au prochain
> `nixos-rebuild switch`. L'immuabilité empêche la persistance d'une backdoor. »

### Étape 5 — Montrer la configuration versionnée

```bash
# Sur le bastion, la config est versionnée Git
cd /etc/nixos
git log --oneline
# Chaque modification est tracée, reproductible, auditable
```

### Étape 6 — Démontrer le durcissement

Montrer la checklist de durcissement :
- `boot.readOnlyNixStore = true` → store en lecture seule
- `boot.tmpOnTmpfs = true` → /tmp en RAM (vidé au reboot)
- `security.auditd.enable = true` → traçabilité
- Pare-feu local (iptables) → SSH entrant VLAN 99 uniquement

## Argument à développer

> « Le bastion NixOS combine quatre piliers :
> 1. **Authentification forte** : clés FIDO2, root interdit, sudo audité.
> 2. **Immuabilité** : configuration déclarative écrasée à chaque rebuild.
> 3. **Défense en profondeur** : pare-feu local, fail2ban, auditd, sysctl.
> 4. **Administration tracée** : ProxyJump, logs vers SIEM, sudo logging.
>
> Si un attaquant compromet le poste admin, il ne peut pas persister sur le
> bastion : toute modification manuelle disparaît au prochain déploiement.
> Et tout est versionné dans Git → reproductibilité totale. »

## Architecture d'administration (rappel)

```
Poste admin (Windows, VLAN 10 ou extérieur)
    │
    │ SSH (clé FIDO2 ed25519-sk)
    ▼
Bastion NixOS (VLAN 99, 10.10.99.20)
    │  ← immuable, config déclarative versionnée Git
    │
    │ SSH (ProxyJump, clé dédiée)
    ▼
Serveurs critiques (VLAN 30)
    - Ubuntu Web+BDD (10.10.30.10)
    - Windows Server AD (10.10.50.20)
```

## Points clés à montrer en entretien

| Élément | Ligne / fichier | Bénéfice |
|---------|-----------------|----------|
| Root interdit | `PermitRootLogin = "no"` | Force l'escalation sudo auditable |
| Mots de passe interdits | `PasswordAuthentication = false` | Anti-bruteforce |
| Clé FIDO2 | `ssh-ed25519-sk` | Facteur matériel, anti-phishing |
| Store lecture seule | `boot.readOnlyNixStore = true` | Anti-persistance |
| /tmp en RAM | `boot.tmpOnTmpfs = true` | Anti-persistance |
| Config versionnée | `configuration.nix` dans Git | Reproductibilité, audit |
| Auditd | `security.auditd.enable = true` | Traçabilité des actions |
| ProxyJump | `ssh/ssh_config` | Pas d'accès direct aux serveurs |
