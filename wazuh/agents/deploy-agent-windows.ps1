# ============================================================
# Wazuh - Deploiement de l'agent sur Windows
# ============================================================
# Installe et configure l'agent Wazuh sur un hote Windows
# (Windows Server 2022, Windows 10/11). Idempotent.
#
# Usage (en administrateur) :
#   .\deploy-agent-windows.ps1 -ManagerIp "10.10.99.10" -AgentName "win-server"
#   .\deploy-agent-windows.ps1 -ManagerIp "10.10.99.10" -AgentName "win10-employe"
# ============================================================
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ManagerIp = "10.10.99.10",

    [Parameter(Mandatory=$false)]
    [string]$AgentName = $env:COMPUTERNAME,

    [Parameter(Mandatory=$false)]
    [string]$AgentGroup = "windows",

    [Parameter(Mandatory=$false)]
    [string]$WazuhVersion = "4.7.0"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] $Message"
}

# --- Verifier les privileges administrateur ---
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Log "ERREUR: Ce script doit etre execute en administrateur."
    exit 1
}

Write-Log "=== Deploiement agent Wazuh ($AgentName) ==="
Write-Log "Manager : $ManagerIp"

# --- 1. Telechargement de l'agent Wazuh ---
$installerUrl = "https://packages.wazuh.com/4.x/windows/wazuh-agent-$WazuhVersion-1.msi"
$installerPath = "$env:TEMP\wazuh-agent-$WazuhVersion.msi"

# Verifier si l'agent est deja installe
$installed = Get-Service -Name "WazuhSvc" -ErrorAction SilentlyContinue
if ($installed) {
    Write-Log "Agent Wazuh deja installe. Reconfiguration uniquement."
} else {
    Write-Log "Telechargement de l'agent Wazuh $WazuhVersion..."
    try {
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
        Write-Log "Telechargement termine : $installerPath"
    } catch {
        Write-Log "ERREUR: Echec du telechargement. Verifiez l'acces Internet."
        Write-Log $_.Exception.Message
        exit 1
    }

    # --- 2. Installation silencieuse ---
    Write-Log "Installation silencieuse de l'agent..."
    $installArgs = "/i `"$installerPath`" /qn /norestart"
    $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $installArgs -Wait -PassThru

    if ($process.ExitCode -ne 0) {
        Write-Log "ERREUR: Echec de l'installation (code $($process.ExitCode))."
        exit 1
    }
    Write-Log "Agent installe avec succes."
}

# --- 3. Configuration de l'agent ---
$configPath = "C:\Program Files (x86)\ossec-agent\ossec.conf"
Write-Log "Configuration de l'agent ($configPath)..."

if (Test-Path $configPath) {
    # Lecture de la config actuelle
    [xml]$config = Get-Content $configPath

    # Mise a jour de l'adresse du manager
    $clientNode = $config.ossec_config.client
    if ($clientNode) {
        $clientNode.address = $ManagerIp
    }

    # Ajout du nom et groupe d'agent via enrollment
    $enrollment = $config.CreateElement("enrollment")
    $nameNode = $config.CreateElement("agent_name")
    $nameNode.InnerText = $AgentName
    $groupNode = $config.CreateElement("agent_group")
    $groupNode.InnerText = $AgentGroup
    $enrollment.AppendChild($nameNode) | Out-Null
    $enrollment.AppendChild($groupNode) | Out-Null
    $config.ossec_config.AppendChild($enrollment) | Out-Null

    $config.Save($configPath)
    Write-Log "Configuration appliquee (manager=$ManagerIp, name=$AgentName, group=$AgentGroup)."
} else {
    Write-Log "ERREUR: Fichier de config introuvable ($configPath)."
    exit 1
}

# --- 4. Redemarrage du service ---
Write-Log "Redemarrage du service Wazuh..."
Restart-Service -Name "WazuhSvc" -Force
Start-Sleep -Seconds 3

$svc = Get-Service -Name "WazuhSvc"
if ($svc.Status -eq "Running") {
    Write-Log "SUCCES: Service Wazuh actif (Running)."
} else {
    Write-Log "ERREUR: Service Wazuh inactif ($($svc.Status))."
    exit 1
}

# --- 5. Configuration du pare-feu Windows (autoriser agent -> manager) ---
Write-Log "Configuration du pare-feu Windows (sortie vers manager)..."
$ruleName = "Wazuh Agent Outbound"
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if (-not $existingRule) {
    New-NetFirewallRule -DisplayName $ruleName -Direction Outbound `
        -Protocol TCP -RemotePort 1514 -RemoteAddress $ManagerIp `
        -Action Allow -Profile Any | Out-Null
    Write-Log "Regle de pare-feu ajoutee (TCP 1514 -> $ManagerIp)."
}

# --- 6. Nettoyage ---
if (Test-Path $installerPath) {
    Remove-Item $installerPath -Force
    Write-Log "Installeur temporaire supprime."
}

Write-Log "=== Agent Wazuh deploye ($AgentName) ==="
Write-Log "Verifiez sur le dashboard Wazuh : Agents > $AgentName"
Write-Log "Logs locaux : C:\Program Files (x86)\ossec-agent\ossec.log"
