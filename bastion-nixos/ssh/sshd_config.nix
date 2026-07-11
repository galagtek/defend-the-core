# ====================================================================
# Module NixOS : service SSH durci (réutilisable)
# ====================================================================
# Ce module encapsule toute la configuration de durcissement SSH.
# Il peut être importé dans n'importe quel configuration.nix du
# projet pour appliquer la même posture de sécurité.
#
# Usage dans configuration.nix :
#   imports = [ ./ssh/sshd_config.nix ];
# ====================================================================

{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.hardened-sshd;
in {
  # Options du module
  options.services.hardened-sshd = {
    enable = mkEnableOption "Service SSH durci (Defend-The-Core)";

    allowedUsers = mkOption {
      type = types.listOf types.str;
      default = [ "opsadmin" ];
      description = "Liste des utilisateurs autorisés à se connecter en SSH";
    };

    listenPort = mkOption {
      type = types.port;
      default = 22;
      description = "Port d'écoute du serveur SSH";
    };
  };

  config = mkIf cfg.enable {
    # Activation du service OpenSSH
    services.openssh = {
      enable = true;
      ports = [ cfg.listenPort ];

      settings = {
        # === Authentification : CLÉS UNIQUEMENT ===
        PasswordAuthentication = false;
        KbdInteractiveAuthentication = false;
        PermitRootLogin = "no";
        PubkeyAuthentication = true;
        PermitEmptyPasswords = false;

        # === Restrictions de forwarding ===
        AllowAgentForwarding = false;
        AllowTcpForwarding = "no";
        X11Forwarding = false;
        PermitTunnel = false;

        # === Robustesse cryptographique ===
        # Algorithmes modernes uniquement (NIST post-quantum ready)
        KexAlgorithms = [
          "curve25519-sha256"
          "curve25519-sha256@libssh.org"
          "diffie-hellman-group16-sha512"
          "diffie-hellman-group18-sha512"
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
        HostKeyAlgorithms = [
          "ssh-ed25519"
          "ssh-ed25519-cert-v01@openssh.com"
          "rsa-sha2-512-cert-v01@openssh.com"
        ];

        # === Limites & logging ===
        MaxAuthTries = 3;
        MaxSessions = 4;
        LoginGraceTime = 30;
        ClientAliveInterval = 300;
        ClientAliveCountMax = 0;
        LogLevel = "VERBOSE";
        PrintMotd = true;

        # === Divers ===
        UseDNS = false;              # Pas de résolution DNS inverse (latence + info)
        GSSAPIAuthentication = false;
        KerberosAuthentication = false;
        StrictModes = true;
        AllowUsers = cfg.allowedUsers;
      };
    };

    # Le pare-feu doit autoriser le port SSH
    networking.firewall.allowedTCPPorts = [ cfg.listenPort ];

    # fail2ban pour surveiller les échecs SSH
    services.fail2ban = {
      enable = true;
      jails.sshd = ''
        enabled = true
        port = ${toString cfg.listenPort}
        filter = sshd
        logpath = /var/log/auth.log
        maxretry = 3
        bantime = 1h
      '';
    };
  };
}
