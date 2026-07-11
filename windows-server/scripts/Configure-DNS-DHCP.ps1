# ============================================================
# Windows Server — Configuration DNS + DHCP (zone critique)
# ============================================================
# Configure le service DNS (forwarders) et le DHCP pour la zone
# critique (VLAN 30). À exécuter après la promotion AD.
#
# Usage (en administrateur) :
#   .\Configure-DNS-DHCP.ps1
# ============================================================
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$DomainName = "defendcore.internal",

    [Parameter(Mandatory=$false)]
    [string]$DnsForwarder = "1.1.1.1",

    [Parameter(Mandatory=$false)]
    [string]$DhcpScopeStart = "10.10.30.100",

    [Parameter(Mandatory=$false)]
    [string]$DhcpScopeEnd = "10.10.30.200",

    [Parameter(Mandatory=$false)]
    [string]$DhcpSubnetMask = "255.255.255.0",

    [Parameter(Mandatory=$false)]
    [string]$DhcpRouter = "10.10.30.1"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] $Message"
}

Write-Log "=== Configuration DNS + DHCP ==="

# --- 1. Configuration DNS ---
Write-Log "Configuration des forwarders DNS..."
# Forwarders : Cloudflare (privacy) + Google (fallback)
$forwarders = @("1.1.1.1", "8.8.8.8")
foreach ($fwd in $forwarders) {
    Add-DnsServerForwarder -IPAddress $fwd -ErrorAction SilentlyContinue
}
Write-Log "Forwarders DNS : $($forwarders -join ', ')"

# Zone de recherche inversée pour le VLAN 30
Write-Log "Creation de la zone de recherche inversee (10.10.30.0/24)..."
Add-DnsServerPrimaryZone -NetworkId "10.10.30.0/24" -ReplicationScope "Forest" `
    -ErrorAction SilentlyContinue
Write-Log "Zone inversee creee."

# --- 2. Installation du rôle DHCP ---
Write-Log "Installation du role DHCP..."
Install-WindowsFeature -Name DHCP -IncludeManagementTools -ErrorAction SilentlyContinue | Out-Null

# Autorisation du serveur DHCP dans AD
Write-Log "Autorisation du serveur DHCP dans AD..."
$dhcpFqdn = "$env:COMPUTERNAME.$DomainName"
try {
    Add-DhcpServerInDC -DnsName $dhcpFqdn -IPAddress "10.10.30.20" -ErrorAction SilentlyContinue
    Write-Log "Serveur DHCP autorise dans AD."
} catch {
    Write-Log "Serveur DHCP deja autorise ou echec: $($_.Exception.Message)"
}

# --- 3. Configuration du scope DHCP (VLAN 30) ---
Write-Log "Creation du scope DHCP (VLAN 30 : $DhcpScopeStart - $DhcpScopeEnd)..."
$scopeName = "VLAN30-Critique"
$scopeId = "10.10.30.0"

Add-DhcpServerv4Scope -Name $scopeName -StartRange $DhcpScopeStart `
    -EndRange $DhcpScopeEnd -SubnetMask $DhcpSubnetMask `
    -State Active -ErrorAction SilentlyContinue
Write-Log "Scope DHCP cree : $scopeName"

# Options DHCP
Set-DhcpServerv4OptionValue -ScopeId $scopeId -Router $DhcpRouter `
    -DnsServer "10.10.30.20" -DnsDomain $DomainName -ErrorAction SilentlyContinue
Write-Log "Options DHCP configurees :"
Write-Log "  - Routeur (passerelle) : $DhcpRouter"
Write-Log "  - Serveur DNS : 10.10.30.20"
Write-Log "  - Domaine DNS : $DomainName"

# Durée du bail (8h pour la zone critique)
Set-DhcpServerv4Scope -ScopeId $scopeId -LeaseDuration (New-TimeSpan -Hours 8) `
    -ErrorAction SilentlyContinue

# --- 4. Redémarrage des services ---
Write-Log "Redemarrage des services DNS et DHCP..."
Restart-Service dnsserver -Force -ErrorAction SilentlyContinue
Restart-Service dhcpserver -Force -ErrorAction SilentlyContinue

Write-Log "=== DNS + DHCP configures ==="
Write-Log "Recapitulatif :"
Write-Log "  DNS forwarders : 1.1.1.1, 8.8.8.8"
Write-Log "  DHCP scope : 10.10.30.100 - 10.10.30.200 (/24)"
Write-Log "  Domaine : $DomainName"
Write-Log "Prochaine etape : Install-WazuhAgent.ps1"
