#!/usr/bin/env python3
"""
Générateur PDF : Document maître d'architecture (00_architecture_maitre.pdf)
Synthèse : contexte PME, problème latéralité, architecture zoning ANSSI,
topologie, plan d'adressage, matrice de flux, choix technologiques, scénarios.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_common import *
from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable

register_fonts()
styles = get_styles()

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'docs', '00_architecture_maitre.pdf')

doc = build_doc(OUTPUT, "Defend-The-Core — Architecture maîtresse")
story = []

# ============================================================
# PAGE DE TITRE
# ============================================================
story.append(Spacer(1, 80))
story.append(Paragraph("Defend-The-Core", styles['title']))
story.append(HRFlowable(width="40%", thickness=2, color=ACCENT, spaceBefore=6, spaceAfter=12))
story.append(Paragraph("Infrastructure PME critique sécurisée", styles['subtitle']))
story.append(Spacer(1, 20))
story.append(Paragraph(
    "Document maître d'architecture<br/>"
    "Synthèse des choix techniques et de la posture de sécurité",
    ParagraphStyle('Desc', fontName='BodyFont', fontSize=11, leading=16,
                   textColor=TEXT_MUTED, alignment=TA_LEFT)
))
story.append(Spacer(1, 40))
story.append(Paragraph(
    "Conformité ANSSI · Zero Trust · DevSecOps · Infrastructure as Code",
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
# 1. CONTEXTE ET PROBLÉMATIQUE
# ============================================================
story.append(add_heading("1. Contexte et problématique", styles, 0))
story.append(Paragraph(
    "Ce projet répond à un besoin concret rencontré dans la plupart des PME manipulant "
    "des données sensibles (cabinets d'audit financier, industrie, santé). L'infrastructure "
    "existante est typiquement « plate » : tous les postes et serveurs sont sur le même "
    "réseau, sans cloisonnement. Si un poste utilisateur est compromis par un phishing — "
    "vecteur d'attaque n°1 — l'attaquant peut se propager latéralement jusqu'aux serveurs "
    "de bases de données, compromettant l'intégralité du système d'information.",
    styles['body']
))
story.append(Spacer(1, 8))
story.append(Paragraph(
    "La reconstruction de cette infrastructure selon les recommandations de l'ANSSI vise "
    "trois objectifs : <b>empêcher la propagation latérale</b> (segmentation), "
    "<b>détecter et réagir</b> aux attaques (SIEM), et <b>sécuriser l'administration</b> "
    "(bastion immuable).",
    styles['body']
))

story.append(add_heading("1.1. Le risque de latéralité", styles, 1))
story.append(Paragraph(
    "Dans un réseau plat, la compromission d'un seul poste suffit à un attaquant pour "
    "scanner l'ensemble du réseau, identifier les serveurs, et exploiter leurs "
    "vulnérabilités. C'est le schéma classique d'une attaque : phishing → compromission "
    "poste → reconnaissance réseau → mouvement latéral → exfiltration de données.",
    styles['body']
))
story.append(Paragraph(
    "Le cloisonnement en zones de confiance (zoning) brise cette chaîne : même si un "
    "poste est compromis, l'attaquant ne voit et ne peut atteindre que ce qui lui est "
    "explicitement autorisé.",
    styles['body']
))

# ============================================================
# 2. ARCHITECTURE RÉSEAU (ZONING & VLANs)
# ============================================================
story.append(add_heading("2. Architecture réseau — zoning et VLANs", styles, 0))
story.append(Paragraph(
    "L'infrastructure est segmentée en <b>quatre zones de confiance</b>, chacune "
    "correspondant à un VLAN distinct, cloisonnées par un pare-feu OPNsense en "
    "<b>default-deny</b>. Le niveau de confiance décroît du VLAN 99 (admin) au VLAN 10 "
    "(bureautique, non fiable).",
    styles['body']
))

story.append(Spacer(1, 12))
story.append(Paragraph("<b>Tableau 1 — Zones de confiance</b>", styles['caption']))
zones_data = [
    ["VLAN", "Zone", "Réseau", "Confiance", "Rôle"],
    ["10", "Bureautique", "10.10.10.0/24", "Faible", "Postes utilisateurs (vecteur d'attaque)"],
    ["20", "DMZ", "10.10.20.0/24", "Moyenne", "Services exposés (proxy, VPN)"],
    ["30", "Critique", "10.10.30.0/24", "Haute", "Serveurs métier, BDD"],
    ["99", "Admin/SIEM", "10.10.99.0/24", "Maximale", "Surveillance, bastion"],
]
story.append(make_table(zones_data, col_ratios=[0.08, 0.14, 0.18, 0.12, 0.48]))
story.append(Spacer(1, 16))

story.append(add_heading("2.1. Principe directeur : default-deny", styles, 1))
story.append(Paragraph(
    "Le pare-feu OPNsense applique une politique <b>default-deny</b> : tout flux non "
    "explicitement autorisé est rejeté. Chaque interface possède une règle finale "
    "implicite <i>block any any</i>. La philosophie ANSSI du cloisonnement impose qu'un "
    "flux ne puisse traverser une zone que s'il est nécessaire, identifié et tracé.",
    styles['body']
))
story.append(Paragraph(
    "<b>Règle d'or</b> : un flux ne peut aller que d'une confiance égale ou supérieure "
    "vers une égale ou inférieure, et uniquement sur des ports métier explicites. Le "
    "retour vers le VLAN 10 n'est jamais initié.",
    styles['callout']
))

story.append(add_heading("2.2. Règles de flux clés", styles, 1))
rules_data = [
    ["Source", "Destination", "Port(s)", "Action", "Justification"],
    ["VLAN 10", "VLAN 20", "80, 443", "Allow", "Accès reverse proxy uniquement"],
    ["VLAN 10", "VLAN 30", "*", "Block", "Isolation totale zone critique"],
    ["VLAN 10", "VLAN 99", "*", "Block", "Isolation zone admin"],
    ["VLAN 99 (bastion)", "VLAN 30", "22", "Allow", "SSH admin via bastion"],
    ["Tous", "VLAN 99 (Wazuh)", "514, 1514", "Allow", "Flux de logs vers SIEM"],
    ["WAN", "VLAN 20", "443", "Allow", "Accès VPN / services publics"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 2 — Règles de flux inter-VLAN (extrait)</b>", styles['caption']))
story.append(make_table(rules_data, col_ratios=[0.18, 0.16, 0.12, 0.10, 0.44]))
story.append(Paragraph(
    "La matrice complète des 20 règles est documentée dans le fichier "
    "<font name='CodeFont'>architecture/firewall-rules.md</font> du dépôt.",
    styles['caption']
))

# ============================================================
# 3. TOPOLOGIE ET COMPOSANTS
# ============================================================
story.append(add_heading("3. Topologie et composants", styles, 0))
story.append(Paragraph(
    "L'infrastructure est déployée sous VirtualBox. Chaque VLAN correspond à un réseau "
    "interne VirtualBox distinct, ce qui simule le zoning physique/VLAN 802.1Q sans "
    "équipement actif. OPNsense possède 5 interfaces réseau : 1 NAT (WAN) + 4 réseaux "
    "internes (VLANs 10, 20, 30, 99).",
    styles['body']
))

story.append(add_heading("3.1. Cartographie des VMs", styles, 1))
vms_data = [
    ["VM", "Rôle", "Technologie", "VLAN", "IP"],
    ["OPNsense", "Pare-feu / routeur", "OPNsense", "tous", ".1/VLAN"],
    ["Wazuh", "SIEM / XDR", "Wazuh + Elastic", "99", "10.10.99.10"],
    ["Bastion", "PAW / administration", "NixOS", "99", "10.10.99.20"],
    ["Win Server", "AD, DNS, DHCP", "Windows Server 2022", "30", "10.10.30.20"],
    ["Ubuntu", "Web + BDD", "Ubuntu 22.04, Nginx, PG", "30", "10.10.30.10"],
    ["Win 10", "Poste employé", "Windows 10", "10", "10.10.10.50"],
    ["Kali", "Attaquant (démo)", "Kali Linux", "10", "10.10.10.100"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 3 — Composants de l'infrastructure</b>", styles['caption']))
story.append(make_table(vms_data, col_ratios=[0.14, 0.18, 0.22, 0.08, 0.18]))

# ============================================================
# 4. CHOIX TECHNOLOGIQUES JUSTIFIÉS
# ============================================================
story.append(add_heading("4. Choix technologiques justifiés", styles, 0))

story.append(add_heading("4.1. OPNsense (pare-feu)", styles, 1))
story.append(Paragraph(
    "Choisi plutôt que pfSense pour son interface plus moderne, son orientation open-source "
    "et sa API REST native, essentielle pour l'automatisation (Infrastructure as Code). "
    "OPNsense assure le routage inter-VLAN avec filtrage strict, le NAT sortant, le port "
    "forwarding des services publics, et l'intégration avec Wazuh (alias dynamique pour "
    "l'active response).",
    styles['body']
))

story.append(add_heading("4.2. Wazuh (SIEM/XDR)", styles, 1))
story.append(Paragraph(
    "Préféré à un Elastic pur pour ses capacités natives de détection (règles OSSEC), "
    "d'active response (blocage automatique d'IP) et de Security Configuration Assessment "
    "(vérification continue du durcissement CIS). Wazuh combine la collecte de logs, la "
    "corrélation, l'alerting et la réaction automatique en une seule solution.",
    styles['body']
))

story.append(add_heading("4.3. NixOS (bastion/PAW)", styles, 1))
story.append(Paragraph(
    "C'est le choix le plus stratégique du projet. NixOS offre une caractéristique unique : "
    "la <b>configuration déclarative et immuable</b>. Toute la configuration système est "
    "décrite dans <font name='CodeFont'>configuration.nix</font>. Toute modification "
    "manuelle d'un fichier de configuration est <b>écrasée</b> au prochain "
    "<font name='CodeFont'>nixos-rebuild switch</font>. Il est donc impossible pour un "
    "attaquant de persister une backdoor dans un fichier de config système. De plus, "
    "l'état du système est versionnable dans Git → reproductibilité totale.",
    styles['body']
))
story.append(Paragraph(
    "<b>Argument clé</b> : l'immuabilité empêche la persistance. Si un attaquant modifie "
    "<font name='CodeFont'>/etc/ssh/sshd_config</font> pour ajouter un mot de passe, "
    "NixOS l'écrasera au prochain déploiement.",
    styles['callout']
))

story.append(add_heading("4.4. Ubuntu 22.04 (serveur métier)", styles, 1))
story.append(Paragraph(
    "Distribution LTS standard pour le serveur Web + BDD. Le durcissement suit le CIS "
    "Benchmark (sysctl, auditd, UFW, PAM, SSH clés uniquement). PostgreSQL écoute "
    "uniquement sur localhost (pas d'exposition réseau), Nginx sert de serveur Web avec "
    "en-têtes de sécurité et TLS 1.2/1.3.",
    styles['body']
))

story.append(add_heading("4.5. Windows Server 2022 (AD/DNS/DHCP)", styles, 1))
story.append(Paragraph(
    "Contrôleur de domaine Active Directory pour la gestion d'identité. Le durcissement "
    "inclut : SMBv1 désactivé (anti EternalBlue), Windows Defender activé (realtime + "
    "cloud), NLA pour RDP, audit complet, GPO de sécurité (politique de mots de passe, "
    "restriction logicielle).",
    styles['body']
))

# ============================================================
# 5. LES TROIS PILIERS DE SÉCURITÉ
# ============================================================
story.append(add_heading("5. Les trois piliers de sécurité", styles, 0))
pillars_data = [
    ["Pilier", "Objectif", "Mise en œuvre", "Bénéfice"],
    ["1. Zoning", "Empêcher la propagation latérale",
     "VLANs 10/20/30/99 + OPNsense default-deny",
     "Poste compromis ≠ tout le réseau"],
    ["2. Détection", "Détecter et réagir aux attaques",
     "Wazuh SIEM + active response (blocage IP auto)",
     "Réaction temps réel, sans humain"],
    ["3. Administration", "Sécuriser l'accès privilégié",
     "Bastion NixOS immuable + ProxyJump + FIDO2",
     "Anti-persistance, traçabilité"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 4 — Les trois piliers</b>", styles['caption']))
story.append(make_table(pillars_data, col_ratios=[0.12, 0.22, 0.34, 0.32]))

# ============================================================
# 6. SCÉNARIOS DE VALIDATION
# ============================================================
story.append(add_heading("6. Scénarios de validation", styles, 0))
story.append(Paragraph(
    "Pour un entretien, ce n'est pas l'installation qui compte, mais la démonstration "
    "que les défenses fonctionnent. Trois scénarios sont préparés :",
    styles['body']
))

scenarios_data = [
    ["#", "Scénario", "Démo", "Résultat attendu"],
    ["1", "Détection SIEM", "Bruteforce SSH depuis Kali",
     "Wazuh détecte → IP bloquée automatiquement (active response)"],
    ["2", "Zero Trust", "Ping Win10 → VLAN 30/99",
     "Échec : OPNsense bloque (default-deny), logs de drop visibles"],
    ["3", "PAW NixOS", "SSH direct vs ProxyJump",
     "Accès direct impossible ; Win → Bastion → Serveur fonctionne ; immuabilité"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 5 — Scénarios de démonstration</b>", styles['caption']))
story.append(make_table(scenarios_data, col_ratios=[0.05, 0.15, 0.30, 0.50]))

# ============================================================
# 7. INFRASTRUCTURE AS CODE
# ============================================================
story.append(add_heading("7. Infrastructure as Code (GitOps)", styles, 0))
story.append(Paragraph(
    "L'intégralité de l'infrastructure est versionnée dans un dépôt Git (GitHub). Chaque "
    "composant — configuration NixOS, scripts OPNsense, règles Wazuh, durcissement Ubuntu, "
    "GPO Windows — est décrit sous forme de code reproductible. Cette approche DevSecOps "
    "garantit :",
    styles['body']
))
iac_points = [
    "<b>Reproductibilité</b> : deux déploiements identiques produisent le même état.",
    "<b>Traçabilité</b> : chaque modification est un commit Git, auditable et réversible.",
    "<b>Collaboration</b> : revue de code (pull requests) avant tout changement de configuration.",
    "<b>Récupération</b> : en cas de compromission, redéploiement rapide depuis le dépôt.",
]
for pt in iac_points:
    story.append(Paragraph(f"• {pt}", styles['bullet']))

story.append(Spacer(1, 12))
story.append(Paragraph(
    "Le dépôt contient également les 3 scénarios d'attaque reproductibles (Kali) et les "
    "dashboards Wazuh exportés, permettant de rejouer les démonstrations à volonté.",
    styles['body']
))

# ============================================================
# 8. CONFORMITÉ ANSSI
# ============================================================
story.append(add_heading("8. Conformité aux recommandations ANSSI", styles, 0))
anssi_data = [
    ["Recommandation ANSSI", "Mise en œuvre dans le projet"],
    ["Cloisonnement en zones de confiance", "4 VLANs (10/20/30/99) + pare-feu default-deny"],
    ["Principe du moindre privilège réseau", "Flux inter-VLAN explicites uniquement"],
    ["Authentification forte", "Clés SSH + FIDO2 (facteur matériel), root interdit"],
    ["Surveillance centralisée", "SIEM Wazuh : collecte, corrélation, alerting, réaction"],
    ["Journalisation et traçabilité", "auditd + logs forwardés vers Wazuh + sudo logging"],
    ["Administration sécurisée", "Bastion (PAW) + ProxyJump + immuabilité NixOS"],
    ["Durcissement des systèmes", "CIS Benchmark (Ubuntu, Windows) + sysctl + UFW"],
    ["Gestion des mises à jour", "Auto-upgrade sécurité (Ubuntu, NixOS, Windows)"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 6 — Correspondance ANSSI</b>", styles['caption']))
story.append(make_table(anssi_data, col_ratios=[0.40, 0.60]))

# ============================================================
# 9. PITCH POUR L'ENTRETIEN
# ============================================================
story.append(add_heading("9. Structure de présentation en entretien", styles, 0))
story.append(Paragraph(
    "La présentation suit une structure orientée <b>bénéfice métier</b> plutôt que technique :",
    styles['body']
))
pitch_data = [
    ["Étape", "Message", "Argument"],
    ["1. Problème", "Le risque n°1 en PME est la latéralité",
     "Un poste compromis = tout le réseau exposé"],
    ["2. Architecture", "Segmentation en zones (ANSSI/VLANs)",
     "Moindre privilège réseau via OPNsense"],
    ["3. Détection", "Un réseau fermé ne suffit pas",
     "Wazuh corrèle les logs et réagit en temps réel"],
    ["4. Administration", "Le point critique : l'accès privilégié",
     "Bastion NixOS = immuabilité, anti-persistance"],
    ["5. Bonus", "Tout est Infrastructure as Code sur GitHub",
     "Posture DevSecOps moderne"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 7 — Structure du pitch</b>", styles['caption']))
story.append(make_table(pitch_data, col_ratios=[0.10, 0.32, 0.58]))

story.append(Spacer(1, 16))
story.append(Paragraph(
    "<i>Les annexes suivantes détaillent chaque domaine :</i><br/>"
    "• Annexe 1 — Réseau & OPNsense<br/>"
    "• Annexe 2 — Sécurité & Wazuh (SIEM)<br/>"
    "• Annexe 3 — Durcissement des serveurs (Linux & Windows)<br/>"
    "• Annexe 4 — Administration sécurisée & Bastion NixOS",
    styles['body_left']
))

# ============================================================
# BUILD
# ============================================================
doc.multiBuild(story)
print(f"PDF généré : {OUTPUT}")
