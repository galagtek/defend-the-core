# Checklist de durcissement — Bastion NixOS

Cette checklist documente chaque durcissement appliqué au bastion et le motif de
sécurité associé. Elle est conçue pour être présentée en entretien : chaque point
se justifie par une recommandation ANSSI ou CIS.

## 1. Authentification

| # | Mesure | Implémentation | Justification |
|---|--------|----------------|---------------|
| 1.1 | SSH par clés uniquement | `PasswordAuthentication = false` | ANSSI : authentification forte, résistance au bruteforce |
| 1.2 | Root interdit en SSH | `PermitRootLogin = "no"` | CIS : moindre privilège, forcer l'escalade sudo auditable |
| 1.3 | Clé FIDO2 (facteur matériel) | `ssh-ed25519-sk` | ANSSI : facteur matériel, résistant au phishing (anti-clonage) |
| 1.4 | Pas de clavier interactif | `KbdInteractiveAuthentication = false` | Réduction de la surface d'authentification |
| 1.5 | 3 essais max | `MaxAuthTries = 3` | Ralentir les attaques |
| 1.6 | Sudo exige le mot de passe | `wheelNeedsPassword = true` | Traçabilité de l'escalade de privilèges |
| 1.7 | Compte admin dédié | `users.users.opsadmin` | Séparation des rôles, pas de login direct root |

## 2. Cryptographie

| # | Mesure | Implémentation | Justification |
|---|--------|----------------|---------------|
| 2.1 | Algorithmes KEX modernes | `curve25519-sha256`, `group16-sha512` | ANSSI : éliminer les algorithmes faibles (DSA, DH groups faibles) |
| 2.2 | Chiffrements forts | `chacha20-poly1305`, `aes256-gcm` | Préférence aux AEAD, élimination de 3DES/CBC |
| 2.3 | MACs étiquetés | `hmac-sha2-512-etm` | Éviter les MACs vulnérables (hmac-sha1) |
| 2.4 | Clés hôtes ed25519 | `HostKeyAlgorithms` | Courbes elliptiques modernes, pas de RSA 1024 |

## 3. Immuabilité (l'argument NixOS)

| # | Mesure | Implémentation | Justification |
|---|--------|----------------|---------------|
| 3.1 | Store Nix en lecture seule | `boot.readOnlyNixStore = true` | Impossible d'ajouter/modifier des binaires sans rebuild |
| 3.2 | /tmp sur tmpfs (RAM) | `boot.tmpOnTmpfs = true` | Vidé à chaque reboot → anti-persistance |
| 3.3 | Configuration déclarative | `configuration.nix` versionné Git | Toute modif manuelle est écrasée au `nixos-rebuild switch` |
| 3.4 | Rebuild reproductible | `system.stateVersion` | Deux déploiements identiques = même état |

**Argument entretien :** « Si un attaquant modifie `/etc/ssh/sshd_config` pour
ajouter un mot de passe, NixOS l'écrasera au prochain déploiement. L'immuabilité
empêche la persistance. »

## 4. Réseau & pare-feu

