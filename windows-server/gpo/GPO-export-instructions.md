# GPO exportées — Defend-The-Core

## GPO créées par `Configure-GPO.ps1`

| GPO | Description |
|-----|-------------|
| `DTC-Password-Policy` | 14 caractères min, 90 jours, complexité, 24 historique, verrouillage 5/30min |
| `DTC-Workstation-Hardening` | SMBv1 désactivé, Defender activé, AutoRun off, NLA RDP |
| `DTC-Audit-Policy` | Audit complet (logon, object access, privilege use, etc.) |
| `DTC-Software-Restriction` | Restriction logicielle (dossiers temp non exécutables) |

## Export des GPO (pour GitOps)

Une fois les GPO créées et appliquées, exportez-les pour traçabilité :

```powershell
# Export d'une GPO en backup
Backup-Gpo -Name "DTC-Password-Policy" -Path "C:\gpo-backup\"
Backup-Gpo -Name "DTC-Workstation-Hardening" -Path "C:\gpo-backup\"
Backup-Gpo -Name "DTC-Audit-Policy" -Path "C:\gpo-backup\"
Backup-Gpo -Name "DTC-Software-Restriction" -Path "C:\gpo-backup\"

# Copier le backup vers ce dossier (via bastion/scp)
# Les fichiers .pol et manifest.xml seront versionnés ici
```

## Paramètres clés appliqués

### Politique de mots de passe
- Longueur minimale : 14
- Complexité : activée (4 classes)
- Durée maximale : 90 jours
- Durée minimale : 1 jour
- Historique : 24
- Verrouillage : 5 essais / 30 minutes

### Durcissement poste de travail
- SMBv1 : désactivé (anti EternalBlue)
- Windows Defender : activé (realtime)
- AutoRun : désactivé (anti malware USB)
- RDP : NLA requis + chiffrement High
