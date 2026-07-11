# ============================================================
# Windows 10 — Durcissement poste employé
# ============================================================
# Applique un durcissement de base sur le poste employé :
# pare-feu, Windows Defender, SMBv1 off, AutoRun off, etc.
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

Write-Log "=== Durcissement Windows 10 (poste employe) ==="

# --- 1. Pare-feu Windows activé ---
Write-Log "Activation du pare-feu (tous profils)..."
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultInboundAction Block
Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultOutboundAction Allow
Write-Log "Pare-feu active (default deny inbound)."

# --- 2. Windows Defender ---
Write-Log "Configuration Windows Defender..."
Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction SilentlyContinue
Set-MpPreference -DisableBehaviorMonitoring $false -ErrorAction SilentlyContinue
Set-MpPreference -CloudBlockLevel High -ErrorAction SilentlyContinue
Set-MpPreference -MAPSReporting Advanced -ErrorAction SilentlyContinue
Set-MpPreference -EnableNetworkProtection Enabled -ErrorAction SilentlyContinue
# Protection contre les ransomwares (controlled folder access)
Set-MpPreference -EnableControlledFolderAccess Enabled -ErrorAction SilentlyContinue
Write-Log "Defender : realtime, cloud high, network protection, anti-ransomware."

# --- 3. SMBv1 désactivé (anti EternalBlue) ---
Write-Log "Desactivation SMBv1..."
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force -ErrorAction SilentlyContinue
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart -ErrorAction SilentlyContinue
Write-Log "SMBv1 desactive."

# --- 4. AutoRun désactivé (anti malware USB) ---
Write-Log "Desactivation AutoRun..."
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" `
    -Name "NoDriveTypeAutoRun" -Value 255 -Type DWord
Write-Log "AutoRun desactive."

# --- 5. Politique d'audit ---
Write-Log "Configuration de la politique d'audit..."
auditpol /set /category:"Connexion/Deconnexion" /success:enable /failure:enable
auditpol /set /category:"Gestion des comptes" /success:enable /failure:enable
auditpol /set /category:"Acces aux objets" /success:enable /failure:enable
auditpol /set /category:"Utilisation des privileges" /success:enable /failure:enable
Write-Log "Audit active (logon, account mgmt, object access, privilege use)."

# --- 6. UAC activé (niveau élevé) ---
Write-Log "Configuration UAC (niveau eleve)..."
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "EnableLUA" -Value 1 -Type DWord
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "ConsentPromptBehaviorAdmin" -Value 2 -Type DWord  # Secure Desktop
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "PromptOnSecureDesktop" -Value 1 -Type DWord
Write-Log "UAC active (secure desktop)."

# --- 7. Désactivation des services inutiles ---
Write-Log "Desactivation des services inutiles..."
$services = @("Fax","PrintNotify","RemoteRegistry","XboxGipSvc","XboxNetApiSvc")
foreach ($svc in $services) {
    $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($s) {
        Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
        Set-Service -Name $svc -StartupType Disabled -ErrorAction SilentlyContinue
        Write-Log "  $svc desactive."
    }
}

# --- 8. Windows Update automatique ---
Write-Log "Configuration Windows Update (automatique)..."
$wuKey = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
if (-not (Test-Path $wuKey)) { New-Item -Path $wuKey -Force | Out-Null }
Set-ItemProperty -Path $wuKey -Name "NoAutoUpdate" -Value 0 -Type DWord
Set-ItemProperty -Path $wuKey -Name "AUOptions" -Value 4 -Type DWord  # Auto download + install
Write-Log "Windows Update : automatique (download + install)."

Write-Log "=== Durcissement Windows 10 termine ==="
Write-Log "Points appliques : pare-feu, Defender (+anti-ransomware), SMBv1 off,"
Write-Log "AutoRun off, audit, UAC secure desktop, services inutiles off, MAJ auto."