| # | Mesure | Implémentation | Justification |
|---|--------|----------------|---------------|
| 4.1 | Pare-feu local activé | `networking.firewall.enable = true` | Défense en profondeur (au-delà d'OPNsense) |
| 4.2 | SSH entrant limité au VLAN 99 | `extraRules` iptables | Seul le réseau admin peut accéder au bastion |
| 4.3 | SSH sortant limité au VLAN 30 | `extraRules` iptables | Le bastion ne peut atteindre QUE les serveurs critiques |
| 4.4 | Blocage VLAN 10/20 sortant | iptables DROP | Anti-mouvement latéral depuis le bastion |
| 4.5 | Pas de forwarding IP | `net.ipv4.ip_forward = 0` | Le bastion ne route pas |
| 4.6 | Anti-spoofing | `rp_filter = 1` | Rejet des paquets usurpés |
| 4.7 | SYN flood protection | `tcp_syncookies = 1` | Résistance aux attaques DoS |
| 4.8 | Log des paquets martiens | `log_martians = 1` | Détection de spoofing |

## 5. Audit & traçabilité

| # | Mesure | Implémentation | Justification |
|---|--------|----------------|---------------|
| 5.1 | auditd activé | `security.auditd.enable = true` | CIS : traçabilité des actions sensibles |
| 5.2 | Surveillance /etc/nixos | règle auditd `-w /etc/nixos/` | Détection de modification de config |
| 5.3 | Surveillance sudoers | règle auditd `-w /etc/sudoers` | Détection d'escalade de privilèges |
| 5.4 | Log des commandes sudo | `Defaults log_input, log_output` | Traçabilité complète des actions admin |
| 5.5 | Logs forwardés vers Wazuh | `services.rsyslogd` | Corrélation SIEM centralisée |
| 5.6 | journald limité à 500M/30j | `SystemMaxUse=500M` | Prévention saturation disque |
| 5.7 | LogLevel SSH VERBOSE | `LogLevel = "VERBOSE"` | Enregistre les clés utilisées (forensics) |

## 6. Durcissement noyau (sysctl)

| # | Mesure | Implémentation | Justification |
|---|--------|----------------|---------------|
| 6.1 | ASLR activé | `randomize_va_space = 2` | ANSSI : randomisation de l'espace d'adressage |
| 6.2 | ptrace restreint | `yama.ptrace_scope = 2` | Anti-debug de processus |
| 6.3 | dmesg restreint | `dmesg_restrict = 1` | Cacher les infos kernel aux utilisateurs non-privilégiés |
| 6.4 | kptr hidden | `kptr_restrict = 2` | Cacher les pointeurs kernel (anti-exploit) |
| 6.5 | Hardlinks/symlinks protégés | `protected_hardlinks = 1` | Prévention des attaques TOCTOU |
| 6.6 | Pas de core dumps suid | `suid_dumpable = 0` | Éviter la fuite de mémoire sensible |
| 6.7 | ICMP broadcast ignoré | `icmp_echo_ignore_broadcasts = 1` | Anti-smurf / reconnaissance |

## 7. Services & moindre privilège

| # | Mesure | Implémentation | Justification |
|---|--------|----------------|---------------|
| 7.1 | Pas de serveur X | `xserver.enable = false` | Un bastion est headless |
| 7.2 | Paquets minimaux | liste `systemPackages` restreinte | Réduction de la surface d'attaque |
| 7.3 | SFTP désactivé | `allowSFTP = false` | Pas de transfert de fichiers sur un bastion |
| 7.4 | Pas de forwarding agent/TCP | `AllowAgentForwarding = false` | Anti-détournement de session |
| 7.5 | fail2ban actif | `services.fail2ban` | Bannissement automatique des IP malveillantes |

## 8. Mises à jour

| # | Mesure | Implémentation | Justification |
|---|--------|----------------|---------------|
| 8.1 | Auto-upgrade sécurité | `system.autoUpgrade` | Patchs de sécurité automatiques |
| 8.2 | Pas de reboot auto | `allowReboot = false` | L'admin valide les redémarrages (disponibilité) |
| 8.3 | NTP synchronisé | `timesyncd.enable = true` | Indispensable pour la corrélation SIEM |

## 9. ProxyJump (administration sécurisée)

| # | Mesure | Implémentation | Justification |
|---|--------|----------------|---------------|
| 9.1 | Accès serveurs via bastion | `ProxyJump bastion` | Aucun accès direct au VLAN 30 |
| 9.2 | Hôtes connus (known_hosts) | `knownHosts` dans NixOS | Prévention MITM |
| 9.3 | Clés dédiées par usage | `id_ed25519_sk` (FIDO2) + `id_ed25519_servers` | Séparation des privilèges SSH |
| 9.4 | StrictHostKeyChecking | `ssh_config` | Rejet des changements de clé inattendus |

## Résumé pour l'entretien

> Le bastion NixOS combine **4 piliers** de sécurité :
> 1. **Authentification forte** (clés FIDO2, root interdit, sudo audité)
> 2. **Immuabilité** (config déclarative écrasée à chaque rebuild)
> 3. **Défense en profondeur** (pare-feu local + fail2ban + auditd + sysctl)
> 4. **Administration tracée** (ProxyJump, logs vers SIEM, sudo logging)
