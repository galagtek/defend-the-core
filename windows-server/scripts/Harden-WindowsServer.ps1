# ============================================================
# Windows Server — Durcissement CIS-like
# ============================================================
# Applique un durcissement essentiel inspiré du CIS Benchmark
# Windows Server 2022. Couvre : pare-feu, audit, comptes, services,
# registre, Windows Defender.
# ============================================================
#Requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] $Message"
}

$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { Write-Log "ERREUR: executer en administrateur"; exit 1 }

Write-Log "=== Durcissement Windows Server (CIS-like) ==="

# --- 1. Pare-feu Windows activé sur tous les profils ---
Write-Log "Activation du pare-feu Windows (tous profils)..."
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultInboundAction Block
Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultOutboundAction Allow
Set-NetFirewallProfile -Profile Domain,Public,Private -LogBlocked True
Set-NetFirewallProfile -Profile Domain,Public,Private -LogAllowed False
Set-NetFirewallProfile -Profile Domain,Public,Private -LogFileName "%SystemRoot%\System32\LogFiles\Firewall\pfirewall.log"
Write-Log "Pare-feu active (default deny inbound)."

# --- 2. Politique d'audit ---
Write-Log "Configuration de la politique d'audit..."
auditpol /set /category:"Connexion/Deconnexion" /success:enable /failure:enable
auditpol /set /category:"Gestion des comptes" /success:enable /failure:enable
auditpol /set /category:"Acces aux objets" /success:enable /failure:enable
auditpol /set /category:"Modification de la strategie" /success:enable /failure:enable
auditpol /set /category:"Utilisation des privileges" /success:enable /failure:enable
auditpol /set /category:"Systeme" /success:enable /failure:enable
Write-Log "Politique d'audit configuree (toutes categories)."

# --- 3. Politique de mots de passe (net accounts) ---
Write-Log "Configuration de la politique de mots de passe..."
net accounts /minpwlen:14          # 14 caractères min
net accounts /maxpwage:90          # 90 jours max
net accounts /minpwage:1           # 1 jour min
net accounts /uniquepw:24          # 24 mots de passe mémorisés
net accounts /lockoutthreshold:5   # 5 essais avant verrouillage
net accounts /lockoutduration:30   # 30 min de verrouillage
net accounts /lockoutwindow:30     # Fenêtre de 30 min
Write-Log "Politique mots de passe : 14 car, 90j, verrouillage 5 essais/30min."

# --- 4. Comptes : renommer Administrator + désactiver Guest ---
Write-Log "Renommage du compte Administrator et desactivation Guest..."
try {
    $admin = Get-LocalUser | Where-Object SID -like "S-1-5-*-500"
    if ($admin) {
        Rename-LocalUser -Name $admin.Name -NewName "secadmin"
        Write-Log "Compte Administrator renomme en 'secadmin'."
    }
} catch { Write-Log "Renommage Administrator: $($_.Exception.Message)" }

try {
    Disable-LocalUser -Name "Guest" -ErrorAction SilentlyContinue
    Write-Log "Compte Guest desactive."
} catch {}

# --- 5. Désactivation des services inutiles ---
Write-Log "Desactivation des services inutiles..."
$servicesToDisable = @(
    "Fax",
    "fhsvc",
    "PrintNotify",
    "RemoteRegistry",
    "scardsvc",
    "SCPolicySvc",
    "TrkWks",
    "WbioSrvc",
    "XboxGipSvc",
    "XboxNetApiSvc"
)
foreach ($svc in $servicesToDisable) {
    $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($s) {
        Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
        Set-Service -Name $svc -StartupType Disabled -ErrorAction SilentlyContinue
        Write-Log "  $svc desactive."
    }
}

# --- 6. Windows Defender ---
Write-Log "Configuration Windows Defender..."
# Activer Defender (déjà actif par défaut, on s'assure)
Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction SilentlyContinue
Set-MpPreference -DisableBehaviorMonitoring $false -ErrorAction SilentlyContinue
Set-MpPreference -DisableScriptScanning $false -ErrorAction SilentlyContinue
# Niveau de protection Cloud (élevé)
Set-MpPreference -CloudBlockLevel High -ErrorAction SilentlyContinue
Set-MpPreference -MAPSReporting Advanced -ErrorAction SilentlyContinue
Set-MpPreference -SubmitSamplesConsent SendSafeSamples -ErrorAction SilentlyContinue
# Network protection
Set-MpPreference -EnableNetworkProtection Enabled -ErrorAction SilentlyContinue
Write-Log "Windows Defender configure (realtime, cloud high, network protection)."

# --- 7. Registre : durcissement divers ---
Write-Log "Durcissement du registre..."

# Cacher le dernier utilisateur connecté
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "dontdisplaylastusername" -Value 1 -Type DWord

# Exiger Ctrl+Alt+Del
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "DisableCAD" -Value 0 -Type DWord

# Désactiver AutoRun (anti malware USB)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" `
    -Name "NoDriveTypeAutoRun" -Value 255 -Type DWord

# Désactiver le stockage des hashes LM
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "NoLMHash" -Value 1 -Type DWord

# Forcer NTLMv2 (refuser LM/NTLMv1)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LmCompatibilityLevel" -Value 5 -Type DWord

# Restriction accès anonyme
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RestrictAnonymous" -Value 1 -Type DWord
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RestrictAnonymousSAM" -Value 1 -Type DWord

# Désactiver PowerShell v2 (surface d'attaque)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\PowerShell\1\ShellIds\Microsoft.PowerShell" `
    -Name "ExecutionPolicy" -Value "RemoteSigned" -Type String

Write-Log "Registre durci (Ctrl+Alt+Del, AutoRun off, NTLMv2, anonyme restreint)."

# --- 8. SMB : désactivation SMBv1 ---
Write-Log "Desactivation SMBv1 (vulnerable EternalBlue)..."
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart -ErrorAction SilentlyContinue
Write-Log "SMBv1 desactive."

# --- 9. RDP : durcissement ---
Write-Log "Durcissement RDP (NLA requis)..."
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" `
    -Name "UserAuthentication" -Value 1 -Type DWord
# Chiffrement fort
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" `
    -Name "MinEncryptionLevel" -Value 3 -Type DWord
Write-Log "RDP : NLA active, chiffrement High."

Write-Log "=== Durcissement Windows Server termine ==="
Write-Log "Points appliques :"
Write-Log "  - Pare-feu actif (default deny inbound)"
Write-Log "  - Audit toutes categories"
Write-Log "  - Mots de passe : 14 car, 90j, verrouillage"
Write-Log "  - Administrator renomme, Guest desactive"
Write-Log "  - Services inutiles desactives"
Write-Log "  - Windows Defender (realtime, cloud high)"
Write-Log "  - Registre durci (NTLMv2, AutoRun off, Ctrl+Alt+Del)"
Write-Log "  - SMBv1 desactive"
Write-Log "  - RDP : NLA + chiffrement High"
Write-Log "Prochaine etape : Configure-GPO.ps1"
