# ============================================================
# Windows 10 — Installation agent Wazuh
# ============================================================
# Délègue au script commun de déploiement.
# Usage :
#   .\Install-WazuhAgent.ps1 -ManagerIp "10.10.99.10" -AgentName "win10-employe"
# ============================================================
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ManagerIp = "10.10.99.10",

    [Parameter(Mandatory=$false)]
    [string]$AgentName = "win10-employe",

    [Parameter(Mandatory=$false)]
    [string]$AgentGroup = "workstation"
)

$ErrorActionPreference = "Stop"

$deployScript = Join-Path $PSScriptRoot "..\..\wazuh\agents\deploy-agent-windows.ps1"

if (Test-Path $deployScript) {
    & $deployScript -ManagerIp $ManagerIp -AgentName $AgentName -AgentGroup $AgentGroup
} else {
    Write-Host "Script commun introuvable. Copiez deploy-agent-windows.ps1 manuellement."
    exit 1
}
