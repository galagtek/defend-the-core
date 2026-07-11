# ============================================================
# Windows Server — Promotion en contrôleur de domaine (forêt AD)
# ============================================================
# Crée une nouvelle forêt Active Directory. À exécuter AVANT les
# autres scripts (redémarrage requis après promotion).
#
# Usage (en administrateur) :
#   .\Install-ADForest.ps1 -DomainName "defendcore.internal" `
#                           -NetBIOSName "DEFENDCORE" `
#                           -DSRMPassword "MotDePasseFort!"
# ============================================================
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$DomainName = "defendcore.internal",

    [Parameter(Mandatory=$false)]
    [string]$NetBIOSName = "DEFENDCORE",

    [Parameter(Mandatory=$true)]
    [string]$DSRMPassword,

    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "10.10.50.20"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] $Message"
}

# --- Verifier administrateur ---
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { Write-Log "ERREUR: executer en administrateur"; exit 1 }

Write-Log "=== Promotion en controleur de domaine ==="
Write-Log "Domaine : $DomainName (NetBIOS: $NetBIOSName)"

# --- 1. Configuration IP statique ---
Write-Log "Configuration IP statique ($ServerIP)..."
$adapter = Get-NetAdapter | Where-Object Status -eq "Up" | Select-Object -First 1
if ($adapter) {
    New-NetIPAddress -InterfaceIndex $adapter.ifIndex `
        -IPAddress $ServerIP -PrefixLength 24 `
        -DefaultGateway "10.10.30.1" -ErrorAction SilentlyContinue | Out-Null
    Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex `
        -ServerAddresses "127.0.0.1","10.10.99.10" -ErrorAction SilentlyContinue
    Write-Log "IP statique configure."
}

# --- 2. Renommage du serveur ---
$desiredName = "DC01"
if ($env:COMPUTERNAME -ne $desiredName) {
    Write-Log "Renommage du serveur en $desiredName..."
    Rename-Computer -NewName $desiredName -Force -PassThru | Out-Null
    Write-Log "Redemarrage necessaire avant promotion. Relancez le script apres redemarrage."
    Write-Log "Execution : Restart-Computer, puis relancez ce script."
    # Si premier passage, on ne continue pas
    if (-not (Get-Command -ErrorAction SilentlyContinue)) {}
}

# --- 3. Installation des roles AD DS ---
Write-Log "Installation du role AD-Domain-Services..."
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools -ErrorAction SilentlyContinue | Out-Null
Write-Log "Role AD-Domain-Services installe."

# --- 4. Vérification si déjà contrôleur ---
$adInstalled = Get-ADDomain -ErrorAction SilentlyContinue
if ($adInstalled) {
    Write-Log "Le serveur est deja un controleur de domaine ($($adInstalled.DNSRoot))."
    Write-Log "Pour recreer la foret, demotez d'abord le serveur."
    exit 0
}

# --- 5. Configuration du mot de passe DSRM ---
$dsrmSecureString = ConvertTo-SecureString $DSRMPassword -AsPlainText -Force

# --- 6. Promotion en forêt ---
Write-Log "Creation de la foret $DomainName..."
try {
    Install-ADDSForest `
        -DomainName $DomainName `
        -DomainNetbiosName $NetBIOSName `
        -SafeModeAdministratorPassword $dsrmSecureString `
        -InstallDns:$true `
        -NoRebootOnCompletion:$false `
        -Force:$true
    Write-Log "Foret creee. Le serveur va redemarrer."
} catch {
    Write-Log "ERREUR lors de la promotion AD : $($_.Exception.Message)"
    exit 1
}

# Le redémarrage est automatique après Install-ADDSForest
Write-Log "=== Promotion AD terminee (redemarrage automatique) ==="
Write-Log "Apres redemarrage : Configure-DNS-DHCP.ps1"
