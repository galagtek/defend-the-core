# ============================================================
# Windows Server — Configuration des GPO de sécurité
# ============================================================
# Crée des GPO de sécurité au niveau du domaine pour appliquer
# des politiques uniformes à tous les postes et serveurs.
#
# Usage (en administrateur, sur le contrôleur de domaine) :
#   .\Configure-GPO.ps1
# ============================================================
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$DomainName = "defendcore.internal"
)

$ErrorActionPreference = "Stop"

# Importer le module GroupPolicy
Import-Module GroupPolicy -ErrorAction Stop

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] $Message"
}

$domain = "DC=" + ($DomainName -replace '\.', ',DC=')
$domainDn = $domain

Write-Log "=== Configuration des GPO de securite ==="
Write-Log "Domaine : $DomainName ($domainDn)"

# ============================================================
# GPO 1 : Politique de mots de passe (Default Domain Policy)
# ============================================================
Write-Log "Creation GPO 'DTC-Password-Policy'..."
$gpoName1 = "DTC-Password-Policy"
try {
    $existing = Get-GPO -Name $gpoName1 -ErrorAction SilentlyContinue
    if (-not $existing) {
        New-GPO -Name $gpoName1 -Comment "Politique mots de passe Defend-The-Core" | Out-Null
    }
    # Configuration via registry (les paramètres de mot de passe sont dans la sécurité)
    # On utilise secedit pour appliquer les politiques de compte
    $secedit = @"
[Unicode]
Unicode=yes
[Version]
signature="`$CHICAGO`$"
Revision=1
[Profile Description]
Description=Defend-The-Core password policy
[System Access]
MinimumPasswordAge = 1
MaximumPasswordAge = 90
MinimumPasswordLength = 14
PasswordComplexity = 1
PasswordHistorySize = 24
LockoutBadCount = 5
ResetLockoutCount = 30
LockoutDuration = 30
"@
    $secedit | Out-File "$env:TEMP\dtc-security.inf" -Encoding Unicode
    secedit /configure /db "$env:TEMP\dtc-security.sdb" /cfg "$env:TEMP\dtc-security.inf" /quiet
    Write-Log "GPO mots de passe : 14 car, 90j, complexite, verrouillage 5/30min."
} catch {
    Write-Log "GPO mots de passe: $($_.Exception.Message)"
}

# ============================================================
# GPO 2 : Durcissement Windows (appliqué aux postes clients)
# ============================================================
Write-Log "Creation GPO 'DTC-Workstation-Hardening'..."
$gpoName2 = "DTC-Workstation-Hardening"
try {
    $existing = Get-GPO -Name $gpoName2 -ErrorAction SilentlyContinue
    if (-not $existing) {
        New-GPO -Name $gpoName2 -Comment "Durcissement des postes de travail" | Out-Null
    }
    $gpo2 = Get-GPO -Name $gpoName2

    # Désactiver SMBv1 sur les clients
    Set-GPRegistryValue -Name $gpoName2 `
        -Key "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
        -ValueName "SMB1" -Type DWord -Value 0

    # Activer Windows Defender
    Set-GPRegistryValue -Name $gpoName2 `
        -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" `
        -ValueName "DisableAntiSpyware" -Type DWord -Value 0

    # Désactiver AutoRun
    Set-GPRegistryValue -Name $gpoName2 `
        -Key "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" `
        -ValueName "NoDriveTypeAutoRun" -Type DWord -Value 255

    # Exiger NLA pour RDP
    Set-GPRegistryValue -Name $gpoName2 `
        -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" `
        -ValueName "UserAuthentication" -Type DWord -Value 1

    Write-Log "GPO workstation hardening cree (SMBv1 off, Defender, AutoRun off, NLA)."

    # Lier à l'OU des postes (à créer selon votre structure AD)
    # New-GPLink -Name $gpoName2 -Target "OU=Workstations,$domainDn"
} catch {
    Write-Log "GPO workstation: $($_.Exception.Message)"
}

# ============================================================
# GPO 3 : Audit et journalisation
# ============================================================
Write-Log "Creation GPO 'DTC-Audit-Policy'..."
$gpoName3 = "DTC-Audit-Policy"
try {
    $existing = Get-GPO -Name $gpoName3 -ErrorAction SilentlyContinue
    if (-not $existing) {
        New-GPO -Name $gpoName3 -Comment "Politique d'audit centralisee" | Out-Null
    }

    # Activer l'audit avancé
    $auditKey = "HKLM\SYSTEM\CurrentControlSet\Control\Lsa"
    $auditCategories = @{
        "AuditLogon" = 3              # Success + Failure
        "AuditObjectAccess" = 3
        "AuditPrivilegeUse" = 3
        "AuditPolicyChange" = 3
        "AuditAccountManagement" = 3
        "AuditProcessTracking" = 2    # Success only
        "AuditSystemEvents" = 3
    }
    foreach ($cat in $auditCategories.GetEnumerator()) {
        Set-GPRegistryValue -Name $gpoName3 -Key $auditKey `
            -ValueName $cat.Key -Type DWord -Value $cat.Value -ErrorAction SilentlyContinue
    }
    Write-Log "GPO audit cree (toutes categories success+failure)."
} catch {
    Write-Log "GPO audit: $($_.Exception.Message)"
}

# ============================================================
# GPO 4 : Restriction d'installation logicielle
# ============================================================
Write-Log "Creation GPO 'DTC-Software-Restriction'..."
$gpoName4 = "DTC-Software-Restriction"
try {
    $existing = Get-GPO -Name $gpoName4 -ErrorAction SilentlyContinue
    if (-not $existing) {
        New-GPO -Name $gpoName4 -Comment "Restriction logicielle (Software Restriction Policy)" | Out-Null
    }

    # Empêcher l'exécution depuis %TEMP% et le dossier Downloads (anti-malware)
    $srpKey = "HKLM\SOFTWARE\Policies\Microsoft\Windows\Safer\CodeIdentifiers"
    Set-GPRegistryValue -Name $gpoName4 -Key $srpKey `
        -ValueName "DefaultLevel" -Type DWord -Value 262144  # Untrusted by default
    Set-GPRegistryValue -Name $gpoName4 -Key $srpKey `
        -ValueName "TransparentEnabled" -Type DWord -Value 1
    Write-Log "GPO software restriction creee."
} catch {
    Write-Log "GPO software restriction: $($_.Exception.Message)"
}

# ============================================================
# Lien des GPO au domaine
# ============================================================
Write-Log "Liaison des GPO au domaine..."
$gpos = @($gpoName1, $gpoName2, $gpoName3, $gpoName4)
foreach ($g in $gpos) {
    try {
        $existingLink = Get-GPLink -Name $g -Target $domainDn -ErrorAction SilentlyContinue
        if (-not $existingLink) {
            New-GPLink -Name $g -Target $domainDn -LinkEnabled Yes | Out-Null
            Write-Log "  $g liee au domaine."
        } else {
            Write-Log "  $g deja liee."
        }
    } catch {
        Write-Log "  Lien $g : $($_.Exception.Message)"
    }
}

Write-Log "=== GPO de securite configurees ==="
Write-Log "GPO creees :"
Write-Log "  - DTC-Password-Policy (14 car, 90j, complexite)"
Write-Log "  - DTC-Workstation-Hardening (SMBv1 off, Defender, NLA)"
Write-Log "  - DTC-Audit-Policy (audit complet)"
Write-Log "  - DTC-Software-Restriction (restriction logicielle)"
Write-Log "Verifiez : GPMC (gpmc.msc) > Domaine > Group Policy Objects"
