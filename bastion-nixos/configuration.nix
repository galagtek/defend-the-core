# ====================================================================
# Bastion NixOS — configuration.nix durci (Defend-The-Core)
# ====================================================================
# Machine : Bastion / PAW (Privileged Access Workstation)
# VLAN    : 99 (Zone Admin / SIEM)
# IP      : 10.10.99.20
#
# Objectif : point d'administration UNIQUE vers les serveurs critiques.
#   - Configuration déclarative et IMMUABLE (NixOS)
#   - SSH par clés uniquement (FIDO2), root interdit
#   - Pare-feu local (défense en profondeur)
#   - Auditd activé (traçabilité)
#   - Services minimaux (principe de moindre privilège)
#
# Argument entretien : si un attaquant modifie manuellement un fichier
# de config système (ex: /etc/ssh/sshd_config), NixOS l'écrasera au
# prochain `nixos-rebuild switch`. L'immuabilité empêche la persistance.
# ====================================================================

{ config, pkgs, lib, ... }:

{
  # ----------------------------------------------------------------
  # 1. IDENTITÉ SYSTÈME
  # ----------------------------------------------------------------
  networking.hostName = "bastion-dtc";      # Nom d'hôte du bastion
  networking.domain = "defendcore.internal";   # Domaine interne
  time.timeZone = "Europe/Paris";           # Fuseau horaire

  # ----------------------------------------------------------------
  # 2. RÉSEAU & ADRESSAGE STATIQUE (VLAN 99)
  # ----------------------------------------------------------------
  # Le bastion est sur le VLAN 99 (admin/SIEM), adresse statique.
  # OPNsense (10.10.99.1) est la passerelle.
  networking.useDHCP = false;
  networking.interfaces.enp0s3 = {
    ipv4.addresses = [{
      address = "10.10.99.20";
      prefixLength = 24;
    }];
  };
  networking.defaultGateway = "10.10.99.1";
  networking.nameservers = [ "10.10.50.20" "1.1.1.1" ];  # AD + fallback

  # ----------------------------------------------------------------
  # 3. PARE-FEU LOCAL (défense en profondeur)
  # ----------------------------------------------------------------
  # Même si OPNsense filtre déjà, le bastion a son propre pare-feu.
  # Règle : on n'accepte QUE le SSH entrant (depuis le VLAN 99 uniquement)
  # et le SSH sortant vers le VLAN 30 (administration). Tout le reste est bloqué.
  networking.firewall = {
    enable = true;
    # Interfaces : on n'écoute que sur enp0s3 (VLAN 99)
    allowedTCPPorts = [ 22 ];           # SSH entrant (admin -> bastion)
    allowedUDPPorts = [ ];
    # Restriction par source via extraRules : seul le VLAN 99 peut SSH entrant
    extraRules = ''
      # Autoriser SSH entrant uniquement depuis le VLAN 99 (admin)
      iptables -A INPUT -i enp0s3 -s 10.10.99.0/24 -p tcp --dport 22 -j ACCEPT
      # Autoriser SSH sortant vers le VLAN 30 (administration des serveurs)
      iptables -A OUTPUT -o enp0s3 -d 10.10.30.0/24 -p tcp --dport 22 -j ACCEPT
      # Bloquer tout autre trafic sortant vers les autres VLANs
      iptables -A OUTPUT -o enp0s3 -d 10.10.10.0/24 -j DROP
      iptables -A OUTPUT -o enp0s3 -d 10.10.20.0/24 -j DROP
    '';
    # Log des connexions refusées
    logRefusedConnections = true;
    logRefusedPackets = true;
  };

  # ----------------------------------------------------------------
  # 4. SSH SERVEUR DURCI (le cœur de la sécurité)
  # ----------------------------------------------------------------
  # Voir aussi ssh/sshd_config.nix pour le module réutilisable.
  services.openssh = {
    enable = true;

    settings = {
      # --- Authentification ---
      PasswordAuthentication = false;        # ❌ Jamais de mots de passe
      KbdInteractiveAuthentication = false;  # ❌ Pas de clavier interactif
      PermitRootLogin = "no";                # ❌ Root interdit en SSH

      # --- Clés etForwarding ---
      PubkeyAuthentication = true;           # ✅ Clés uniquement
      AllowAgentForwarding = false;          # ❌ Pas de forwarding d'agent (anti-détournement)
      AllowTcpForwarding = "no";             # ❌ Pas de tunneling TCP (sauf besoin métier)

      # --- Robustesse cryptographique ---
      KexAlgorithms = [
        "curve25519-sha256"
        "curve25519-sha256@libssh.org"
        "diffie-hellman-group16-sha512"
      ];
      Ciphers = [
        "chacha20-poly1305@openssh.com"
        "aes256-gcm@openssh.com"
        "aes256-ctr"
      ];
      MACs = [
        "hmac-sha2-512-etm@openssh.com"
        "hmac-sha2-256-etm@openssh.com"
      ];

      # --- Limites et logging ---
      MaxAuthTries = 3;                      # 3 essais max avant ban
      LoginGraceTime = 30;                   # 30s pour s'authentifier
      ClientAliveInterval = 300;             # Timeout inactivité 5min
      ClientAliveCountMax = 0;               # Déconnexion immédiate au timeout
      LogLevel = "VERBOSE";                  # Logging détaillé (traçabilité)
      PermitEmptyPasswords = false;           # Sécurité : jamais de mdp vides
      X11Forwarding = false;                 # ❌ Pas de X11 (surface d'attaque)
    };

    # Restreindre les utilisateurs autorisés à se connecter
    allowSFTP = false;                       # SFTP désactivé (pas nécessaire sur un bastion)

    # Hôtes connus (servers critiques du VLAN 30) - empêche le MITM
    knownHosts = {
      ubuntu-web = {
        hostNames = [ "10.10.30.10" ];
        publicKey = "ssh-ed25519 AAAA... remplacer_par_clé_publique_ubuntu_web";
      };
      win-server = {
        hostNames = [ "10.10.50.20" ];
        publicKey = "ssh-ed25519 AAAA... remplacer_par_clé_publique_win_server";
      };
    };
  };

  # ----------------------------------------------------------------
  # 5. UTILISATEUR ADMINISTRATEUR (opsadmin)
  # ----------------------------------------------------------------
  # Compte dédié à l'administration. Pas de login root direct.
  # La clé SSH DOIT être une clé FIDO2 (ssh-ed25519-sk) : facteur matériel.
  users.users.opsadmin = {
    isNormalUser = true;
    description = "Administrateur Defend-The-Core";
    # Mot de passe initial (sera changé au premier login) - hashé via mkpasswd
    # ⚠️ Remplacer par un hash généré : mkpasswd -m sha-512
    hashedPassword = "$6$rounds=5000$REPLACE_WITH_HASH";

    # Groupe sudo pour l'escalade (avec mot de passe)
    extraGroups = [ "wheel" "audit" "systemd-journal" ];

    # Clé SSH publique FIDO2 (ssh-ed25519-sk)
    # ⚠️ REMPLACER par votre clé : ssh-keygen -t ed25519-sk
    openssh.authorizedKeys.keys = [
      "ssh-ed25519-sk AAAA... remplacer_par_votre_cle_fido2 opsadmin@paw"
    ];

    # Shell : bash minimaliste (pas de zsh/fish superflu)
    shell = pkgs.bash;

    # Pas de mot de passe au login (clé uniquement), mais sudo exige le mot de passe
  };

  # Configuration de sudo : exige le mot de passe, log tout
  security.sudo = {
    enable = true;
    wheelNeedsPassword = true;              # Le sudo exige TOUJOURS un mot de passe
    extraConfig = ''
      # Log toutes les commandes sudo (traçabilité)
      Defaults log_input, log_output
      Defaults logfile="/var/log/sudo.log"
      # Timeout court pour les sessions sudo
      Defaults timestamp_timeout=5
    '';
  };

  # ----------------------------------------------------------------
  # 6. DURCISSEMENT SYSTÈME (sysctl)
  # ----------------------------------------------------------------
  # Paramètres noyau renforcés (inspirés CIS Benchmark).
  boot.kernel.sysctl = {
    # --- Protection réseau ---
    "net.ipv4.ip_forward" = 0;              # Le bastion ne route pas
    "net.ipv4.conf.all.send_redirects" = 0;
    "net.ipv4.conf.default.send_redirects" = 0;
    "net.ipv4.conf.all.accept_redirects" = 0;
    "net.ipv4.conf.default.accept_redirects" = 0;
    "net.ipv4.conf.all.secure_redirects" = 0;
    "net.ipv6.conf.all.accept_redirects" = 0;
    "net.ipv4.conf.all.accept_source_route" = 0;
    "net.ipv4.conf.default.accept_source_route" = 0;
    # --- Anti-spoofing ---
    "net.ipv4.conf.all.rp_filter" = 1;
    "net.ipv4.conf.default.rp_filter" = 1;
    # --- SYN flood protection ---
    "net.ipv4.tcp_syncookies" = 1;
    # --- Logging paquets étranges ---
    "net.ipv4.conf.all.log_martians" = 1;
    # --- ICMP : limiter les réponses (anti-reconnaissance) ---
    "net.ipv4.icmp_echo_ignore_broadcasts" = 1;
    "net.ipv4.icmp_ignore_bogus_error_responses" = 1;
    # --- Mémoire : ASLR renforcé ---
    "kernel.randomize_va_space" = 2;
    # --- Kernel : restrictions ptrace (anti-debug) ---
    "kernel.yama.ptrace_scope" = 2;         # 2 = ptrace restreint à root
    # --- Restriction dmesg aux utilisateurs non-privilégiés ---
    "kernel.dmesg_restrict" = 1;
    "kernel.kptr_restrict" = 2;             # Cacher les pointeurs kernel
    # --- Exec shield / ASLR ---
    "dev.tty.ldisc_autoload" = 0;
    "fs.protected_hardlinks" = 1;
    "fs.protected_symlinks" = 1;
    "fs.protected_fifos" = 2;
    "fs.protected_regular" = 2;
    "fs.suid_dumpable" = 0;                 # Pas de core dumps pour les binaires suid
  };

  # ----------------------------------------------------------------
  # 7. IMMUABILITÉ & LECTURE SEULE
  # ----------------------------------------------------------------
  # Le store Nix est en lecture seule : impossible d'ajouter des binaires
  # ou de modifier les programmes installés sans passer par nixos-rebuild.
  boot.readOnlyNixStore = true;

  # /tmp sur tmpfs (RAM) : vidé à chaque redémarrage (anti-persistance)
  boot.tmpOnTmpfs = true;
  boot.cleanTmpDir = true;

  # ----------------------------------------------------------------
  # 8. AUDIT & TRAÇABILITÉ (auditd)
  # ----------------------------------------------------------------
  # Auditd enregistre les actions sensibles : accès fichiers, exec, identité.
  # Les logs sont envoyés vers Wazuh pour corrélation SIEM.
  security.auditd.enable = true;
  security.audit = {
    enable = true;
    rules = [
      # Surveiller les modifications de fichiers de configuration
      "-w /etc/nixos/ -p wa -k config_changes"
      "-w /etc/passwd -p wa -k identity"
      "-w /etc/group -p wa -k identity"
      "-w /etc/sudoers -p wa -k sudo_changes"
      "-w /var/log/sudo.log -p wa -k sudo_log"
      # Surveiller les exécutions de commandes sensibles
      "-w /run/current-system/sw/bin/nixos-rebuild -p x -k nixos_admin"
      # Surveiller les changements de contexte SELinux/AppArmor
      "-w /etc/apparmor/ -p wa -k apparmor"
    ];
  };

  # ----------------------------------------------------------------
  # 9. SERVICES MINIMAUX (moindre privilège)
  # ----------------------------------------------------------------
  # Un bastion ne fait QUE du SSH. On désactive tout le superflu.
  services = {
    # Pas de serveur web, pas de base de données, pas de mail...
    openssh.startWhenNeeded = false;  # sshd toujours actif (besoin admin)

    # NTP : synchronisation temporelle (indispensable pour la corrélation SIEM)
    timesyncd.enable = true;

    # Pas de gestionnaire de bureau (c'est un serveur, pas un desktop)
    xserver.enable = false;
  };

  # ----------------------------------------------------------------
  # 10. JOURNALING & LOGS VERS WAZUH
  # ----------------------------------------------------------------
  # Les journaux système sont conservés localement ET envoyés à Wazuh.
  services.journald = {
    extraConfig = ''
      SystemMaxUse=500M       # Limite de stockage
      MaxRetentionSec=30day   # Conservation 30 jours
      ForwardToSyslog=yes     # Forward vers syslog (pour Wazuh)
    '';
  };

  # Rsyslog : forward des logs vers Wazuh (10.10.99.10:514)
  services.rsyslogd.enable = true;
  services.rsyslogd.extraConfig = ''
    *.* action(type="omfwd" target="10.10.99.10" port="514" protocol="udp")
  '';

  # ----------------------------------------------------------------
  # 11. PAQUETS INSTALLÉS (minimaliste)
  # ----------------------------------------------------------------
  # Seulement ce qui est nécessaire pour administrer.
  environment.systemPackages = with pkgs; [
    vim                  # Éditeur
    git                  # Versionnage de la config
    curl                 # Requêtes HTTP (API OPNsense/Wazuh)
    wget
    tmux                 # Multiplexeur de terminaux
    htop                 # Monitoring
    mtr                  # Diagnostic réseau
    nmap                 # Scan réseau (admin seulement)
    openssl              # Gestion certificats/clés
    mkpasswd             # Génération de hash de mot de passe
  ];

  # ----------------------------------------------------------------
  # 12. AGENT WAZUH (surveillance du bastion lui-même)
  # ----------------------------------------------------------------
  # Le bastion est lui-même surveillé : ses logs SSH et sudo remontent
  # vers le SIEM. Configuration gérée via deploy-agent-linux.sh du dossier wazuh/.
  # (L'installation de l'agent n'est pas déclarative Nix car Wazuh ne fournit
  #  pas de paquet Nix officiel ; on utilise le script de déploiement.)

  # ----------------------------------------------------------------
  # 13. MISES À JOUR AUTOMATIQUES DE SÉCURITÉ
  # ----------------------------------------------------------------
  # NixOS peut appliquer automatiquement les mises à jour de sécurité.
  # Sur un bastion, on préfère cependant le contrôle manuel (revue avant apply).
  # On active donc seulement le channel de sécurité et on notifie.
  system.autoUpgrade = {
    enable = true;
    channel = "https://nixos.org/channels/nixos-26.05-small";
    # Ne pas reboot automatiquement : l'admin valide
    allowReboot = false;
    # Fréquence : une fois par jour
    dates = "04:00";
  };

  # ----------------------------------------------------------------
  # 14. BANNIÈRE D'AVERTISSEMENT (légal + dissuasion)
  # ----------------------------------------------------------------
  # Affichée à chaque connexion SSH : rappel que l'accès est surveillé.
  services.openssh.banner = ''
    ============================================================
    ACCES RESERVE - Defend-The-Core Bastion (VLAN 99)
    ============================================================
    Toute connexion est journalisee et envoyee au SIEM (Wazuh).
    Toute tentative d'acces non autorise sera poursuivie.
    Deconnectez-vous immediatement si vous n'etes pas autorise.
    ============================================================
  '';

  # ----------------------------------------------------------------
  # 15. FAIL2BAN (défense en profondeur anti-bruteforce)
  # ----------------------------------------------------------------
  # Même si le mot de passe est désactivé, fail2ban bannit les IP
  # qui génèrent trop d'échecs (scan, erreurs de clé).
  services.fail2ban = {
    enable = true;
    maxretry = 3;                          # 3 échecs = ban
    bantime = "1h";                        # Ban 1 heure
    bantime-increment = {
      enable = true;                       # Ban de plus en plus long
      maxbantime = "1w";                   # Max 1 semaine
    };
    jails = {
      sshd = ''
        enabled = true
        port = 22
        filter = sshd
        logpath = /var/log/auth.log
        maxretry = 3
        bantime = 1h
      '';
    };
  };

  # ----------------------------------------------------------------
  # 16. VERSION SYSTÈME (NixOS)
  # ----------------------------------------------------------------
  # Cette déclaration permet de suivre l'évolution de la config.
  system.stateVersion = "26.05";           # Version NixOS de référence
}
