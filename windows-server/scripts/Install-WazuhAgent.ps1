# ============================================================
# Windows Server — Installation agent Wazuh
# ============================================================
# Délègue au script commun de déploiement.
# Usage :
#   .\Install-WazuhAgent.ps1 -ManagerIp "10.10.99.10" -AgentName "win-server"
# ============================================================
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ManagerIp = "10.10.99.10",

    [Parameter(Mandatory=$false)]
    [string]$AgentName = "win-server",

    [Parameter(Mandatory=$false)]
    [string]$AgentGroup = "critical"
)

$ErrorActionPreference = "Stop"

$deployScript = Join-Path $PSScriptRoot "..\..\wazuh\agents\deploy-agent-windows.ps1"

if (Test-Path $deployScript) {
    Write-Host "Utilisation du script commun de deploiement..."
    & $deployScript -ManagerIp $ManagerIp -AgentName $AgentName -AgentGroup $AgentGroup
} else {
    Write-Host "Script commun introuvable ($deployScript)."
    Write-Host "Veuillez copier wazuh/agents/deploy-agent-windows.ps1 et l'executer."
    exit 1
}
