#!/usr/bin/env python3
"""
Générateur PDF : Annexe 1 — Réseau & OPNsense (01_reseau_opnsense.pdf)
Détaille : zoning VLAN, topologie VirtualBox, configuration OPNsense (API REST,
scripts, alias), matrice de filtrage default-deny, NAT/port forwarding,
comparatif OPNsense vs pfSense, intégration Wazuh active response.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_common import *
from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable
from reportlab.lib.styles import ParagraphStyle

register_fonts()
styles = get_styles()

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'docs', '01_reseau_opnsense.pdf')

doc = build_doc(OUTPUT, "Defend-The-Core — Réseau & OPNsense")
story = []


def code_block(text):
    """Bloc de code échappé pour ReportLab (Paragraph en style code)."""
    escaped = (text.replace('&', '&')
                   .replace('<', '<')
                   .replace('>', '>'))
    # Préserver les sauts de ligne
    escaped = escaped.replace('\n', '<br/>')
    return Paragraph(escaped, styles['code'])


# ============================================================
# PAGE DE TITRE
# ============================================================
story.append(Spacer(1, 80))
story.append(Paragraph("Defend-The-Core", styles['title']))
story.append(HRFlowable(width="40%", thickness=2, color=ACCENT, spaceBefore=6, spaceAfter=12))
story.append(Paragraph("Annexe 1 : Réseau & OPNsense", styles['subtitle']))
story.append(Spacer(1, 20))
story.append(Paragraph(
    "Pare-feu / routeur inter-VLAN — zoning, filtrage default-deny, "
    "NAT et intégration active response",
    ParagraphStyle('Desc', fontName='BodyFont', fontSize=11, leading=16,
                   textColor=TEXT_MUTED, alignment=TA_LEFT)
))
story.append(Spacer(1, 40))
story.append(Paragraph(
    "Segmentation ANSSI · Default-deny · API REST · Infrastructure as Code",
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
# 1. ZONING ET SEGMENTATION VLAN
# ============================================================
story.append(add_heading("1. Zoning et segmentation VLAN", styles, 0))
story.append(Paragraph(
    "Dans un réseau « plat », la compromission d'un seul poste utilisateur suffit à un "
    "attaquant pour scanner l'ensemble du système d'information, identifier les serveurs "
    "et exploiter leurs vulnérabilités. C'est le schéma classique de la propagation "
    "latérale : phishing → compromission poste → reconnaissance → mouvement latéral → "
    "exfiltration. La <b>segmentation en zones de confiance</b> (zoning) brise cette "
    "chaîne : même si un poste est compromis, l'attaquant ne voit et ne peut atteindre "
    "que ce qui lui est explicitement autorisé.",
    styles['body']
))
story.append(Paragraph(
    "L'infrastructure Defend-The-Core est découpée en <b>quatre zones de confiance</b>, "
    "chacune matérialisée par un VLAN distinct et cloisonnée par un pare-feu OPNsense en "
    "<b>default-deny</b>. Le niveau de confiance décroît du VLAN 99 (administration) au "
    "VLAN 10 (bureautique, considéré comme non fiable car exposé au vecteur phishing).",
    styles['body']
))

story.append(Spacer(1, 8))
story.append(Paragraph("<b>Tableau 1 — Zones de confiance et segmentation VLAN</b>", styles['caption']))
zones_data = [
    ["VLAN", "Zone", "Réseau", "Confiance", "Rôle"],
    ["10", "Bureautique", "10.10.10.0/24", "Faible",
     "Postes utilisateurs (vecteur d'attaque n°1)"],
    ["20", "DMZ", "10.10.20.0/24", "Moyenne",
     "Services exposés : reverse proxy, passerelle VPN"],
    ["30", "Critique", "10.10.30.0/24", "Haute",
     "Serveurs métier (Web + BDD), Active Directory"],
    ["99", "Admin / SIEM", "10.10.99.0/24", "Maximale",
     "Surveillance (Wazuh), bastion d'administration (NixOS)"],
]
story.append(make_table(zones_data, col_ratios=[0.08, 0.14, 0.18, 0.12, 0.48]))
story.append(Spacer(1, 12))

story.append(add_heading("1.1. Niveaux de confiance", styles, 1))
story.append(Paragraph(
    "Chaque zone se voit attribuer un niveau de confiance reflétant son exposition et la "
    "sensibilité des données qu'elle héberge. Ce niveau détermine la matrice des flux "
    "autorisés : un flux ne peut aller que d'une confiance <b>égale ou supérieure</b> vers "
    "une confiance <b>égale ou inférieure</b>, jamais l'inverse. Concrètement, le VLAN 99 "
    "(admin) peut initier des flux vers le VLAN 30 (critique) pour l'administration, mais "
    "le VLAN 10 (bureautique) ne peut jamais initier de flux vers le VLAN 30 ni le VLAN 99.",
    styles['body']
))

story.append(add_heading("1.2. Règle d'or : default-deny", styles, 1))
story.append(Paragraph(
    "Le pare-feu OPNsense applique une politique <b>default-deny</b> : tout flux non "
    "explicitement autorisé est rejeté. Chaque interface possède une règle finale implicite "
    "<i>block any any</i>. La philosophie ANSSI du cloisonnement impose qu'un flux ne puisse "
    "traverser une zone que s'il est <b>nécessaire, identifié et tracé</b>.",
    styles['body']
))
story.append(Paragraph(
    "<b>Règle d'or</b> : un flux ne peut aller que d'une confiance égale ou supérieure vers "
    "une égale ou inférieure, et uniquement sur des ports métier explicites. Le retour vers "
    "le VLAN 10 n'est <b>jamais</b> initié depuis une zone plus sensible.",
    styles['callout']
))
story.append(Paragraph(
    "Ce principe transforme un compromission de poste en incident contenu : l'attaquant "
    "bloqué sur le VLAN 10 ne peut ni atteindre les bases de données (VLAN 30), ni "
    "compromettre le SIEM ou le bastion (VLAN 99). La latéralité est structurellement "
    "impossible.",
    styles['body']
))

# ============================================================
# 2. TOPOLOGIE VIRTUALBOX
# ============================================================
story.append(add_heading("2. Topologie VirtualBox", styles, 0))
story.append(Paragraph(
    "L'infrastructure est déployée sous VirtualBox. Chaque VLAN correspond à un "
    "<b>réseau interne VirtualBox</b> distinct (Internal Network), ce qui simule le zoning "
    "physique / VLAN 802.1Q sans équipement actif. OPNsense possède <b>5 interfaces "
    "réseau</b> : 1 NAT (WAN, accès Internet) + 4 réseaux internes correspondant aux "
    "VLANs 10, 20, 30 et 99. Le pare-feu est ainsi le seul point de passage entre les "
    "zones, garantissant que <b>aucun flux ne contourne le filtrage</b>.",
    styles['body']
))

story.append(Spacer(1, 6))
story.append(Paragraph(
    "<b>Tableau 2 — Mapping interfaces OPNsense / réseaux internes VirtualBox</b>",
    styles['caption']))
iface_data = [
    ["Interface", "Réseau interne VirtualBox", "VLAN", "OPNsense", "Adressage"],
    ["vtnet0", "vbox-wan (NAT)", "—", "WAN", "DHCP (10.0.2.0/24)"],
    ["vtnet1", "vbox-vlan10", "10", "LAN", "10.10.10.1/24"],
    ["vtnet2", "vbox-vlan20", "20", "OPT1", "10.10.20.1/24"],
    ["vtnet3", "vbox-vlan30", "30", "OPT2", "10.10.30.1/24"],
    ["vtnet4", "vbox-vlan99", "99", "OPT3", "10.10.99.1/24"],
]
story.append(make_table(iface_data, col_ratios=[0.13, 0.27, 0.10, 0.15, 0.35]))
story.append(Spacer(1, 12))

story.append(add_heading("2.1. Plan d'adressage", styles, 1))
story.append(Paragraph(
    "Le référentiel d'adressage est <font name='CodeFont'>10.10.X.0/24</font> où "
    "<font name='CodeFont'>X</font> identifie le VLAN. OPNsense porte toujours l'IP "
    "<font name='CodeFont'>.1</font> de chaque sous-réseau et sert de passerelle par "
    "défaut. Aucun hôte ne possède de route statique vers un autre VLAN : tout transite "
    "par OPNsense, qui filtre chaque flux.",
    styles['body']
))

story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 3 — Plan d'adressage par VLAN</b>", styles['caption']))
addr_data = [
    ["VLAN", "Réseau", "Passerelle", "Masque", "Plage hôtes", "DHCP"],
    ["10", "10.10.10.0/24", "10.10.10.1", "255.255.255.0", ".10 – .200", "Oui (OPNsense)"],
    ["20", "10.10.20.0/24", "10.10.20.1", "255.255.255.0", ".10 – .100", "Non (statique)"],
    ["30", "10.10.30.0/24", "10.10.30.1", "255.255.255.0", ".10 – .100", "AD (Win Server)"],
    ["99", "10.10.99.0/24", "10.10.99.1", "255.255.255.0", ".10 – .50", "Non (statique)"],
]
story.append(make_table(addr_data, col_ratios=[0.08, 0.18, 0.16, 0.17, 0.18, 0.23]))
story.append(Paragraph(
    "Le DHCP n'est activé que sur le VLAN 10 (bureautique). Les zones sensibles (DMZ, "
    "admin) fonctionnent en adresses strictement statiques, conformément au principe du "
    "moindre privilège. Le VLAN 30 délègue son DHCP au contrôleur Active Directory.",
    styles['caption']
))

story.append(add_heading("2.2. Affectation des hôtes", styles, 1))
story.append(Spacer(1, 4))
hosts_data = [
    ["Hôte", "VLAN", "IP", "Rôle", "OS"],
    ["OPNsense", "tous", ".1 / VLAN", "Pare-feu / routeur", "OPNsense"],
    ["Win10 (employé)", "10", "10.10.10.50", "Poste utilisateur", "Windows 10"],
    ["Kali (attaquant)", "10", "10.10.10.100", "Simulation d'attaque", "Kali Linux"],
    ["Reverse proxy", "20", "10.10.20.10", "Proxy inverse (DMZ)", "Ubuntu 22.04"],
    ["Passerelle VPN", "20", "10.10.20.20", "Accès distant", "Ubuntu 22.04"],
    ["Ubuntu (Web + BDD)", "30", "10.10.30.10", "Serveur métier", "Ubuntu 22.04"],
    ["Windows Server (AD)", "30", "10.10.30.20", "AD / DNS / DHCP", "Windows Server 2022"],
    ["Wazuh (SIEM)", "99", "10.10.99.10", "SIEM / XDR + Elastic", "Ubuntu 22.04"],
    ["Bastion NixOS", "99", "10.10.99.20", "PAW / administration", "NixOS"],
]
story.append(make_table(hosts_data, col_ratios=[0.20, 0.07, 0.16, 0.27, 0.30]))

# ============================================================
# 3. CONFIGURATION OPNSENSE
# ============================================================
story.append(add_heading("3. Configuration OPNsense", styles, 0))
story.append(Paragraph(
    "OPNsense est configuré de façon <b>reproductible</b> via une API REST, pilotée par "
    "quatre scripts shell versionnés dans le dépôt (<font name='CodeFont'>opnsense/scripts/</font>). "
    "Cette approche Infrastructure as Code garantit que la configuration du pare-feu est "
    "auditable, réversible et rejouable — un prérequis pour une posture DevSecOps.",
    styles['body']
))

story.append(add_heading("3.1. Activation de l'API REST", styles, 1))
story.append(Paragraph(
    "Les scripts exploitent l'<b>API REST native d'OPNsense</b> (authentification HTTP "
    "Basic, clé + secret). Son activation est un préalable indispensable :",
    styles['body']
))
story.append(Paragraph(
    "1. Interface web → <b>System → Settings → Administration</b> — cocher <i>Enable API</i>.<br/>"
    "2. Créer une clé API + secret via <b>System → Access → Users → root → Edit</b> "
    "(onglet « API keys »).<br/>"
    "3. Renseigner les valeurs dans <font name='CodeFont'>.env</font> :",
    styles['body_left']
))
story.append(code_block(
    'OPNSENSE_API_KEY="..."      # clé API générée\n'
    'OPNSENSE_API_SECRET="..."   # secret associé\n'
    'OPNSENSE_HOST="10.10.99.1"  # IP d\'administration (VLAN 99)'
))
story.append(Paragraph(
    "Aucune clé n'est versionnée : le fichier <font name='CodeFont'>.env</font> est exclu "
    "du dépôt via <font name='CodeFont'>.gitignore</font>. Seul le modèle "
    "<font name='CodeFont'>.env.example</font> est commité.",
    styles['body']
))

story.append(add_heading("3.2. Scripts d'automatisation", styles, 1))
story.append(Paragraph(
    "La configuration est appliquée séquentiellement par quatre scripts, chacun "
    "responsable d'un domaine. Ils sont <b>idempotents</b> et peuvent être ré-exécutés "
    "sans effet de bord.",
    styles['body']
))
story.append(Spacer(1, 6))
story.append(Paragraph(
    "<b>Tableau 4 — Scripts de configuration OPNsense</b>", styles['caption']))
scripts_data = [
    ["Script", "Description"],
    ["00-initial-setup.sh",
     "Configuration initiale et hardening global : vérification de l'API, "
     "changement du mot de passe admin, activation HTTPS (port 8443), "
     "désactivation des services inutiles (UPnP), syslog distant vers Wazuh, "
     "timeout de session, synchronisation NTP."],
    ["01-vlan-interfaces.sh",
     "Affectation des adresses IP des interfaces conformément au plan "
     "d'adressage (10.10.X.0/24). Activation du DHCP sur le VLAN 10, "
     "désactivation explicite sur les VLANs 20/30/99. Rechargement des "
     "interfaces (idempotent)."],
    ["02-firewall-rules.sh",
     "Application de la matrice de filtrage default-deny (voir section 4). "
     "Création des alias réseau, puis déploiement des règles block prioritaires "
     "et des règles allow métier, avant un block final explicite sur chaque "
     "interface."],
    ["03-nat-gateway.sh",
     "NAT sortant (masquerade) pour les VLANs autorisés, port forwarding des "
     "services publics (443 → reverse proxy, 51820 → VPN), création de l'alias "
     "dynamique active response et hardening WAN (bogon, réseaux privés)."],
]
story.append(make_table(scripts_data, col_ratios=[0.28, 0.72]))
story.append(Paragraph(
    "Ordre d'exécution (depuis la machine hôte ou le bastion) :",
    styles['body_left']
))
story.append(code_block(
    'export $(cat ../.env | xargs)\n'
    'bash scripts/00-initial-setup.sh\n'
    'bash scripts/01-vlan-interfaces.sh\n'
    'bash scripts/02-firewall-rules.sh\n'
    'bash scripts/03-nat-gateway.sh'
))

story.append(add_heading("3.3. Alias réseau", styles, 1))
story.append(Paragraph(
    "Les alias centralisent les objets réseau (sous-réseaux et hôtes) pour produire des "
    "règles <b>lisibles et maintenables</b>. Plutôt que d'écrire "
    "<font name='CodeFont'>10.10.99.10</font> dans chaque règle, on référence l'alias "
    "<font name='CodeFont'>host_wazuh</font>. Le script "
    "<font name='CodeFont'>02-firewall-rules.sh</font> définit <b>11 alias</b> réseau "
    "(4 sous-réseaux + 7 hôtes), auxquels s'ajoute l'alias dynamique "
    "<font name='CodeFont'>wazuh_blocked_ips</font> créé par "
    "<font name='CodeFont'>03-nat-gateway.sh</font> pour l'active response.",
    styles['body']
))
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 5 — Alias réseau OPNsense (11 alias)</b>", styles['caption']))
alias_data = [
    ["Alias", "Valeur", "Type", "Usage"],
    ["net_vlan10", "10.10.10.0/24", "Sous-réseau", "Zone bureautique"],
    ["net_vlan20", "10.10.20.0/24", "Sous-réseau", "Zone DMZ"],
    ["net_vlan30", "10.10.30.0/24", "Sous-réseau", "Zone critique"],
    ["net_vlan99", "10.10.99.0/24", "Sous-réseau", "Zone admin / SIEM"],
    ["host_wazuh", "10.10.99.10", "Hôte", "SIEM Wazuh (destination logs)"],
    ["host_bastion", "10.10.99.20", "Hôte", "Bastion NixOS (SSH admin)"],
    ["host_reverse_proxy", "10.10.20.10", "Hôte", "Reverse proxy (DMZ)"],
    ["host_vpn", "10.10.20.20", "Hôte", "Passerelle VPN (DMZ)"],
    ["host_ubuntu_web", "10.10.30.10", "Hôte", "Serveur Web + BDD"],
    ["host_win_server", "10.10.30.20", "Hôte", "AD / DNS / DHCP"],
    ["host_win10", "10.10.10.50", "Hôte", "Poste utilisateur"],
]
story.append(make_table(alias_data, col_ratios=[0.22, 0.20, 0.16, 0.42]))

# ============================================================
# 4. RÈGLES DE FILTRAGE
# ============================================================
story.append(add_heading("4. Règles de filtrage", styles, 0))
story.append(Paragraph(
    "La matrice de filtrage traduit la politique default-deny en règles explicites. Les "
    "règles <b>block</b> d'isolation des zones sensibles sont placées en priorité haute, "
    "suivies des règles <b>allow</b> métier, puis d'un block final explicite sur chaque "
    "interface. L'extrait ci-dessous présente les règles principales (le dépôt contient la "
    "matrice complète dans <font name='CodeFont'>architecture/firewall-rules.md</font>).",
    styles['body']
))

story.append(Spacer(1, 6))
story.append(Paragraph(
    "<b>Tableau 6 — Matrice de filtrage default-deny (extrait)</b>", styles['caption']))
rules_data = [
    ["Source", "Destination", "Port(s)", "Action", "Justification"],
    ["VLAN 10", "host_reverse_proxy", "80, 443", "Allow",
     "Accès au reverse proxy uniquement"],
    ["VLAN 10", "host_vpn", "443", "Allow",
     "Accès à la passerelle VPN"],
    ["VLAN 10", "VLAN 30", "any", "Block",
     "Isolation totale de la zone critique"],
    ["VLAN 10", "VLAN 99", "any", "Block",
     "Isolation totale de la zone admin"],
    ["VLAN 10", "WAN", "53, 80, 443", "Allow",
     "DNS + HTTP(S) sortant (via OPNsense)"],
    ["VLAN 10", "host_wazuh", "514", "Allow",
     "Syslog bureautique vers Wazuh"],
    ["Reverse proxy", "host_ubuntu_web", "80, 443", "Allow",
     "Reverse proxy → serveur Web métier"],
    ["VPN (DMZ)", "VLAN 30", "any", "Block",
     "Le VPN ne doit pas atteindre la BDD directement"],
    ["VLAN 30", "host_win_server", "53", "Allow",
     "Résolution DNS via l'Active Directory"],
    ["VLAN 30", "host_wazuh", "1514, 1515", "Allow",
     "Flux de logs des serveurs vers Wazuh"],
    ["VLAN 30", "VLAN 99", "any", "Block",
     "Aucun autre flux vers la zone admin"],
    ["Bastion (VLAN 99)", "VLAN 30", "22", "Allow",
     "SSH admin du bastion vers les serveurs"],
    ["VLAN 99 (hors bastion)", "VLAN 30", "any", "Block",
     "Seul le bastion peut SSH, pas Wazuh"],
    ["VLAN 99", "WAN", "123", "Allow",
     "NTP pour la synchronisation SIEM"],
    ["VLAN 99", "WAN", "80, 443", "Allow",
     "Mises à jour Wazuh / Elastic"],
    ["WAN", "host_reverse_proxy", "443", "Allow",
     "Accès public au reverse proxy"],
    ["WAN", "host_vpn", "51820", "Allow",
     "Accès VPN entrant (WireGuard)"],
    ["WAN", "VLAN 30", "any", "Block",
     "Aucune exposition de la zone critique"],
    ["WAN", "VLAN 99", "any", "Block",
     "Aucune exposition de la zone admin"],
    ["* (toutes)", "any", "any", "Block",
     "Règle finale implicite — default-deny"],
]
story.append(make_table(rules_data, col_ratios=[0.20, 0.20, 0.13, 0.10, 0.37]))

story.append(add_heading("4.1. Ordre d'évaluation", styles, 1))
story.append(Paragraph(
    "Les règles sont évaluées <b>de haut en bas</b>, la première correspondance l'emportant "
    "(first-match wins). L'ordre reflète la priorité dans OPNsense : les règles <b>block</b> "
    "d'isolation précèdent les règles <b>allow</b>, de sorte qu'un flux interdit ne puisse "
    "jamais être autorisé par une règle plus permissive placée plus bas. La règle finale "
    "<i>block any any</i> (présente sur chaque interface) garantit qu'aucun flux oublié ne "
    "passe.",
    styles['body']
))

story.append(add_heading("4.2. Logging", styles, 1))
story.append(Paragraph(
    "Toutes les règles <b>block</b> et les règles <b>allow</b> sensibles (inter-zone) "
    "activent explicitement le logging (<font name='CodeFont'>log = yes</font>). Les logs "
    "OPNsense ont une double destination :",
    styles['body']
))
story.append(Paragraph(
    "• consultation locale — <i>Firewall → Log Files</i> sur l'interface web ;<br/>"
    "• transfert vers Wazuh en syslog UDP 514, pour corrélation SIEM en temps réel.",
    styles['bullet']
))
story.append(Paragraph(
    "Cette journalisation croisée permet au SIEM de détecter des patterns d'attaque "
    "(scans, tentatives répétées) à partir des drops du pare-feu, et de déclencher une "
    "active response (voir section 7).",
    styles['body']
))

# ============================================================
# 5. NAT ET PORT FORWARDING
# ============================================================
story.append(add_heading("5. NAT et port forwarding", styles, 0))
story.append(Paragraph(
    "OPNsense assure deux fonctions de traduction d'adresses : le <b>NAT sortant</b> "
    "(masquerade) qui permet aux VMs autorisées d'accéder à Internet, et le <b>port "
    "forwarding</b> qui publie les services publics de la DMZ. Ces deux mécanismes sont "
    "configurés par le script <font name='CodeFont'>03-nat-gateway.sh</font>.",
    styles['body']
))

story.append(add_heading("5.1. NAT sortant", styles, 1))
story.append(Paragraph(
    "Le NAT sortant fonctionne en mode <b>hybrid</b> avec des règles explicites par VLAN. "
    "L'accès Internet est accordé aux VLANs 10, 20 et 99, mais <b>refusé au VLAN 30</b> "
    "(zone critique) : les serveurs métier n'ont aucun besoin d'accéder directement à "
    "Internet, et cette absence de route sortante supprime une classe entière de vecteurs "
    "d'exfiltration et de C2 (command & control).",
    styles['body']
))
story.append(Spacer(1, 4))
story.append(Paragraph("<b>Tableau 7 — NAT sortant par VLAN</b>", styles['caption']))
nat_data = [
    ["VLAN", "NAT sortant", "Justification"],
    ["10 — Bureautique", "Oui (masquerade WAN)",
     "DNS et navigation Web des postes"],
    ["20 — DMZ", "Oui (masquerade WAN)",
     "Mises à jour des services DMZ"],
    ["30 — Critique", "Non (aucune règle)",
     "Isolation sortante — anti-exfiltration"],
    ["99 — Admin / SIEM", "Oui (masquerade WAN)",
     "Mises à jour Wazuh / Elastic, NTP"],
]
story.append(make_table(nat_data, col_ratios=[0.22, 0.26, 0.52]))

story.append(add_heading("5.2. Port forwarding (services publics)", styles, 1))
story.append(Paragraph(
    "Seuls deux services de la DMZ sont publiés vers Internet. Aucun port n'est jamais "
    "directement redirigé vers le VLAN 30 ou le VLAN 99, conformément au default-deny.",
    styles['body']
))
story.append(Spacer(1, 4))
story.append(Paragraph("<b>Tableau 8 — Règles de port forwarding WAN → DMZ</b>", styles['caption']))
pf_data = [
    ["Port WAN", "Protocole", "Cible (DMZ)", "Port local", "Service"],
    ["443", "TCP", "host_reverse_proxy (10.10.20.10)", "443",
     "Reverse proxy public (HTTPS)"],
    ["51820", "UDP", "host_vpn (10.10.20.20)", "51820",
     "VPN WireGuard (accès distant)"],
]
story.append(make_table(pf_data, col_ratios=[0.12, 0.12, 0.34, 0.14, 0.28]))
story.append(Paragraph(
    "Le reverse proxy sert de point d'entrée unique pour les services Web publics et "
    "termine les connexions TLS ; il forward ensuite vers le serveur métier du VLAN 30 sur "
    "les ports 80/443 (règle allow dédiée). La passerelle VPN expose le port WireGuard "
    "51820/udp pour l'accès distant.",
    styles['body']
))

story.append(add_heading("5.3. Alias dynamique et active response", styles, 1))
story.append(Paragraph(
    "Le script <font name='CodeFont'>03-nat-gateway.sh</font> crée un alias dynamique "
    "<b><font name='CodeFont'>wazuh_blocked_ips</font></b> (type host, initialement vide) "
    "et une règle <b>block</b> placée en priorité haute sur le WAN, dont la source référence "
    "cet alias. Wazuh peut ainsi injecter à la volée des IP à bloquer via l'API OPNsense "
    "(<font name='CodeFont'>/api/firewall/alias/addItem</font>) ; le rechargement de "
    "l'alias propage immédiatement le blocage sur toutes les interfaces. Ce mécanisme est "
    "détaillé section 7.",
    styles['body']
))
story.append(Paragraph(
    "Le script applique également un <b>hardening WAN</b> : filtrage des réseaux bogon et "
    "des plages privées sur l'interface externe (anti-spoofing).",
    styles['body']
))

# ============================================================
# 6. CHOIX OPNSENSE VS PFSENSE
# ============================================================
story.append(add_heading("6. Choix OPNsense vs pfSense", styles, 0))
story.append(Paragraph(
    "OPNsense et pfSense sont deux pare-feux open-source dérivés de m0n0wall, tous deux "
    "basés sur FreeBSD et le moteur pf. Le projet Defend-The-Core a retenu <b>OPNsense</b> "
    "pour quatre raisons techniques déterminantes, résumées dans le tableau ci-dessous.",
    styles['body']
))
story.append(Spacer(1, 6))
story.append(Paragraph(
    "<b>Tableau 9 — Comparatif OPNsense vs pfSense</b>", styles['caption']))
comp_data = [
    ["Critère", "OPNsense", "pfSense"],
    ["API REST native",
     "API REST intégrée et documentée — automatisation IaC directe",
     "API REST partielle ; dépend de l'API legacy XMLRPC"],
    ["Interface web",
     "Interface moderne (framework Phalcon), UX claire et responsive",
     "Interface plus ancienne, moins uniforme"],
    ["Fréquence de mises à jour",
     "Releases majeures fréquentes (~2 semestrielles) + correctifs réguliers",
     "Cycle plus lent, correctifs moins fréquents"],
    ["Communauté & écosystème",
     "Communauté active, plugins tiers, intégration cloud native",
     "Communauté établie mais plus conservatrice"],
    ["Licence & modèle",
     "BSD, projet communautaire soutenu par Deciso (pas de verrou)",
     "Apache 2.0, soutenu par Netgate (édition CE vs plus)"],
    ["Sécurité par défaut",
     "Hardening intégré, reporting IDS/IPS (Suricata) mature",
     "Fonctionnalité IDS/IPS présente, configuration plus manuelle"],
]
story.append(make_table(comp_data, col_ratios=[0.22, 0.42, 0.36]))
story.append(Paragraph(
    "<b>Verdict</b> : la présence d'une <b>API REST native</b> est le critère décisif. Elle "
    "rend la configuration du pare-feu entièrement scriptable et reproductible — un "
    "prérequis pour la posture Infrastructure as Code du projet. C'est précisément cette "
    "API qui permet aux quatre scripts de configurer le zoning, les règles et le NAT sans "
    "intervention manuelle, et à Wazuh d'injecter des blocages dynamiques en active "
    "response.",
    styles['callout']
))

# ============================================================
# 7. INTÉGRATION WAZUH (ACTIVE RESPONSE)
# ============================================================
story.append(add_heading("7. Intégration Wazuh (active response)", styles, 0))
story.append(Paragraph(
    "L'active response ferme la boucle détection → réaction. Lorsque Wazuh corrèle une "
    "attaque (bruteforce SSH, scan réseau, mouvement latéral) et déclenche une alerte de "
    "niveau ≥ 10, il exécute automatiquement le script "
    "<font name='CodeFont'>wazuh/rules/active-response/block-attacker.sh</font>. Ce script "
    "ajoute l'IP source à l'alias <b><font name='CodeFont'>wazuh_blocked_ips</font></b> sur "
    "OPNsense via l'API REST, propageant un blocage immédiat sur l'ensemble des interfaces.",
    styles['body']
))

story.append(add_heading("7.1. Mécanisme de blocage automatique", styles, 1))
story.append(Paragraph(
    "Le flux d'active response se déroule en cinq étapes :",
    styles['body']
))
story.append(Paragraph(
    "1. <b>Détection</b> — Wazuh corrèle les logs (OPNsense syslog, agents) et déclenche "
    "une alerte de niveau ≥ 10 (règles 100100, 100101, 100200…).<br/>"
    "2. <b>Déclenchement</b> — le manager exécute <font name='CodeFont'>block-attacker.sh</font> "
    "avec l'IP source de l'alerte.<br/>"
    "3. <b>Injection</b> — le script valide l'IP (anti-injection) puis l'ajoute à l'alias "
    "<font name='CodeFont'>wazuh_blocked_ips</font> via "
    "<font name='CodeFont'>POST /api/firewall/alias/addItem</font>.<br/>"
    "4. <b>Propagation</b> — rechargement de l'alias et du filtre "
    "(<font name='CodeFont'>alias/reconfigure</font>, <font name='CodeFont'>filter/apply</font>) ; "
    "le blocage est effectif en quelques secondes.<br/>"
    "5. <b>Débloquage</b> — après un timeout (3600 s par défaut), Wazuh rappelle le script "
    "en mode <font name='CodeFont'>delete</font> et retire l'IP de l'alias.",
    styles['bullet']
))

story.append(Paragraph(
    "L'alias <font name='CodeFont'>wazuh_blocked_ips</font> est donc un <b>pont dynamique</b> "
    "entre le SIEM et le pare-feu : il transforme une détection logicielle en action "
    "réseau, sans intervention humaine.",
    styles['body']
))

story.append(add_heading("7.2. Règle de pare-feu correspondante", styles, 1))
story.append(Paragraph(
    "La règle de blocage est créée par <font name='CodeFont'>03-nat-gateway.sh</font> et "
    "placée en <b>priorité haute sur le WAN</b>, de sorte qu'une IP bloquée soit rejetée "
    "avant toute autre règle allow :",
    styles['body']
))
story.append(code_block(
    '{\n'
    '    "rule": {\n'
    '        "interface": "wan",\n'
    '        "action": "block",\n'
    '        "protocol": "any",\n'
    '        "source": "wazuh_blocked_ips",\n'
    '        "destination": "any",\n'
    '        "descr": "Block IPs detectees par Wazuh (active response)",\n'
    '        "log": "1"\n'
    '    }\n'
    '}'
))

story.append(add_heading("7.3. Sécurités du script active response", styles, 1))
story.append(Paragraph(
    "Le script <font name='CodeFont'>block-attacker.sh</font> intègre plusieurs garde-fous "
    "pour éviter les blocages abusifs ou l'injection :",
    styles['body']
))
story.append(Paragraph(
    "• <b>Validation d'IP</b> — l'IP source est contrôlée par expression régulière avant "
    "tout appel API (anti-injection de payload).<br/>"
    "• <b>Whitelist implicite</b> — le bastion (10.10.99.20), Wazuh (10.10.99.10) et "
    "localhost ne sont jamais bloqués, même s'ils apparaissent comme source d'une alerte.<br/>"
    "• <b>Fallback local</b> — si l'API OPNsense est injoignable ou les clés absentes, le "
    "script bascule sur un blocage <font name='CodeFont'>iptables</font> local pour ne "
    "jamais rester sans défense.<br/>"
    "• <b>Timeout de déblocage</b> — configuration <font name='CodeFont'><timeout>3600</timeout></font> "
    "dans <font name='CodeFont'>ossec.conf</font> ; l'IP est libérée automatiquement après 1 h.",
    styles['bullet']
))
story.append(Paragraph(
    "Ce mécanisme illustre le pilier « Détection » du projet : un réseau fermé (default-deny) "
    "ne suffit pas — il faut aussi <b>réagir en temps réel</b> aux attaques observées, sans "
    "attendre une intervention humaine.",
    styles['callout']
))

# ============================================================
# BUILD
# ============================================================
doc.multiBuild(story)
print(f"PDF généré : {OUTPUT}")
