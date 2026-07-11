# ====================================================================
# Bastion NixOS — hardware-configuration.nix
# ====================================================================
# Configuration matériel pour une VM VirtualBox standard.
# ⚠️ À ajuster selon votre VM (UUID disque, type d'interface).
# Généré normalement par `nixos-generate-config` à l'installation.
# ====================================================================

{ config, lib, pkgs, modulesPath, ... }:

{
  imports = [ (modulesPath + "/profiles/qemu-guest.nix") ];

  # --- Chargeur de démarrage (GRUB sur le disque virtuel) ---
  boot.loader.grub = {
    enable = true;
    device = "/dev/sda";             # Disque principal VirtualBox
    useOSProber = false;             # Pas de multi-boot sur un bastion
  };

  boot.initrd = {
    availableKernelModules = [ "ata_piix" "ohci_pci" "ehci_pci" "ahci" "sd_mod" "sr_mod" ];
    kernelModules = [ ];
  };
  boot.kernelModules = [ "kvm-amd" "kvm-intel" ];
  boot.extraModulePackages = [ ];

  # --- Système de fichiers ---
  fileSystems."/" = {
    device = "/dev/disk/by-uuid/REPLACE_WITH_ROOT_UUID";
    fsType = "ext4";
  };

  # Swap (optionnel sur VM, mais recommandé pour la stabilité)
  swapDevices = [
    { device = "/dev/disk/by-uuid/REPLACE_WITH_SWAP_UUID"; }
  ];

  # --- Configuration VirtualBox guest ---
  virtualisation.virtualbox.guest.enable = true;

  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";
}
