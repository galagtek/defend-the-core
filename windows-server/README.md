# Windows Server 2022 — Active Directory (Zone Critique)

## Rôle

Contrôleur de domaine Active Directory, DNS et DHCP pour la **zone critique**
(VLAN 30, 10.10.30.20). Gère l'identité et la résolution de noms des serveurs.

## Pré-requis

- VM Windows Server 2022 (2 vCPU, 4 Go RAM, 40 Go disque)
- Réseau interne VirtualBox `vbox-vlan30`
- IP statique : 10.10.30.20 / Passerelle : 10.10.30.1
- OpenSSH Server installé (pour l'administration via bastion)

## Scripts PowerShell

| Script | Description |
|--------|-------------|
| `Install-ADForest.ps1` | Promotion en contrôleur de domaine (forêt) |
| `Configure-DNS-DHCP.ps1` | Configuration DNS + DHCP zone critique |
| `Install-WazuhAgent.ps1` | Déploiement agent Wazuh |
| `Harden-WindowsServer.ps1` | Durcissement CIS-like + audit |
| `Configure-GPO.ps1` | GPO de sécurité (politique mots de passe, etc.) |

## Ordre d'exécution (en administrateur)

```powershell
.\scripts\Install-ADForest.ps1 -DomainName "defendcore.local" -DSRMPassword "..."
# Redémarrage requis après promotion AD
.\scripts\Configure-DNS-DHCP.ps1
.\scripts\Install-WazuhAgent.ps1 -ManagerIp "10.10.99.10" -AgentName "win-server"
.\scripts\Harden-WindowsServer.ps1
.\scripts\Configure-GPO.ps1
```

## Administration

Connexion **uniquement** via le bastion (ProxyJump) :
```bash
ssh -J bastion Administrator@10.10.30.20
```
