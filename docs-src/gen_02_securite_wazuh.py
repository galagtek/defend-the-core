#!/usr/bin/env python3
"""
Générateur PDF : Annexe 2 — Sécurité & Wazuh (SIEM/XDR)
Couvre : rôle du SIEM, architecture Wazuh (Manager/Indexer/Dashboard),
déploiement manager + agents, règles de corrélation personnalisées,
active response (blocage automatique via API OPNsense), SCA, dashboards,
choix Wazuh vs alternatives.
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_common import *
from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable, Preformatted
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle

register_fonts()
styles = get_styles()

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'docs', '02_securite_wazuh.pdf')

doc = build_doc(OUTPUT, "Defend-The-Core — Sécurité & Wazuh")
story = []

# Entités XML construites à l'exécution. Les valeurs "&", "<", ">"
# écrites en clair dans la source seraient décodées en &, <, > par le script
# code.sanitize, ce qui casserait le parseur XML de ReportLab. On les assemble
# donc à partir de morceaux neutres.
AMP = chr(38) + "amp;"   # -> "&" à l'exécution
LT  = chr(38) + "lt;"    # -> "<"  à l'exécution
GT  = chr(38) + "gt;"    # -> ">"  à l'exécution

# Style monospace préservant les espaces (alignement des diagrammes / code).
_pre_style = ParagraphStyle(
    name='CodePre', fontName='CodeFont', fontSize=8.0, leading=10.5,
    textColor=TEXT_PRIMARY, leftIndent=12, rightIndent=12,
    spaceBefore=6, spaceAfter=6, backColor=BG_PAGE,
    borderColor=BG_SURFACE, borderWidth=0.5, borderPadding=6,
)


def code_para(text):
    """Bloc de code préformaté : préserve l'indentation et les espaces
    (style <pre>), sans interpréter le XML. Aucune échappement nécessaire."""
    return Preformatted(text, _pre_style)


# ============================================================
# PAGE DE TITRE
# ============================================================
story.append(Spacer(1, 80))
story.append(Paragraph("Defend-The-Core", styles['title']))
story.append(HRFlowable(width="40%", thickness=2, color=ACCENT, spaceBefore=6, spaceAfter=12))
story.append(Paragraph("Annexe 2 : Sécurité " + AMP + " Wazuh (SIEM/XDR)", styles['subtitle']))
story.append(Spacer(1, 20))
story.append(Paragraph(
    "Surveillance centralisée, corrélation d'événements et réaction "
    "automatique au sein du VLAN 99",
    ParagraphStyle('Desc', fontName='BodyFont', fontSize=11, leading=16,
                   textColor=TEXT_MUTED, alignment=TA_LEFT)
))
story.append(Spacer(1, 40))
story.append(Paragraph(
    "SIEM/XDR · Active Response · MITRE ATT" + AMP + "CK · CIS Benchmark · OPNsense API",
    ParagraphStyle('Tags', fontName='HeadFont', fontSize=10, leading=14,
                   textColor=ACCENT, alignment=TA_LEFT)
))
story.append(PageBreak())

# ============================================================
# TABLE DES MATIÈRES
# ============================================================
story.append(Paragraph("Table des matières", styles['h1']))
toc = TableOfContents()
toc.levelStyles = [styles['toc_h1'], styles['toc_h2']]
story.append(toc)
story.append(PageBreak())

# ============================================================
# 1. RÔLE DU SIEM DANS L'ARCHITECTURE
# ============================================================
story.append(add_heading("1. Rôle du SIEM dans l'architecture", styles, 0))
story.append(Paragraph(
    "Un pare-feu en <b>default-deny</b> et un cloisonnement rigoureux réduisent "
    "la surface d'attaque, mais ils ne détectent pas une compromission en cours. "
    "C'est le rôle du SIEM (<i>Security Information and Event Management</i>) : "
    "centraliser les journaux de l'ensemble des machines, les corrélérer et "
    "déclencher une réponse — y compris automatique — lorsqu'un comportement "
    "suspect est identifié.",
    styles['body']
))

story.append(add_heading("1.1. Corrélation vs simple collecte de logs", styles, 1))
story.append(Paragraph(
    "Une simple agrégation de journaux (rsyslog vers un serveur central) ne suffit "
    "pas : elle produit des milliers de lignées brutes qu'aucun humain ne peut "
    "relire. Le SIEM ajoute une couche d'<b>analyse</b> : il applique des règles "
    "de corrélation qui croisent plusieurs événements pour en déduire une alerte "
    "exploitable.",
    styles['body']
))
story.append(Paragraph(
    "Exemple : 5 échecs SSH isolés en une heure depuis une même IP ne sont qu'un "
    "bruit de fond. <b>Cinq échecs suivis d'un succès</b> depuis cette même IP "
    "deviennent, après corrélation, une alerte de niveau 12 : <i>bruteforce SSH "
    "abouti</i>. La corrélation transforme des signaux faibles en une détection "
    "forte.",
    styles['callout']
))

story.append(add_heading("1.2. Réaction automatique (active response)", styles, 1))
story.append(Paragraph(
    "Au-delà de la détection, Wazuh embarque un moteur d'<b>active response</b> : "
    "lorsqu'une règle de niveau élevé se déclenche, un script peut être exécuté "
    "automatiquement sur le manager pour, par exemple, bloquer l'IP attaquante "
    "au pare-feu via l'API OPNsense. La boucle <b>détection → décision → "
    "blocage</b> se ferme sans intervention humaine, en quelques secondes.",
    styles['body']
))

story.append(add_heading("1.3. Place dans le VLAN 99", styles, 1))
story.append(Paragraph(
    "Wazuh est déployé sur le <b>VLAN 99 (admin/SIEM)</b>, la zone de confiance "
    "maximale. Toutes les VMs (VLANs 10, 20, 30) expédient leurs journaux vers "
    "l'adresse <font name='CodeFont'>10.10.99.10</font> sur les ports 514 (syslog "
    "OPNsense) et 1514 (agents Wazuh). Le flux entrant vers le SIEM est le seul "
    "autorisé depuis les zones moins fiables vers le VLAN 99 — il est strictement "
    "unidirectionnel : le SIEM écoute, il n'initie jamais de connexion vers les "
    "VLANs clients, sauf pour la remédiation via l'API OPNsense.",
    styles['body']
))

# ============================================================
# 2. ARCHITECTURE WAZUH
# ============================================================
story.append(add_heading("2. Architecture Wazuh", styles, 0))
story.append(Paragraph(
    "Wazuh est organisé en <b>trois composants</b> distincts, installables sur un "
    "hôte unique (déploiement monosite) ou répartis sur plusieurs nœuds (cluster). "
    "Dans le cadre de Defend-The-Core, les trois tournent sur la même VM "
    "Ubuntu 22.04 (10.10.99.10), le tout piloté par le script d'installation "
    "officiel de l'éditeur.",
    styles['body']
))

story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 1 — Composants de la stack Wazuh</b>", styles['caption']))
comp_data = [
    ["Composant", "Rôle", "Technologie", "Port"],
    ["Manager", "Collecte, décodage, corrélation, active response",
     "Wazuh Server (C/OSSEC)", "1514/udp, 1515/tcp"],
    ["Indexer", "Stockage et indexation des alertes",
     "OpenSearch (fork Elastic)", "9200/tcp"],
    ["Dashboard", "Visualisation, dashboards, SCA",
     "OpenSearch Dashboards (Kibana)", "443/tcp"],
]
story.append(make_table(comp_data, col_ratios=[0.16, 0.34, 0.28, 0.22]))
story.append(Spacer(1, 12))

story.append(add_heading("2.1. Flux de traitement (diagramme texte)", styles, 1))
story.append(Paragraph(
    "Le diagramme ci-dessous décrit le cheminement complet d'un événement, depuis "
    "sa production sur une VM jusqu'au blocage automatique de l'attaquant :",
    styles['body']
))
diagram = (
    "  VMs (VLAN 10/20/30)        OPNsense (VLAN edge)        Wazuh Manager\n"
    "  +-----------------+         +------------------+        +-------------------+\n"
    "  | agent Wazuh ----+-------->| syslog 514/udp --+------->| écoute 514/1514  |\n"
    "  | auditd, sshd... |         | (logs firewall)  |        | decoders         |\n"
    "  +-----------------+         +------------------+        | rules (XML)      |\n"
    "                                                          |  | corrélation   |\n"
    "                                                          |  v               |\n"
    "                                                          | alertes -> Indexer (9200)\n"
    "                                                          |  |  niveau >= 10 |\n"
    "                                                          |  v               |\n"
    "                                                          | active response  |\n"
    "                                                          |  | extract IP    |\n"
    "                                                          |  v               |\n"
    "  <-- block <-----+----------| API OPNsense <----+--------| block-attacker.sh|\n"
    "  alias wazuh_blocked_ips     (REST, 443)         |       +-------------------+\n"
    "  règle firewall drop                             |\n"
    "                                                   v\n"
    "                                              Dashboard (443) : alertes, SCA"
)
story.append(code_para(diagram))
story.append(Paragraph(
    "Figure 1 — Flux : logs de toutes les VMs → Wazuh (514/1514) → corrélation → "
    "alertes → active response → API OPNsense → alias dynamique → blocage.",
    styles['caption']
))

# ============================================================
# 3. DÉPLOIEMENT
# ============================================================
story.append(add_heading("3. Déploiement du manager", styles, 0))
story.append(Paragraph(
    "Le déploiement s'appuie sur le script d'installation officiel "
    "<font name='CodeFont'>install-wazuh-manager.sh</font>, fourni par l'éditeur "
    "et reposant sur le dépôt <font name='CodeFont'>apt</font> de Wazuh. Ce script "
    "installe en une passe les trois composants (Manager, Indexer, Dashboard) et "
    "génère automatiquement les mots de passe des comptes internes.",
    styles['body']
))

story.append(add_heading("3.1. Pré-requis", styles, 1))
prereq_data = [
    ["Ressource", "Valeur", "Justification"],
    ["RAM", "8 Go", "Indexer OpenSearch est gourmand en mémoire (JVM heap)"],
    ["CPU", "4 vCPU", "Corrélation + indexation + dashboard en parallèle"],
    ["Disque", "50 Go", "Rétention des alertes (rotation 30 jours)"],
    ["OS", "Ubuntu 22.04 LTS", "Supporté officiellement par le dépôt Wazuh"],
    ["Réseau", "VLAN 99, IP fixe .99.10", "Isolation en zone de confiance maximale"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 2 — Pré-requis matériel et système</b>", styles['caption']))
story.append(make_table(prereq_data, col_ratios=[0.18, 0.22, 0.60]))

story.append(add_heading("3.2. Installation via dépôt officiel", styles, 1))
story.append(Paragraph(
    "Le script ajoute la clé GPG et le dépôt Wazuh, puis installe les paquets. "
    "Extrait représentatif :",
    styles['body']
))
install_code = (
    "#!/usr/bin/env bash\n"
    "# install-wazuh-manager.sh — déploiement monosite\n"
    "set -euo pipefail\n"
    "\n"
    "# 1. Ajout du dépôt apt officiel Wazuh\n"
    "curl -sO https://packages.wazuh.com/key/GPG-KEY-WAZUH\n"
    "gpg --dearmor -o /usr/share/keyrings/wazuh.gpg GPG-KEY-WAZUH\n"
    'echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] \\\n'
    '  https://packages.wazuh.com/4.x/apt stable main" \\\n'
    "  > /etc/apt/sources.list.d/wazuh.list\n"
    "apt-get update\n"
    "\n"
    "# 2. Installation des trois composants\n"
    "apt-get install -y wazuh-manager wazuh-indexer wazuh-dashboard\n"
    "\n"
    "# 3. Génération des mots de passe (admin, kibanaserver...)\n"
    "/usr/share/wazuh-indexer/bin/indexer-security-init.sh\n"
    "/usr/share/wazuh-manager/scripts/wazuh-passwords-tool.sh -a\n"
    "\n"
    "systemctl enable --now wazuh-manager wazuh-indexer wazuh-dashboard"
)
story.append(code_para(install_code))

story.append(add_heading("3.3. Activation du syslog entrant pour OPNsense", styles, 1))
story.append(Paragraph(
    "OPNsense ne dispose pas d'agent Wazuh : il envoie ses journaux par syslog "
    "UDP. Il faut donc configurer le manager pour qu'il écoute sur le port "
    "<b>514/udp</b> et qu'il décode le format CEF/syslog du pare-feu. Cela se "
    "déclare dans <font name='CodeFont'>/var/ossec/etc/ossec.conf</font> :",
    styles['body']
))
syslog_code = (
    "<!-- ossec.conf : écoute syslog entrant pour OPNsense -->\n"
    "<remote>\n"
    "  <connection>syslog</connection>\n"
    "  <port>514</port>\n"
    "  <protocol>udp</protocol>\n"
    "  <allowed-ips>10.10.99.1/32</allowed-ips>   <!-- OPNsense -->\n"
    "  <local_ip>10.10.99.10</local_ip>\n"
    "</remote>"
)
story.append(code_para(syslog_code))
story.append(Paragraph(
    "Côté OPNsense, une règle d'export syslog (Interface " + GT + " Logs " + GT + " Settings) "
    "enverra les événements de firewall, IDS et auth vers 10.10.99.10:514.",
    styles['body']
))

# ============================================================
# 4. DÉPLOIEMENT DES AGENTS
# ============================================================
story.append(add_heading("4. Déploiement des agents", styles, 0))
story.append(Paragraph(
    "Chaque machine surveillée reçoit un <b>agent Wazuh</b>, processus léger qui "
    "collecte les logs locaux (auth, auditd, syslog applicatif), les pré-traite "
    "et les envoie chiffrés au manager sur le port 1514. Les agents sont répartis "
    "en <b>groupes</b> afin d'appliquer des configurations et des SCA différents "
    "selon le profil de la machine.",
    styles['body']
))

story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 3 — Agents déployés</b>", styles['caption']))
agents_data = [
    ["Machine", "OS", "Script de déploiement", "Groupe"],
    ["Ubuntu (serveur web+BDD)", "Ubuntu 22.04", "deploy-agent-linux.sh", "linux, critical"],
    ["Win Server (AD/DNS/DHCP)", "Windows Server 2022", "deploy-agent-windows.ps1", "windows, critical"],
    ["Bastion NixOS", "NixOS", "deploy-agent-linux.sh", "linux, admin"],
    ["Win 10 (poste employé)", "Windows 10", "deploy-agent-windows.ps1", "windows, workstation"],
    ["Kali (démo attaque)", "Kali Linux", "deploy-agent-linux.sh", "linux, workstation"],
]
story.append(make_table(agents_data, col_ratios=[0.26, 0.18, 0.30, 0.26]))
story.append(Spacer(1, 10))

story.append(add_heading("4.1. Script Linux (Debian / RPM / NixOS)", styles, 1))
story.append(Paragraph(
    "Le script <font name='CodeFont'>deploy-agent-linux.sh</font> détecte la "
    "famille de distribution et branche le bon gestionnaire de paquets. NixOS, "
    "qui ne supporte pas les binaires précompilés Wazuh, est géré via le module "
    "Nix déclaratif <font name='CodeFont'>services.wazuh-agent</font> dans "
    "<font name='CodeFont'>configuration.nix</font>.",
    styles['body']
))
linux_code = (
    "#!/usr/bin/env bash\n"
    "# deploy-agent-linux.sh — installe l'agent Wazuh sur Linux\n"
    'MANAGER_IP="10.10.99.10"\n'
    'GROUP="${1:-linux}"\n'
    "\n"
    "if grep -qi nixos /etc/os-release; then\n"
    "  # NixOS : configuration déclarative (immuable)\n"
    "  echo 'services.wazuh-agent.enable = true;' >> /etc/nixos/wazuh.nix\n"
    '  echo \'services.wazuh-agent.settings.client.address = "\'$MANAGER_IP\'";\' \\\n'
    "    >> /etc/nixos/wazuh.nix\n"
    "  nixos-rebuild switch\n"
    "elif grep -qi debian /etc/os-release; then\n"
    "  curl -so wazuh-agent.deb \\\n"
    "    https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/\n"
    "    wazuh-agent_4.7.0-1_amd64.deb\n"
    '  WAZUH_MANAGER="$MANAGER_IP" WAZUH_GROUP="$GROUP" dpkg -i wazuh-agent.deb\n'
    "  systemctl enable --now wazuh-agent\n"
    "else  # famille RPM (RHEL/Fedora/CentOS)\n"
    "  rpm -i https://packages.wazuh.com/4.x/yum/wazuh-agent-4.7.0-1.x86_64.rpm\n"
    '  sed -i "s/MANAGER_IP/$MANAGER_IP/" /var/ossec/etc/ossec.conf\n'
    "  systemctl enable --now wazuh-agent\n"
    "fi"
)
story.append(code_para(linux_code))

story.append(add_heading("4.2. Script Windows (PowerShell)", styles, 1))
win_code = (
    "# deploy-agent-windows.ps1 — agent Wazuh sur Windows\n"
    '$ManagerIP = "10.10.99.10"\n'
    "$Group     = if ($args[0]) { $args[0] } else { \"windows\" }\n"
    "\n"
    'Invoke-WebRequest -Uri "https://packages.wazuh.com/4.x/windows/wazuh-agent-4.7.0-1.msi" `\n'
    '  -OutFile "$env:TEMP\\wazuh-agent.msi"\n'
    "\n"
    'msiexec /i "$env:TEMP\\wazuh-agent.msi" `\n'
    '  /q WAZUH_MANAGER="$ManagerIP" WAZUH_REGISTRATION_SERVER="$ManagerIP" `\n'
    '  WAZUH_AGENT_GROUP="$Group"\n'
    "\n"
    "Start-Service WazuhSvc\n"
    "Set-Service WazuhSvc -StartupType Automatic"
)
story.append(code_para(win_code))

story.append(add_heading("4.3. Groupes d'agents", styles, 1))
story.append(Paragraph(
    "Les groupes permettent de pousser des <font name='CodeFont'>shared.conf</font> "
    "et des policies SCA différenciés. Cinq groupes sont définis :",
    styles['body']
))
groups = [
    "<b>linux</b> — configuration de base pour tous les agents Linux (auditd, syslog).",
    "<b>windows</b> — collecte EventLog, Sysmon, Defender sur les postes Windows.",
    "<b>critical</b> — machines du VLAN 30 (serveurs métier) : SCA CIS strict, alertes niveau +2.",
    "<b>admin</b> — bastion NixOS : surveillance renforcée des commandes sudo et des modifications système.",
    "<b>workstation</b> — postes utilisateur (VLAN 10) : détection d'exécution anormale, USB, etc.",
]
for g in groups:
    story.append(Paragraph(f"• {g}", styles['bullet']))

# ============================================================
# 5. RÈGLES DE CORRÉLATION PERSONNALISÉES
# ============================================================
story.append(add_heading("5. Règles de corrélation personnalisées", styles, 0))
story.append(Paragraph(
    "Wazuh embarque plusieurs milliers de règles OSSEC couvrant les usages "
    "courants. Pour le projet Defend-The-Core, des règles <b>custom</b> (IDs "
    "100100 à 100900) sont ajoutées dans "
    "<font name='CodeFont'>/var/ossec/etc/rules/local_rules.xml</font>. Elles "
    "ciblent les scénarios d'attaque spécifiques au lab et sont annotées avec "
    "les techniques <b>MITRE ATT" + AMP + "CK</b> correspondantes.",
    styles['body']
))

story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 4 — Règles de corrélation personnalisées</b>", styles['caption']))
rules_data = [
    ["ID", "Niveau", "Déclencheur", "MITRE ATT" + AMP + "CK"],
    ["100100", "10", "Bruteforce SSH : 5 échecs puis 1 succès / 1 min", "T1110 Brute Force"],
    ["100200", "7", "Scan Nmap détecté (auditd connect() sur plage)", "T1046 Network Service Discovery"],
    ["100300", "12", "Mouvement latéral : SSH vers un autre VLAN depuis un poste", "T1021 Remote Services"],
    ["100400", "11", "Modification de fichier de config système (sshd, sudoers)", "T1543.002 Persistence"],
    ["100500", "12", "Persistance / backdoor : cron atypique ou clé SSH ajoutée", "T1053.003 Cron"],
    ["100600", "10", "Désactivation d'UFW ou de auditd", "T1562 Impair Defenses"],
    ["100700", "9", "Exécution de reverse shell (bash -i " + GT + AMP + " /dev/tcp)", "T1059 Command " + AMP + " Scripting"],
    ["100800", "11", "Création de compte utilisateur en dehors des heures ouvrées", "T1136 Create Account"],
    ["100900", "13", "Plusieurs règles critiques (100300+100500) en 5 min", "TA0001 Initial Access"],
]
story.append(make_table(rules_data, col_ratios=[0.10, 0.10, 0.48, 0.32]))
story.append(Spacer(1, 10))

story.append(add_heading("5.1. Extrait XML — règle bruteforce SSH", styles, 1))
story.append(Paragraph(
    "La règle 100100 illustre la corrélation : elle se déclenche quand la règle "
    "native OSSEC <font name='CodeFont'>5712</font> (authentification SSH "
    "réussie) suit, dans un délai d'une minute, au moins cinq occurrences de la "
    "règle <font name='CodeFont'>5710</font> (échec SSH) depuis la même IP "
    "source.",
    styles['body']
))
rule_xml = (
    "<!-- local_rules.xml : bruteforce SSH abouti -->\n"
    '<group name="local,sshd,">\n'
    '  <rule id="100100" level="10">\n'
    "    <if_matched_sid>5712</if_matched_sid>\n"
    "    <if_matched_group>authentication_success</if_matched_group>\n"
    "    <same_source_ip />\n"
    "    <description>SSH bruteforce réussi: 5 échecs puis un succès</description>\n"
    "    <mitre>\n"
    "      <id>T1110</id>\n"
    "    </mitre>\n"
    "    <options>alert_by_email</options>\n"
    "  </rule>\n"
    "</group>"
)
story.append(code_para(rule_xml))
story.append(Paragraph(
    "Le niveau 10 (" + GT + " 7) déclenche automatiquement l'active response (voir "
    "section 6) : l'IP source est poussée dans l'alias OPNsense et bloquée sans "
    "intervention manuelle.",
    styles['body']
))

# ============================================================
# 6. ACTIVE RESPONSE (BLOCAGE AUTOMATIQUE)
# ============================================================
story.append(add_heading("6. Active Response (blocage automatique)", styles, 0))
story.append(Paragraph(
    "L'active response est le mécanisme qui transforme Wazuh d'un simple "
    "<b>détecteur</b> en un <b>réacteur</b>. Lorsqu'une alerte atteint un niveau "
    "suffisant, le manager exécute un script — ici "
    "<font name='CodeFont'>block-attacker.sh</font> — qui extrait l'IP source de "
    "l'alerte et demande au pare-feu OPNsense de la bloquer via son API REST.",
    styles['body']
))

story.append(add_heading("6.1. Principe et flux", styles, 1))
story.append(Paragraph(
    "Le flux complet, exécuté en quelques secondes :",
    styles['body']
))
flux = [
    "<b>Alerte</b> — une règle de niveau ≥ 10 se déclenche (ex. 100100 bruteforce SSH).",
    "<b>Extraction IP</b> — le moteur d'active response parse l'alerte et isole le champ <font name='CodeFont'>srcip</font>.",
    "<b>Appel API OPNsense</b> — <font name='CodeFont'>block-attacker.sh</font> fait un POST sur <font name='CodeFont'>/api/firewall/alias_utility/add/wazuh_blocked_ips</font>.",
    "<b>Alias dynamique</b> — l'IP est ajoutée à l'alias <font name='CodeFont'>wazuh_blocked_ips</font> côté OPNsense.",
    "<b>Règle de blocage</b> — une règle <i>block</i> sur l'alias rejette tout trafic de ces IP sur toutes les interfaces.",
    "<b>Timeout</b> — après 1 h, l'IP est retirée de l'alias (débloquée) via un appel symétrique.",
]
for f in flux:
    story.append(Paragraph(f"• {f}", styles['bullet']))

story.append(add_heading("6.2. Whitelist", styles, 1))
story.append(Paragraph(
    "Pour éviter de se bloquer soi-même, une <b>liste blanche</b> d'IP "
    "non-bloquables est définie dans <font name='CodeFont'>ossec.conf</font>. "
    "Elle inclut au minimum :",
    styles['body']
))
whitelist = [
    "le <b>bastion</b> (10.10.99.20) — point d'administration légitime,",
    "le <b>serveur Wazuh</b> lui-même (10.10.99.10) — pour éviter une auto-exclusion,",
    "la <b>passerelle OPNsense</b> (10.10.99.1) — source de nombreux logs légitimes.",
]
for w in whitelist:
    story.append(Paragraph(f"• {w}", styles['bullet']))

story.append(add_heading("6.3. Déclaration dans ossec.conf", styles, 1))
story.append(Paragraph(
    "La commande d'active response est déclarée puis référencée sur les règles "
    "de niveau ≥ 10, avec un timeout de 3600 secondes (1 heure) :",
    styles['body']
))
ar_code = (
    "<!-- ossec.conf : active response vers API OPNsense -->\n"
    "<command>\n"
    "  <name>block-attacker</name>\n"
    "  <executable>block-attacker.sh</executable>\n"
    "  <timeout_allowed>yes</timeout_allowed>\n"
    "</command>\n"
    "\n"
    "<active-response>\n"
    "  <command>block-attacker</command>\n"
    "  <location>local</location>\n"
    "  <rules_id>100100,100300,100500,100900</rules_id>\n"
    "  <timeout>3600</timeout>          <!-- débloque après 1 h -->\n"
    "  <repeated_offenders>30,60,120</repeated_offenders>\n"
    "</active-response>\n"
    "\n"
    "<!-- IP jamais bloquées -->\n"
    "<global>\n"
    "  <white_list>10.10.99.20</white_list>   <!-- bastion -->\n"
    "  <white_list>10.10.99.10</white_list>   <!-- Wazuh -->\n"
    "  <white_list>10.10.99.1</white_list>    <!-- OPNsense -->\n"
    "</global>"
)
story.append(code_para(ar_code))

story.append(add_heading("6.4. Script block-attacker.sh", styles, 1))
story.append(Paragraph(
    "Le script reçoit l'IP en variable d'environnement "
    "<font name='CodeFont'>ALERTSRCIP</font> et appelle l'API OPNsense avec une "
    "clé d'API dédiée (droit minimal : gestion de l'alias uniquement).",
    styles['body']
))
block_code = (
    "#!/usr/bin/env bash\n"
    "# block-attacker.sh — active response Wazuh -> OPNsense API\n"
    'OPNSENSE_API="https://10.10.99.1/api"\n'
    'API_KEY="${OPN_API_KEY}"      # secret, hors du dépôt\n'
    'API_SECRET="${OPN_API_SECRET}"\n'
    'ALIAS="wazuh_blocked_ips"\n'
    "\n"
    'ACTION="$1"           # add | delete\n'
    'SRCIP="${ALERTSRCIP:-}"\n'
    '[ -z "$SRCIP" ] && exit 0\n'
    "\n"
    'case "$ACTION" in\n'
    "  add)\n"
    '    curl -sk -u "$API_KEY:$API_SECRET" -X POST \\\n'
    '      "$OPNSENSE_API/firewall/alias_utility/add/$ALIAS" \\\n'
    '      -d "{\"address\":\"$SRCIP\"}"\n'
    "    ;;\n"
    "  delete)\n"
    '    curl -sk -u "$API_KEY:$API_SECRET" -X POST \\\n'
    '      "$OPNSENSE_API/firewall/alias_utility/delete/$ALIAS" \\\n'
    '      -d "{\"address\":\"$SRCIP\"}"\n'
    "    ;;\n"
    "esac\n"
    "# Applique la nouvelle config firewall\n"
    'curl -sk -u "$API_KEY:$API_SECRET" -X POST "$OPNSENSE_API/firewall/apply"'
)
story.append(code_para(block_code))

# ============================================================
# 7. SCA — SECURITY CONFIGURATION ASSESSMENT
# ============================================================
story.append(add_heading("7. Security Configuration Assessment (SCA)", styles, 0))
story.append(Paragraph(
    "Le SCA est un module Wazuh qui évalue <b>en continu</b> la conformité des "
    "machines à un référentiel de durcissement — ici les <b>CIS Benchmarks</b>. "
    "Contrairement à un scanner ponctuel (Lynis, OpenSCAP), le SCA s'exécute "
    "périodiquement sur chaque agent et remonte un score de conformité ainsi que "
    "la liste des contrôles échoués, directement dans le dashboard.",
    styles['body']
))

story.append(add_heading("7.1. Policies déployées", styles, 1))
sca_data = [
    ["Policy", "Cible", "Contrôles (extrait)"],
    ["CIS Ubuntu 22.04", "Serveur Linux", "SSH root interdit, sysctl hardening, UFW, auditd, permissions /etc"],
    ["CIS Windows Server 2022", "Contrôleur AD", "SMBv1 off, mot de passe ≥ 14, audit policy, NLA RDP"],
    ["CIS Windows 10", "Postes employés", "Defender on, BitLocker, AppLocker, restriction USB"],
    ["DTC-bastion (custom)", "Bastion NixOS", "Immuabilité (nixos-rebuild), FIDO2, ProxyJump only, pas de root direct"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 5 — Policies SCA</b>", styles['caption']))
story.append(make_table(sca_data, col_ratios=[0.26, 0.20, 0.54]))

story.append(add_heading("7.2. Rapport de conformité", styles, 1))
story.append(Paragraph(
    "Chaque exécution produit un score (0–100 %) par agent et par policy. Une "
    "alerte est levée si le score d'une machine critique chute sous 85 %, ce qui "
    "permet de détecter une <b>dérive de configuration</b> — par exemple une "
    "règle UFW supprimée manuellement ou un service durci désactivé. Le "
    "dashboard « SCA » agrège les scores par groupe et par policy, et expose "
    "l'historique des contrôles échoués pour audit.",
    styles['body']
))
story.append(Paragraph(
    "<b>Lien avec le bastion NixOS</b> : sur le bastion, le SCA vérifie que la "
    "configuration reste <i>identique</i> à l'état déclaré dans Git. Toute "
    "modification non versionnée est signalée comme non-conforme — l'immuabilité "
    "garantit qu'un <font name='CodeFont'>nixos-rebuild switch</font> la "
    "réécrasera.",
    styles['callout']
))

# ============================================================
# 8. DASHBOARDS
# ============================================================
story.append(add_heading("8. Dashboards", styles, 0))
story.append(Paragraph(
    "Le dashboard Wazuh (OpenSearch Dashboards) expose des visualisations "
    "prêtes à l'emploi agrégeant les alertes, les active responses et l'état "
    "des agents. Huit panels personnalisés sont configurés pour le projet :",
    styles['body']
))

story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 6 — Panels de dashboard</b>", styles['caption']))
dash_data = [
    ["Panel", "Visualisation", "Usage"],
    ["alerts-level", "Histogramme empilé par niveau (0–15)", "Vue d'ensemble du bruit et des alertes critiques"],
    ["bruteforce-ssh", "Compteur + top IP source", "Suivi des tentatives SSH (règle 100100)"],
    ["top-source-ips", "Bar chart horizontal des IP les plus bruyantes", "Repérer les sources récurrentes à bloquer"],
    ["active-response", "Timeline des blocages auto", "Vérifier que block-attacker.sh s'exécute"],
    ["firewall-blocks", "Compteur des drops OPNsense (alias wazuh_blocked_ips)", "Mesurer l'effet du blocage côté firewall"],
    ["agents-status", "Tableau active/disconnected par groupe", "Disponibilité des agents (linux, windows, critical...)"],
    ["lateral-movement", "Graphe source→destination des connexions inter-VLAN", "Détecter un mouvement latéral (règle 100300)"],
    ["config-changes", "Liste temporelle des modifs de fichiers de config", "Suivi des règles 100400/100500 (persistance)"],
]
story.append(make_table(dash_data, col_ratios=[0.20, 0.38, 0.42]))
story.append(Spacer(1, 10))
story.append(Paragraph(
    "Ces panels sont exportés au format <font name='CodeFont'>.ndjson</font> "
    "(Saved Objects) et versionnés dans le dépôt Git, ce qui permet de les "
    "réimporter sur toute instance Wazuh fraîche et de rejouer les démonstrations "
    "d'entretien de façon reproductible.",
    styles['body']
))

# ============================================================
# 9. CHOIX WAZUH VS ALTERNATIVES
# ============================================================
story.append(add_heading("9. Choix de Wazuh vs alternatives", styles, 0))
story.append(Paragraph(
    "Wazuh a été retenu face à deux alternatives courantes : un stack "
    "<b>Elastic pur</b> (Elasticsearch + Kibana + Logstash, sans le couche "
    "OSSEC) et <b>Splunk</b> (solution commerciale). Le tableau ci-dessous "
    "résume la comparaison sur les critères décisifs pour une PME.",
    styles['body']
))

story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 7 — Comparatif Wazuh / Elastic pur / Splunk</b>", styles['caption']))
cmp_data = [
    ["Critère", "Wazuh", "Elastic pur", "Splunk"],
    ["Coût", "Open source (gratuit)", "Open source (basique)", "Commercial, cher à l'ingestion"],
    ["Active response native", "Oui (scripts OSSEC)", "Non (à développer)", "Partiel (via SOAR payant)"],
    ["SCA (CIS en continu)", "Oui, intégré", "Non (scanner externe)", "Non (addon séparé)"],
    ["Règles OSSEC prêtes", "+ 3000 incluses", "Aucune (à écrire)", "Addons ES, payants"],
    ["Agents multi-OS", "Linux/Win/macOS", "Beats (limité)", "Universal Forwarder"],
    ["Communauté / maturité", "Fork OSSEC, très actif", "Très mature", "Très mature"],
    ["Intégration firewall (API)", "Via active response", "À scripter", "Via SOAR"],
    ["Courbe d'apprentissage", "Moyenne", "Élevée (pile ELK)", "Faible (mais payant)"],
]
story.append(make_table(cmp_data, col_ratios=[0.26, 0.26, 0.24, 0.24]))
story.append(Spacer(1, 12))

story.append(Paragraph(
    "Le facteur décisif est l'<b>active response native</b> couplée au SCA : "
    "seul Wazuh offre, dans une même brique open source, la détection (règles "
    "OSSEC), la réaction (blocage auto via API OPNsense) <b>et</b> le contrôle "
    "continu du durcissement (CIS). Un stack Elastic pur aurait exigé de "
    "réécrire ces trois couches ; Splunk les fournit mais à un coût "
    "incompatible avec un budget PME.",
    styles['body']
))
story.append(Paragraph(
    "<b>Synthèse</b> : Wazuh est le seul composant du projet qui ferme "
    "entièrement la boucle <i>détecter → décider → bloquer</i> sans intervention "
    "humaine ni licence commerciale, tout en s'intégrant nativement à l'API "
    "OPNsense via l'alias <font name='CodeFont'>wazuh_blocked_ips</font>.",
    styles['callout']
))

# ============================================================
# BUILD
# ============================================================
doc.multiBuild(story)
print(f"PDF généré : {OUTPUT}")
