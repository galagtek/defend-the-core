#!/usr/bin/env python3
"""
Générateur PDF : Annexe 3 — Durcissement des serveurs (Linux & Windows)
Synthèse : philosophie de défense en profondeur, durcissement Ubuntu Server
(VLAN 30) — SSH, auditd, UFW, sysctl, CIS, pile Web —, durcissement Windows
Server 2022 (VLAN 30) — pare-feu, audit, mots de passe, comptes, Defender,
registre, SMBv1, RDP —, GPO de sécurité et justification ANSSI.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_common import *
from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle

register_fonts()
styles = get_styles()

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'docs', '03_durcissement_serveurs.pdf')

doc = build_doc(OUTPUT, "Defend-The-Core — Durcissement des serveurs")
story = []

# ============================================================
# PAGE DE TITRE
# ============================================================
story.append(Spacer(1, 80))
story.append(Paragraph("Defend-The-Core", styles['title']))
story.append(HRFlowable(width="40%", thickness=2, color=ACCENT, spaceBefore=6, spaceAfter=12))
story.append(Paragraph("Annexe 3 : Durcissement des serveurs", styles['subtitle']))
story.append(Spacer(1, 20))
story.append(Paragraph(
    "Durcissement Ubuntu Server et Windows Server 2022<br/>"
    "Défense en profondeur, conformité CIS Benchmark, justification ANSSI",
    ParagraphStyle('Desc', fontName='BodyFont', fontSize=11, leading=16,
                   textColor=TEXT_MUTED, alignment=TA_LEFT)
))
story.append(Spacer(1, 40))
story.append(Paragraph(
    "SSH durci · auditd · UFW · sysctl · CIS Benchmark · Nginx · PostgreSQL · "
    "Windows Defender · GPO · SMBv1 désactivé · RDP NLA",
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
# 1. PHILOSOPHIE DE DURCISSEMENT
# ============================================================
story.append(add_heading("1. Philosophie de durcissement", styles, 0))
story.append(Paragraph(
    "Le durcissement d'un serveur consiste à réduire sa surface d'attaque en "
    "désactivant tout ce qui n'est pas strictement nécessaire et en renforçant "
    "les mécanismes de sécurité qui restent. Pour Defend-The-Core, cette "
    "démarche s'inscrit dans trois principes directeurs : la <b>défense en "
    "profondeur</b>, le <b>principe du moindre privilège</b> et la <b>conformité "
    "aux CIS Benchmarks</b>, eux-mêmes alignés sur les recommandations de "
    "l'ANSSI.",
    styles['body']
))

story.append(add_heading("1.1. Défense en profondeur", styles, 1))
story.append(Paragraph(
    "La défense en profondeur repose sur l'empilement de couches de protection "
    "<b>indépendantes</b>, de sorte que la défaillance ou le contournement d'une "
    "seule ne suffise pas à compromettre le système. Chaque couche ajoute une "
    "barrière distincte qu'un attaquant doit franchir séparément.",
    styles['body']
))
story.append(Paragraph(
    "Sur les serveurs du VLAN 30, la chaîne de défense est la suivante : "
    "<b>pare-feu OPNsense</b> (filtrage inter-VLAN) puis <b>UFW local</b> "
    "(filtrage de l'hôte), <b>sysctl</b> (paramètres noyau : ASLR, anti-spoofing, "
    "SYN flood), <b>auditd</b> (journalisation des actions sensibles) et enfin "
    "<b>SSH durci</b> (clés uniquement, root interdit, crypto forte). Aucune de "
    "ces couches ne fait confiance à une autre : un flux autorisé par OPNsense "
    "reste filtré par UFW, une session SSH acceptée reste surveillée par auditd.",
    styles['body']
))
story.append(Paragraph(
    "Cette indépendance est essentielle : si une vulnérabilité contournait le "
    "pare-feu périphérique, les couches internes (sysctl, auditd, SSH) "
    "continueraient de limiter les dégâts et de générer des alertes exploitables "
    "par le SIEM Wazuh.",
    styles['callout']
))

story.append(add_heading("1.2. Moindre privilège", styles, 1))
story.append(Paragraph(
    "Le principe du moindre privilège s'applique à tous les niveaux : services "
    "tournant sous des comptes dédiés sans shell, fichiers en possession stricte "
    "(<font name='CodeFont'>chmod 600</font> pour les clés), comptes "
    "administratifs isolés derrière le bastion, et ports d'écoute limités au "
    "strict métier. Aucun service n'expose plus que ce que sa fonction requiert.",
    styles['body']
))

story.append(add_heading("1.3. Conformité CIS Benchmark", styles, 1))
story.append(Paragraph(
    "Le durcissement suit les <b>CIS Benchmarks</b> (Center for Internet "
    "Security), référentiels reconnus qui déclinent en contrôles concrets les "
    "bonnes pratiques de sécurité. Ces benchmarks servent également de base à "
    "l'évaluation continue réalisée par Wazuh (Security Configuration "
    "Assessment) : toute dérive de configuration déclenche une alerte. Les "
    "recommandations CIS retenues sont celles pertinentes pour un serveur en "
    "zone critique, et leur mise en œuvre est justifiée dans les sections "
    "suivantes.",
    styles['body']
))
story.append(Paragraph(
    "Au-delà des CIS, la démarche répond directement aux préconisations de "
    "l'<b>ANSSI</b> en matière de durcissement des systèmes, de journalisation "
    "et d'administration sécurisée (voir section 5).",
    styles['body']
))

# ============================================================
# 2. DURCISSEMENT UBUNTU SERVER (VLAN 30)
# ============================================================
story.append(add_heading("2. Durcissement Ubuntu Server (VLAN 30)", styles, 0))
story.append(Paragraph(
    "Le serveur Ubuntu 22.04 LTS du VLAN 30 (10.10.30.10) héberge la pile Web "
    "métier (Nginx + PostgreSQL). Son durcissement couvre six domaines : le "
    "service SSH, la journalisation auditd, le pare-feu local UFW, les "
    "paramètres noyau sysctl, le durcissement CIS général et la pile "
    "applicative.",
    styles['body']
))

# --- 2.1 SSH durci ---
story.append(add_heading("2.1. SSH durci", styles, 1))
story.append(Paragraph(
    "L'accès SSH est le seul canal d'administration du serveur. Il est verrouillé "
    "à l'extrême : <b>authentification par clé uniquement</b> (aucun mot de "
    "passe), <b>connexion root interdite</b> (passage par un compte sudo dédié "
    "via le bastion), algorithmes cryptographiques modernes, et limitation "
    "stricte des tentatives.",
    styles['body']
))
ssh_data = [
    ["Paramètre", "Valeur", "Justification"],
    ["PermitRootLogin", "no", "Force l'usage d'un compte sudo dédié, traçable"],
    ["PasswordAuthentication", "no", "Authentification par clé uniquement, anti-bruteforce"],
    ["PubkeyAuthentication", "yes", "Mécanisme d'authentification retenu"],
    ["KexAlgorithms", "curve25519-sha256, ecdh-sha2-nistp256", "Échange de clés modernes, anti attaque par pré-image"],
    ["Ciphers", "chacha20-poly1305, aes256-gcm", "Chiffrement symétrique AEAD, confidentialité + intégrité"],
    ["MACs", "hmac-sha2-512-etm, hmac-sha2-256-etm", "Codes d'authentification résistants aux collisions"],
    ["MaxAuthTries", "3", "Blocage rapide des tentatives de bruteforce"],
    ["LoginGraceTime", "30", "Ferme la connexion non authentifiée après 30 s"],
    ["AllowUsers", "ops-admin", "Liste blanche stricte d'utilisateurs autorisés"],
    ["Banner", "/etc/issue.net", "Avertissement légal avant authentification"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 1 — Paramètres de durcissement SSH</b>", styles['caption']))
story.append(make_table(ssh_data, col_ratios=[0.26, 0.30, 0.44]))
story.append(Paragraph(
    "Extrait du fichier <font name='CodeFont'>/etc/ssh/sshd_config.d/50-hardening.conf</font> :",
    styles['caption']
))
ssh_code = (
    "# Authentification et accès<br/>"
    "PermitRootLogin no<br/>"
    "PasswordAuthentication no<br/>"
    "PubkeyAuthentication yes<br/>"
    "MaxAuthTries 3<br/>"
    "LoginGraceTime 30<br/>"
    "AllowUsers ops-admin<br/>"
    "Banner /etc/issue.net<br/>"
    "<br/>"
    "# Suite cryptographique (algorithme moderne uniquement)<br/>"
    "KexAlgorithms curve25519-sha256,ecdh-sha2-nistp256<br/>"
    "Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com<br/>"
    "MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com"
)
story.append(Paragraph(ssh_code, styles['code']))
story.append(Paragraph(
    "Le compte <font name='CodeFont'>ops-admin</font> n'est accessible qu'en "
    "rebond depuis le bastion NixOS (ProxyJump), ce qui ajoute une couche "
    "d'authentification forte et d'immutabilité.",
    styles['body']
))

# --- 2.2 Auditd ---
story.append(add_heading("2.2. Auditd — surveillance des actions sensibles", styles, 1))
story.append(Paragraph(
    "Le daemon <font name='CodeFont'>auditd</font> journalise en continu les "
    "actions sensibles : modifications de fichiers d'identité et de "
    "configuration, exécution de commandes privilégiées, changements de droits. "
    "Les journaux sont forwardés vers le SIEM Wazuh pour corrélation. Les règles "
    "sont rendues <b>immuables</b> via <font name='CodeFont'>-e 2</font> : leur "
    "modification exige un redémarrage, ce qui empêche un attaquant de les "
    "désactiver discrètement.",
    styles['body']
))
audit_data = [
    ["Règle", "Cible surveillée", "Objectif"],
    ["-w /etc/passwd -p wa", "Fichier d'identité", "Détecte création/modification de comptes"],
    ["-w /etc/group -p wa", "Fichier de groupes", "Détecte élévation de privilèges via groupe"],
    ["-w /etc/sudoers -p wa", "Configuration sudo", "Détecte attribution de droits d'administration"],
    ["-w /etc/ssh/sshd_config -p wa", "Configuration SSH", "Détecte tentative de backdoor SSH"],
    ["-w /var/log/auth.log -p wa", "Journal d'authentification", "Détecte falsification des logs"],
    ["-a always,exit -F arch=b64 -S execve", "Exécution de commandes", "Trace toutes les commandes exécutées"],
    ["-e 2", "Verrou d'immutabilité", "Règles non modifiables sans redémarrage"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 2 — Règles auditd clés</b>", styles['caption']))
story.append(make_table(audit_data, col_ratios=[0.34, 0.26, 0.40]))

# --- 2.3 UFW ---
story.append(add_heading("2.3. UFW — pare-feu local", styles, 1))
story.append(Paragraph(
    "UFW (Uncomplicated Firewall) constitue la couche de filtrage de l'hôte, "
    "indépendante du pare-feu OPNsense. La politique par défaut est <b>deny "
    "incoming</b> : seuls les flux explicitement listés sont acceptés. Le SSH "
    "n'est autorisé que depuis le bastion ; le HTTP/HTTPS n'est servi que par le "
    "reverse proxy.",
    styles['body']
))
ufw_data = [
    ["Règle", "Action", "Justification"],
    ["default deny incoming", "Deny", "Refus par défaut de tout flux entrant"],
    ["default allow outgoing", "Allow", "Le serveur initie ses propres flux (MAJ, DNS)"],
    ["from 10.10.99.20 to any port 22", "Allow", "SSH uniquement depuis le bastion (VLAN 99)"],
    ["from 10.10.20.0/24 to any port 80,443", "Allow", "HTTP/HTTPS depuis le reverse proxy (DMZ) uniquement"],
    ["from any to any", "Deny", "Règle finale implicite de blocage"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 3 — Règles UFW</b>", styles['caption']))
story.append(make_table(ufw_data, col_ratios=[0.40, 0.12, 0.48]))

# --- 2.4 sysctl ---
story.append(add_heading("2.4. sysctl — paramètres noyau durcis", styles, 1))
story.append(Paragraph(
    "Les paramètres noyau sont renforcés via <font name='CodeFont'>sysctl</font> "
    "pour activer l'ASLR, empêcher l'attachement à un processus, contrer "
    "l'usurpation d'adresse (anti-spoofing) et le SYN flood, et désactiver IPv6 "
    "inutilisé.",
    styles['body']
))
sysctl_data = [
    ["Paramètre", "Valeur", "Justification"],
    ["kernel.randomize_va_space", "2", "ASLR complet, complique l'exploitation de failles mémoire"],
    ["kernel.yama.ptrace_scope", "1", "Restreint ptrace aux processus enfants, anti-injection"],
    ["net.ipv4.conf.all.rp_filter", "1", "Anti-spoofing : vérifie la cohérence source/chemin"],
    ["net.ipv4.conf.all.accept_redirects", "0", "Ignore les redirections ICMP, anti-MITM"],
    ["net.ipv4.conf.all.send_redirects", "0", "Le serveur n'émet pas de redirections ICMP"],
    ["net.ipv4.tcp_syncookies", "1", "Protection contre le SYN flood (DoS)"],
    ["net.ipv4.conf.all.log_martians", "1", "Journalise les paquets impossible/martien (alerte Wazuh)"],
    ["net.ipv6.conf.all.disable_ipv6", "1", "Désactive IPv6 inutilisé, réduit la surface d'attaque"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 4 — Paramètres sysctl durcis</b>", styles['caption']))
story.append(make_table(sysctl_data, col_ratios=[0.38, 0.10, 0.52]))

# --- 2.5 CIS ---
story.append(add_heading("2.5. Durcissement CIS général", styles, 1))
story.append(Paragraph(
    "Au-delà des domaines précédents, plusieurs contrôles CIS transverses sont "
    "appliqués : politique de mots de passe PAM, limites de session, permissions "
    "de fichiers, suppression des services inutiles et blacklisting de modules "
    "noyau dangereux.",
    styles['body']
))
cis_points = [
    "<b>PAM</b> : mots de passe de 14 caractères minimum, 4 classes de caractères "
    "(majuscule, minuscule, chiffre, spécial), verrouillage du compte après 5 "
    "échecs pendant 30 minutes.",
    "<b>Limites de session</b> : <font name='CodeFont'>/etc/security/limits.conf</font> "
    "plafonne les processus par utilisateur (anti fork bomb) et la mémoire, pour "
    "empêcher un DoS local d'épuiser les ressources.",
    "<b>Permissions fichiers</b> : fichiers de configuration en <font name='CodeFont'>"
    "640</font> ou <font name='CodeFont'>600</font>, journaux en append-only, "
    "recherche de fichiers SUID inattendus.",
    "<b>Services inutiles</b> : désactivation de <font name='CodeFont'>avahi</font>, "
    "<font name='CodeFont'>cups</font>, <font name='CodeFont'>modemmanager</font> "
    "et de tout service non requis par le rôle du serveur.",
    "<b>Modules noyau blacklistés</b> : <font name='CodeFont'>dccp</font>, "
    "<font name='CodeFont'>sctp</font>, <font name='CodeFont'>rds</font>, "
    "<font name='CodeFont'>tipc</font> — protocoles rares non utilisés et "
    "historiquement vulnérables.",
]
for pt in cis_points:
    story.append(Paragraph(f"• {pt}", styles['bullet']))

# --- 2.6 Pile Web ---
story.append(add_heading("2.6. Pile Web durcie", styles, 1))
story.append(Paragraph(
    "<b>Nginx</b> sert de serveur Web frontal. Il masque sa version "
    "(<font name='CodeFont'>server_tokens off</font>), injecte des en-têtes de "
    "sécurité et limite les protocoles TLS aux versions récentes (1.2 et 1.3) "
    "avec des suites cryptographiques fortes.",
    styles['body']
))
nginx_headers_data = [
    ["En-tête / paramètre", "Valeur", "Rôle"],
    ["server_tokens", "off", "Masque la version de Nginx, complique le fingerprinting"],
    ["X-Frame-Options", "SAMEORIGIN", "Anti clickjacking (encadrement interdit)"],
    ["X-Content-Type-Options", "nosniff", "Anti MIME-sniffing"],
    ["X-XSS-Protection", "1; mode=block", "Filtre XSS réfléchi côté navigateur"],
    ["Strict-Transport-Security", "max-age=31536000", "HSTS : force HTTPS pendant 1 an"],
    ["ssl_protocols", "TLSv1.2 TLSv1.3", "TLS modernes uniquement, abandon de TLS 1.0/1.1"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 5 — En-têtes et paramètres Nginx</b>", styles['caption']))
story.append(make_table(nginx_headers_data, col_ratios=[0.30, 0.26, 0.44]))
story.append(Paragraph(
    "<b>PostgreSQL</b> n'écoute que sur <font name='CodeFont'>localhost</font> "
    "(<font name='CodeFont'>127.0.0.1</font>) : aucune exposition réseau, "
    "connexion uniquement via le socket local depuis Nginx. L'authentification "
    "utilise <font name='CodeFont'>scram-sha-256</font> dans "
    "<font name='CodeFont'>pg_hba.conf</font>, qui remplace l'obsolète MD5 par "
    "un mécanisme à hachage salé résistant aux attaques hors ligne. La base "
    "métier utilise un compte dédié à droits limités, distinct du superutilisateur.",
    styles['body']
))
nginx_code = (
    "# Nginx — durcissement TLS et en-têtes<br/>"
    "server_tokens off;<br/>"
    "ssl_protocols TLSv1.2 TLSv1.3;<br/>"
    "ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;<br/>"
    "add_header X-Frame-Options SAMEORIGIN always;<br/>"
    "add_header X-Content-Type-Options nosniff always;<br/>"
    "add_header Strict-Transport-Security \"max-age=31536000\" always;<br/>"
    "<br/>"
    "# PostgreSQL — pg_hba.conf<br/>"
    "host    metier    metier_app    127.0.0.1/32    scram-sha-256"
)
story.append(Paragraph(nginx_code, styles['code']))

# ============================================================
# 3. DURCISSEMENT WINDOWS SERVER 2022 (VLAN 30)
# ============================================================
story.append(add_heading("3. Durcissement Windows Server 2022 (VLAN 30)", styles, 0))
story.append(Paragraph(
    "Le contrôleur de domaine Windows Server 2022 (10.10.30.20) assure "
    "l'annuaire Active Directory, le DNS et le DHCP. Son durcissement combine "
    "pare-feu hôte, politique d'audit, politique de mots de passe, gestion des "
    "comptes, Windows Defender, paramètres de registre et désactivation des "
    "protocoles hérités dangereux.",
    styles['body']
))

# --- 3.1 Pare-feu Windows ---
story.append(add_heading("3.1. Pare-feu Windows", styles, 1))
story.append(Paragraph(
    "Le pare-feu Windows Defender est activé sur les trois profils (domaine, "
    "privé, public) en politique <b>inbound default-deny</b> : aucune connexion "
    "entrante n'est acceptée sauf règle explicite. La journalisation des paquets "
    "droppés est activée pour alimenter la détection.",
    styles['body']
))
win_fw_data = [
    ["Paramètre", "Valeur", "Justification"],
    ["Domain/Private/Public profile", "Enabled", "Pare-feu actif sur tous les profils"],
    ["Default Inbound Action", "Block", "Refus par défaut des connexions entrantes"],
    ["Default Outbound Action", "Allow", "Le serveur initie ses propres flux"],
    ["Log Dropped Packets", "Yes", "Journalisation des paquets rejetés, corrélation Wazuh"],
    ["Log Successful Connections", "Yes", "Traçabilité des connexions acceptées"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 6 — Pare-feu Windows Defender</b>", styles['caption']))
story.append(make_table(win_fw_data, col_ratios=[0.34, 0.16, 0.50]))

# --- 3.2 Politique d'audit ---
story.append(add_heading("3.2. Politique d'audit", styles, 1))
story.append(Paragraph(
    "Toutes les catégories d'audit sont activées pour fournir au SIEM une "
    "vision complète de l'activité du serveur. Les événements sont collectés par "
    "l'agent Wazuh et corrélés aux signaux provenant des autres hôtes.",
    styles['body']
))
audit_win_data = [
    ["Catégorie", "Sous-catégorie", "Niveau"],
    ["Logon/Logoff", "Logon, Logoff, Account Lockout", "Success + Failure"],
    ["Account Management", "User/Group creation, deletion", "Success + Failure"],
    ["Object Access", "File, Registry, Kernel", "Success + Failure"],
    ["Privilege Use", "Sensitive privilege use", "Success + Failure"],
    ["Policy Change", "Audit policy, auth policy", "Success + Failure"],
    ["Account Logon", "Credential validation", "Success + Failure"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 7 — Politique d'audit Windows</b>", styles['caption']))
story.append(make_table(audit_win_data, col_ratios=[0.24, 0.46, 0.30]))

# --- 3.3 Mots de passe ---
story.append(add_heading("3.3. Politique de mots de passe", styles, 1))
story.append(Paragraph(
    "La politique de mots de passe, déployée par GPO, impose une longueur et une "
    "complexité élevées ainsi qu'un verrouillage automatique du compte en cas "
    "d'échecs répétés, conformément aux recommandations CIS et ANSSI.",
    styles['body']
))
pwd_win_data = [
    ["Paramètre", "Valeur", "Justification"],
    ["Minimum length", "14", "Complexité suffisante pour résister au bruteforce hors ligne"],
    ["Maximum age", "90 jours", "Renouvellement périodique, limite la durée de vie d'un secret compromis"],
    ["Complexity", "Enabled", "4 classes de caractères obligatoires"],
    ["Lockout threshold", "5 échecs", "Verrouillage rapide en cas de bruteforce"],
    ["Lockout duration", "30 minutes", "Fenêtre d'attente avant déverrouillage automatique"],
    ["Reversible encryption", "Disabled", "Stockage sous forme de hachage, jamais en clair"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 8 — Politique de mots de passe Windows</b>", styles['caption']))
story.append(make_table(pwd_win_data, col_ratios=[0.30, 0.16, 0.54]))

# --- 3.4 Comptes ---
story.append(add_heading("3.4. Gestion des comptes", styles, 1))
story.append(Paragraph(
    "Le compte <b>Administrator</b> natif est renommé afin de rendre les "
    "attaques par énumération de comptes moins efficaces, et le compte "
    "<b>Guest</b> est désactivé pour éliminer une porte d'entrée sans mot de "
    "passe. Aucun compte à privilèges n'est utilisé pour les tâches courantes : "
    "l'administration passe par des comptes dédiés et le bastion.",
    styles['body']
))
acct_win_data = [
    ["Action", "Cible", "Objectif"],
    ["Renommage", "Administrator", "Évite l'énumération du compte par défaut"],
    ["Désactivation", "Guest", "Supprime un compte sans mot de passe"],
    ["Désactivation", "Comptes inactifs (90 j)", "Réduit la surface d'attaque"],
    ["Restriction", "Administrateurs locaux", "Accès uniquement via le bastion"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 9 — Gestion des comptes Windows</b>", styles['caption']))
story.append(make_table(acct_win_data, col_ratios=[0.20, 0.30, 0.50]))

# --- 3.5 Windows Defender ---
story.append(add_heading("3.5. Windows Defender", styles, 1))
story.append(Paragraph(
    "L'antivirus natif Windows Defender est activé en mode <b>real-time</b> avec "
    "protection cloud et protection réseau, et le module anti-ransomware "
    "(contrôle d'accès aux dossiers) est activé pour limiter l'impact d'un "
    "chiffrement malveillant.",
    styles['body']
))
defender_data = [
    ["Fonctionnalité", "Valeur", "Rôle"],
    ["Real-time protection", "On", "Analyse en temps réel des fichiers accédés"],
    ["Cloud-delivered protection", "High", "Réputation cloud, détection des menaces émergentes"],
    ["Network protection", "On", "Bloque les connexions vers des domaines malveillants"],
    ["Controlled folder access", "On", "Anti-ransomware, protège les dossiers sensibles"],
    ["PUA protection", "On", "Bloque les applications potentiellement indésirables"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 10 — Windows Defender</b>", styles['caption']))
story.append(make_table(defender_data, col_ratios=[0.32, 0.14, 0.54]))

# --- 3.6 Registre ---
story.append(add_heading("3.6. Paramètres de registre", styles, 1))
story.append(Paragraph(
    "Plusieurs clés de registre renforcent l'authentification et le contrôle de "
    "l'environnement : imposition de NTLMv2, désactivation du stockage du hash "
    "LM (faible) et de l'AutoRun, et conservation du séquenceur SAS "
    "(Ctrl+Alt+Del) pour l'ouverture de session.",
    styles['body']
))
reg_data = [
    ["Clé de registre", "Valeur", "Justification"],
    ["LmCompatibilityLevel", "5",
     "NTLMv2 uniquement, refus des LM/NTLMv1 obsolètes"],
    ["NoLMHash", "1",
     "Ne stocke pas le hash LM (cassable instantanément)"],
    ["AutoRun", "Disabled",
     "Empêche l'exécution automatique depuis un média amovible"],
    ["DisableCAD", "0",
     "Ctrl+Alt+Del obligatoire avant ouverture de session (anti-spoofing de l'écran de login)"],
    ["ScForceOption", "1",
     "Carte à puce requise pour l'ouverture de session interactive (si déployée)"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 11 — Paramètres de registre de sécurité</b>", styles['caption']))
story.append(make_table(reg_data, col_ratios=[0.26, 0.12, 0.62]))

# --- 3.7 SMBv1 ---
story.append(add_heading("3.7. Désactivation de SMBv1", styles, 1))
story.append(Paragraph(
    "Le protocole SMBv1 — exploité notamment par l'exploit EternalBlue "
    "(WannaCry, NotPetya) — est entièrement désactivé au niveau du serveur et "
    "du client. Seules les versions SMB 2 et 3 modernes, prenant en charge le "
    "chiffrement, sont autorisées.",
    styles['body']
))
smb_code = (
    "# Désactivation de SMBv1 (PowerShell, administrateur)<br/>"
    "Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart<br/>"
    "Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force<br/>"
    "Set-SmbClientConfiguration -EnableSecuritySignature $true -Force"
)
story.append(Paragraph(smb_code, styles['code']))
story.append(Paragraph(
    "<b>Argument clé</b> : EternalBlue (MS17-010) a permis en 2017 la "
    "propagation mondiale de WannaCry. Désactiver SMBv1 neutralise définitivement "
    "ce vecteur, y compris sur des systèmes à jour par mesure de réduction de "
    "surface d'attaque.",
    styles['callout']
))

# --- 3.8 RDP ---
story.append(add_heading("3.8. RDP — NLA et chiffrement", styles, 1))
story.append(Paragraph(
    "L'accès RDP, lorsqu'il est requis, exige la <b>NLA</b> (Network Level "
    "Authentication) : l'authentification a lieu avant l'allocation des "
    "ressources de session, ce qui protège le serveur contre les attaques par "
    "déni de service et certaines vulnérabilités BlueKeep-like. Le chiffrement "
    "est réglé sur <b>High</b> (niveau maximal).",
    styles['body']
))
rdp_data = [
    ["Paramètre", "Valeur", "Justification"],
    ["UserAuthentication (NLA)", "Required", "Authentification avant allocation de session"],
    ["SecurityLayer", "TLS", "Authentification TLS, abandon de la couche RDP héritée"],
    ["MinEncryptionLevel", "High", "Chiffrement maximal des données de session"],
    ["MaxDisconnectionTime", "30 min", "Déconnexion automatique des sessions inactives"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 12 — Paramètres RDP</b>", styles['caption']))
story.append(make_table(rdp_data, col_ratios=[0.34, 0.16, 0.50]))

# ============================================================
# 4. GPO DE SÉCURITÉ (WINDOWS)
# ============================================================
story.append(add_heading("4. GPO de sécurité (Windows)", styles, 0))
story.append(Paragraph(
    "Quatre objets de stratégie de groupe (GPO) déploient automatiquement les "
    "contrôles de sécurité sur le domaine. Ils sont versionnés dans le dépôt "
    "Git du projet et appliqués via un cycle DevSecOps, ce qui garantit leur "
    "reproductibilité et leur auditabilité.",
    styles['body']
))
gpo_data = [
    ["GPO", "Description", "Paramètres clés"],
    ["DTC-Password-Policy",
     "Politique de mots de passe et de verrouillage",
     "14 car, 90 j, complexité, verrouillage 5/30 min, historique 24"],
    ["DTC-Workstation-Hardening",
     "Durcissement des postes et serveurs membres",
     "SMBv1 off, NLA, Defender realtime, AutoRun off, LMCompatibilityLevel=5"],
    ["DTC-Audit-Policy",
     "Journalisation complète des événements de sécurité",
     "Toutes catégories Success+Failure, forward vers Wazuh"],
    ["DTC-Software-Restriction",
     "Restriction logicielle et contrôle d'exécution",
     "AppLocker (listes blanches), chemins d'exécution contrôlés"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 13 — GPO de sécurité Defend-The-Core</b>", styles['caption']))
story.append(make_table(gpo_data, col_ratios=[0.24, 0.30, 0.46]))

# ============================================================
# 5. JUSTIFICATION ANSSI
# ============================================================
story.append(add_heading("5. Justification ANSSI", styles, 0))
story.append(Paragraph(
    "Le tableau ci-dessous établit la correspondance entre les grandes "
    "recommandations de l'ANSSI et leur mise en œuvre concrète dans le cadre du "
    "durcissement des serveurs. Il démontre que chaque préconisation se traduit "
    "par un contrôle technique vérifiable.",
    styles['body']
))
anssi_data = [
    ["Recommandation ANSSI", "Mise en œuvre dans le durcissement"],
    ["Cloisonnement en zones de confiance",
     "Serveurs en VLAN 30 (critique), filtrés par OPNsense default-deny et UFW local"],
    ["Principe du moindre privilège",
     "Services sous comptes dédiés, fichiers en 600, AllowUsers SSH, ports métier uniquement"],
    ["Authentification forte",
     "SSH par clé uniquement, root interdit, NTLMv2 imposé, NLA RDP"],
    ["Journalisation et traçabilité",
     "auditd immuable (-e 2) sur Linux, audit complet Windows, forward vers Wazuh"],
    ["Durcissement des systèmes",
     "CIS Benchmark (sysctl, PAM, registre, Defender), SMBv1 désactivé, TLS 1.2/1.3"],
    ["Mise à jour continue",
     "Unattended-upgrades sécurité (Ubuntu), WSUS/Defender (Windows), évaluation SCA Wazuh"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 14 — Correspondance recommandations ANSSI</b>", styles['caption']))
story.append(make_table(anssi_data, col_ratios=[0.36, 0.64]))

story.append(Spacer(1, 16))
story.append(Paragraph(
    "Cette annexe complète le document maître d'architecture. Les annexes "
    "voisines traitent du réseau et d'OPNsense (annexe 1), du SIEM Wazuh "
    "(annexe 2) et de l'administration sécurisée via le bastion NixOS (annexe 4).",
    styles['body_left']
))

# ============================================================
# BUILD
# ============================================================
doc.multiBuild(story)
print(f"PDF généré : {OUTPUT}")
