#!/usr/bin/env python3
"""
Générateur PDF : 05 — Guide d'installation pas à pas (KVM/QEMU)
Trace complète des étapes d'installation de l'infrastructure Defend-The-Core
en local avec KVM/QEMU sous Linux Mint 22.
Couvre : vérification du support KVM, installation des paquets, configuration
libvirt, plan d'allocation des ressources, création des VLANs isolés,
téléchargement des ISO, création des VMs (OPNsense, Wazuh, Bastion NixOS,
serveurs et postes clients), vérifications, cheat sheet et dépannage.
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_common import *
from reportlab.platypus import (
    Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable, Preformatted
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle

register_fonts()
styles = get_styles()

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'docs', '05_guide_installation.pdf')

doc = build_doc(OUTPUT, "Defend-The-Core — Guide d'installation pas à pas")
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
story.append(Spacer(1, 60))
story.append(Paragraph("Defend-The-Core", styles['title']))
story.append(HRFlowable(width="40%", thickness=2, color=ACCENT, spaceBefore=6, spaceAfter=12))
story.append(Paragraph("Infrastructure PME critique sécurisée", styles['subtitle']))
story.append(Spacer(1, 20))
story.append(Paragraph(
    "Guide d'installation pas à pas (KVM/QEMU)<br/>"
    "Trace des étapes de déploiement de l'infrastructure en local",
    ParagraphStyle('Desc', fontName='BodyFont', fontSize=11, leading=16,
                   textColor=TEXT_MUTED, alignment=TA_LEFT)
))
story.append(Spacer(1, 30))
story.append(Paragraph(
    "KVM/QEMU " + AMP + " libvirt " + AMP + " OPNsense " + AMP + " NixOS " + AMP + " Zero Trust",
    ParagraphStyle('Tags', fontName='HeadFont', fontSize=10, leading=14,
                   textColor=ACCENT, alignment=TA_LEFT)
))
story.append(Spacer(1, 6))
story.append(Paragraph(
    "« Hôte Linux Mint 22, 32 Go RAM, 250 Go disque — 7 VMs segmentées en 4 VLANs. »",
    ParagraphStyle('Quote', fontName='BodyFont-Italic', fontSize=10, leading=14,
                   textColor=TEXT_MUTED, alignment=TA_LEFT)
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
# 1. INTRODUCTION
# ============================================================
story.append(add_heading("1. Introduction", styles, 0))
story.append(Paragraph(
    "Ce document est la <b>trace pas à pas</b> de l'installation de l'infrastructure "
    "Defend-The-Core sur un poste de travail local, à l'aide de l'hyperviseur "
    "<b>KVM/QEMU</b> piloté par <b>libvirt</b>. L'objectif est double : constituer "
    "un journal reproductible de toutes les opérations effectuées (pré-requis, "
    "installation des paquets, configuration des réseaux isolés, création des VMs, "
    "tests) et fournir un mode opératoire utilisable pour rejouer le déploiement "
    "à l'identique sur une autre machine.",
    styles['body']
))
story.append(Paragraph(
    "Contrairement à VirtualBox, KVM/QEMU est l'hyperviseur <b>natif du noyau Linux</b> : "
    "il bénéficie de l'accélération matérielle directe (VT-x/AMD-V), d'une intégration "
    "profonde avec systemd et d'un outillage mature (libvirt, virt-manager). Ce choix "
    "reflète une démarche d'ingénierie réaliste : sur un serveur Linux de production, "
    "KVM/QEMU est la solution de virtualisation de référence. Les réseaux internes "
    "VirtualBox sont ici remplacés par des <b>réseaux isolés libvirt</b>, qui simulent "
    "le zoning 802.1Q sans équipement actif.",
    styles['body']
))
story.append(Paragraph(
    "Chaque section décrit une étape avec ses commandes exactes (exécutées en tant "
    "que simple utilisateur membre des groupes <font name='CodeFont'>libvirt</font> "
    "et <font name='CodeFont'>kvm</font>, sauf mention de <font name='CodeFont'>sudo</font>) "
    "et ses vérifications. Les scripts d'automatisation du dépôt sont appliqués après "
    "installation manuelle du système d'exploitation de chaque VM.",
    styles['body']
))

story.append(add_heading("1.1. Pré-requis matériels", styles, 1))
story.append(Paragraph(
    "L'infrastructure fait tourner jusqu'à 7 VMs simultanément. Les ressources "
    "matérielles de l'hôte doivent couvrir la somme des allocations, la marge de "
    "l'hyperviseur et l'OS hôte lui-même.",
    styles['body']
))
prereq_data = [
    ["Ressource", "Minimum", "Justification"],
    ["RAM", "32 Go", "Somme des VMs (21 Go) + OS hôte (5 Go) + marge"],
    ["CPU", "8 cœurs, VT-x/AMD-V", "4 vCPU Wazuh + 2 OPNsense + autres ; virtualisation matérielle obligatoire"],
    ["Disque", "250 Go", "ISOs (~20 Go) + disques VMs (~200 Go) + snapshots"],
    ["Réseau", "1 carte Ethernet", "Accès WAN pour téléchargements / mise à jour"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 1 — Pré-requis matériels de l'hôte</b>", styles['caption']))
story.append(make_table(prereq_data, col_ratios=[0.16, 0.26, 0.58]))

story.append(add_heading("1.2. Système d'exploitation hôte", styles, 1))
story.append(Paragraph(
    "L'hôte est un <b>Linux Mint 22 (Wilma)</b>, basé sur Ubuntu 24.04 LTS. Ce choix "
    "garantit un accès direct aux paquets Debian/Ubuntu de KVM/QEMU et libvirt, une "
    "longue durée de support et un environnement de bureau familier pour lancer "
    "<font name='CodeFont'>virt-manager</font>. Toutes les commandes de ce guide sont "
    "valables sur toute distribution Debian/Ubuntu récente.",
    styles['body']
))
story.append(Paragraph(
    "Vérifier la version de l'hôte avant toute chose :",
    styles['body']
))
story.append(code_para("lsb_release -a\n# Description: Linux Mint 22 Wilma / Ubuntu 24.04 base"))

# ============================================================
# 2. VÉRIFICATION DU SUPPORT KVM
# ============================================================
story.append(add_heading("2. Vérification du support KVM", styles, 0))
story.append(Paragraph(
    "KVM nécessite l'<b>extension de virtualisation matérielle</b> du processeur : "
    "Intel VT-x (flag <font name='CodeFont'>vmx</font>) ou AMD-V (flag "
    "<font name='CodeFont'>svm</font>). Sans elle, QEMU bascule en émulation logicielle "
    "et les VMs sont inutilisables. Cette vérification est le préalable non négociable.",
    styles['body']
))

story.append(add_heading("2.1. Flags CPU vmx/svm", styles, 1))
story.append(Paragraph(
    "On cherche la présence d'un des deux flags dans <font name='CodeFont'>/proc/cpuinfo</font>. "
    "L'awk ci-dessous renvoie un verdict explicite :",
    styles['body']
))
story.append(code_para(
    "awk '/vmx|svm/{found=1} END{print found?\"vmx/svm detecte OK\":\"NON detecte X\"}' /proc/cpuinfo"
))

story.append(add_heading("2.2. Périphérique /dev/kvm", styles, 1))
story.append(Paragraph(
    "Si le module noyau <font name='CodeFont'>kvm</font> (et <font name='CodeFont'>kvm_intel</font> "
    "ou <font name='CodeFont'>kvm_amd</font>) est chargé, le périphérique caractère "
    "<font name='CodeFont'>/dev/kvm</font> existe :",
    styles['body']
))
story.append(code_para("ls -la /dev/kvm\n# crw-rw----+ 1 root kvm ... /dev/kvm"))

story.append(add_heading("2.3. Récapitulatif matériel", styles, 1))
story.append(Paragraph(
    "Une vue d'ensemble de l'architecture CPU, du modèle et de la mémoire disponible "
    "permet de valider que l'hôte est dimensionné :",
    styles['body']
))
story.append(code_para(
    "lscpu | awk '/^Architecture|^CPU\\(|^Model name|^Vendor/{print}'\n"
    "free -h"
))
story.append(Paragraph(
    "Sortie attendue (exemple) : Architecture x86_64, Vendor ID GenuineIntel, 8 cœurs, "
    "Mem total ~32 Gi. Si <font name='CodeFont'>vmx/svm</font> n'est pas détecté alors "
    "que le CPU le supporte, il faut activer la virtualisation dans le BIOS/UEFI "
    "(option « Intel VT-x » ou « SVM Mode »).",
    styles['body']
))

# ============================================================
# 3. INSTALLATION DE KVM/QEMU
# ============================================================
story.append(add_heading("3. Installation de KVM/QEMU", styles, 0))
story.append(Paragraph(
    "La pile logicielle se compose de l'hyperviseur <b>QEMU/KVM</b>, de l'API de "
    "gestion <b>libvirt</b>, des clients en ligne de commande et graphique, et "
    "d'utilitaires de découverte d'OS. L'installation se fait en une seule commande "
    "depuis les dépôts officiels de Linux Mint/Ubuntu.",
    styles['body']
))
story.append(code_para(
    "sudo apt update && \\\n"
    "sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients \\\n"
    "    bridge-utils virt-manager virtinst libosinfo-bin"
))

story.append(add_heading("3.1. Rôle de chaque paquet", styles, 1))
story.append(Paragraph(
    "Chaque paquet a un rôle précis dans la chaîne de virtualisation. Comprendre "
    "ces rôles facilite le dépannage ultérieur.",
    styles['body']
))
packages_data = [
    ["Paquet", "Rôle"],
    ["qemu-kvm", "Hyperviseur utilisateur : émulation des périphériques + accès à /dev/kvm pour l'accélération matérielle"],
    ["libvirt-daemon-system", "Service libvirtd : API de gestion des VMs, réseaux et pools de stockage"],
    ["libvirt-clients", "Clients CLI virsh / virt-xml pour piloter libvirtd"],
    ["bridge-utils", "Outil brctl : création de ponts réseau (bridges) pour le mode ponté"],
    ["virt-manager", "Interface graphique GTK pour créer et gérer les VMs (utile pour l'installation interactive)"],
    ["virtinst", "Commande virt-install : création de VMs en ligne de commande (scriptable)"],
    ["libosinfo-bin", "Base osinfo-db : détection automatique de l'OS pour optimiser le type de VM (os-variant)"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 2 — Paquets installés et leur rôle</b>", styles['caption']))
story.append(make_table(packages_data, col_ratios=[0.26, 0.74]))

# ============================================================
# 4. CONFIGURATION POST-INSTALLATION
# ============================================================
story.append(add_heading("4. Configuration post-installation", styles, 0))
story.append(Paragraph(
    "Une fois les paquets installés, trois actions restent obligatoires : activer le "
    "service <font name='CodeFont'>libvirtd</font>, accorder à l'utilisateur les "
    "droits d'accès à la virtualisation, et créer le pool de stockage par défaut qui "
    "contiendra les disques des VMs.",
    styles['body']
))

story.append(add_heading("4.1. Activation du service libvirtd", styles, 1))
story.append(Paragraph(
    "Le service doit démarrer maintenant et à chaque boot :",
    styles['body']
))
story.append(code_para("sudo systemctl enable --now libvirtd"))
story.append(Paragraph(
    "Vérifier l'état (<font name='CodeFont'>active (running)</font>) :",
    styles['body']
))
story.append(code_para("systemctl is-active libvirtd"))

story.append(add_heading("4.2. Groupes libvirt et kvm", styles, 1))
story.append(Paragraph(
    "Par défaut, seul root peut piloter libvirt. On ajoute l'utilisateur courant aux "
    "groupes <font name='CodeFont'>libvirt</font> (gestion des VMs) et "
    "<font name='CodeFont'>kvm</font> (accès à /dev/kvm), puis on recharge les "
    "groupes de la session courante :",
    styles['body']
))
story.append(code_para(
    "sudo usermod -aG libvirt,kvm $USER\n"
    "newgrp libvirt"
))
story.append(Paragraph(
    "Après <font name='CodeFont'>newgrp</font>, les commandes "
    "<font name='CodeFont'>virsh</font> s'exécutent sans <font name='CodeFont'>sudo</font>. "
    "Pour une prise d'effet complète (toutes les sessions), une déconnexion/reconnexion "
    "de l'utilisateur est plus sûre.",
    styles['body']
))

story.append(add_heading("4.3. Création du pool de stockage par défaut", styles, 1))
story.append(Paragraph(
    "Le pool <font name='CodeFont'>default</font> est un répertoire, "
    "<font name='CodeFont'>/var/lib/libvirt/images</font>, qui accueillera les "
    "fichiers <font name='CodeFont'>.qcow2</font> des disques VMs. On le crée, on en "
    "définit le propriétaire (l'utilisateur système <font name='CodeFont'>libvirt-qemu</font>), "
    "puis on le déclare, le construit, le démarre et l'active au boot :",
    styles['body']
))
story.append(code_para(
    "sudo mkdir -p /var/lib/libvirt/images && \\\n"
    "sudo chown libvirt-qemu:kvm /var/lib/libvirt/images && \\\n"
    "virsh pool-define-as default --type dir --target /var/lib/libvirt/images && \\\n"
    "virsh pool-build default && \\\n"
    "virsh pool-start default && \\\n"
    "virsh pool-autostart default"
))

story.append(add_heading("4.4. Vérifications", styles, 1))
story.append(Paragraph(
    "Trois vérifications confirment que l'environnement est opérationnel : le réseau "
    "NAT par défaut existe, le pool de stockage est actif et ses informations sont "
    "cohérentes.",
    styles['body']
))
story.append(code_para(
    "virsh net-list --all\n"
    "virsh pool-list --all\n"
    "virsh pool-info default"
))
story.append(Paragraph(
    "Le réseau <font name='CodeFont'>default</font> (virbr0, 192.168.122.0/24, mode "
    "NAT) sert de <b>WAN</b> pour OPNsense : il donne accès à Internet via l'hôte. "
    "Il doit apparaître comme <font name='CodeFont'>active</font> et "
    "<font name='CodeFont'>autostart</font> ; si ce n'est pas le cas : "
    "<font name='CodeFont'>virsh net-start default " + AMP + AMP + " virsh net-autostart default</font>.",
    styles['body']
))

# ============================================================
# 5. PLAN D'ALLOCATION DES RESSOURCES
# ============================================================
story.append(add_heading("5. Plan d'allocation des ressources", styles, 0))
story.append(Paragraph(
    "Le dimensionnement reflète le rôle de chaque VM. Les VMs « cœur » (OPNsense, "
    "Wazuh, Bastion, Ubuntu Server) tournent en permanence ; les VMs Windows et "
    "Kali ne sont démarrées qu'à la demande, ce qui permet de dépasser la RAM "
    "physique si toutes ne sont pas allumées simultanément. Chaque VM est rattachée "
    "à un (ou plusieurs) VLAN(s) via son interface réseau.",
    styles['body']
))
alloc_data = [
    ["VM", "RAM", "vCPU", "Disque", "Priorité", "VLAN"],
    ["OPNsense", "2 Go", "2", "20 Go", "Cœur", "tous (WAN+10/20/30/99)"],
    ["Wazuh", "8 Go", "4", "50 Go", "Cœur", "99"],
    ["Bastion NixOS", "1 Go", "1", "10 Go", "Cœur", "99"],
    ["Ubuntu Server", "2 Go", "2", "20 Go", "Cœur", "30"],
    ["Windows Server", "4 Go", "2", "40 Go", "À la demande", "30"],
    ["Windows 10", "2,5 Go", "2", "40 Go", "À la demande", "10"],
    ["Kali", "1,5 Go", "2", "20 Go", "À la demande", "10"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 3 — Plan d'allocation des ressources (7 VMs)</b>", styles['caption']))
story.append(make_table(alloc_data, col_ratios=[0.18, 0.10, 0.08, 0.10, 0.18, 0.36]))

story.append(Paragraph(
    "<b>Bilan mémoire.</b> Somme des RAM VMs = 21 Go. En comptant l'OS hôte (~5 Go) "
    "et la marge de libvirt/QEMU, on consomme environ <b>26 Go sur 32 Go</b> lorsque "
    "toutes les VMs « cœur » tournent. Les VMs à la demande (Windows Server, "
    "Windows 10, Kali) ne sont démarrées qu'une à la fois lors des démonstrations, "
    "ce qui évite la sur-allocation.",
    styles['callout']
))

# ============================================================
# 6. CRÉATION DES RÉSEAUX ISOLÉS (VLANs)
# ============================================================
story.append(add_heading("6. Création des réseaux isolés (VLANs)", styles, 0))
story.append(Paragraph(
    "Le zoning ANSSI est implémenté par <b>quatre réseaux libvirt isolés</b>, un par "
    "VLAN. En mode <font name='CodeFont'>isolated</font>, le réseau n'a <b>ni NAT ni "
    "passerelle par défaut vers l'extérieur</b> : les VMs ne peuvent communiquer qu'entre "
    "elles sur ce segment. Le DHCP n'est pas géré par libvirt — c'est <b>OPNsense qui "
    "distribue les baux</b> sur chaque VLAN via ses interfaces LAN/OPT. Chaque réseau "
    "porte l'adresse de sous-réseau correspondante, avec OPNsense en .1.",
    styles['body']
))

story.append(add_heading("6.1. Les quatre réseaux à créer", styles, 1))
vlans_data = [
    ["Réseau libvirt", "VLAN", "Plage d'adresses", "Rôle de la zone"],
    ["vlan10", "10", "10.10.10.0/24", "Bureautique (postes, vecteur d'attaque)"],
    ["vlan20", "20", "10.10.20.0/24", "DMZ (services exposés, proxy/VPN)"],
    ["vlan30", "30", "10.10.30.0/24", "Critique (serveurs métier, BDD, AD)"],
    ["vlan99", "99", "10.10.99.0/24", "Admin/SIEM (Wazuh, bastion)"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 4 — Réseaux isolés libvirt (un par VLAN)</b>", styles['caption']))
story.append(make_table(vlans_data, col_ratios=[0.18, 0.08, 0.22, 0.52]))

story.append(add_heading("6.2. Format XML d'un réseau isolé", styles, 1))
story.append(Paragraph(
    "Chaque réseau est décrit dans un fichier XML. Ci-dessous le modèle pour "
    "<font name='CodeFont'>vlan10.xml</font> — les trois autres s'en déduisent en "
    "adaptant le nom, l'UUID (optionnel) et la plage d'adresses :",
    styles['body']
))
story.append(code_para(
    "<network>\n"
    "  <name>vlan10</name>\n"
    "  <!-- mode isolated : pas de forward, donc ni NAT ni route externe -->\n"
    "  <bridge name='virbr10' stp='off' delay='0'/>\n"
    "  <domain name='vlan10'/>\n"
    "  <!-- Pas de <ip> ni de <dhcp> : OPNsense gere le DHCP sur ce segment -->\n"
    "</network>"
))
story.append(Paragraph(
    "Explication des éléments : <font name='CodeFont'>" + LT + "name" + GT + "</font> "
    "identifie le réseau côté libvirt ; l'<b>absence de balise "
    "<font name='CodeFont'>" + LT + "forward" + GT + "</font></b> est ce qui active le "
    "mode isolé (aucune sortie vers l'hôte ou Internet) ; "
    "<font name='CodeFont'>" + LT + "bridge" + GT + "</font> crée le pont Linux "
    "<font name='CodeFont'>virbr10</font> ; on omet volontairement "
    "<font name='CodeFont'>" + LT + "ip" + GT + "</font> et "
    "<font name='CodeFont'>" + LT + "dhcp" + GT + "</font> pour laisser OPNsense gérer "
    "l'adressage et la distribution des baux.",
    styles['body']
))

story.append(add_heading("6.3. Définition et démarrage", styles, 1))
story.append(Paragraph(
    "Pour chaque réseau (répéter pour vlan10, vlan20, vlan30, vlan99) :",
    styles['body']
))
story.append(code_para(
    "virsh net-define vlan10.xml\n"
    "virsh net-start vlan10\n"
    "virsh net-autostart vlan10"
))
story.append(Paragraph(
    "Vérification finale — les 5 réseaux (default + 4 VLANs) doivent être actifs :",
    styles['body']
))
story.append(code_para(
    "virsh net-list --all\n"
    "#  Name      State    Autostart  Persistent\n"
    "#  default   active   yes        yes\n"
    "#  vlan10    active   yes        yes\n"
    "#  vlan20    active   yes        yes\n"
    "#  vlan30    active   yes        yes\n"
    "#  vlan99    active   yes        yes"
))

# ============================================================
# 7. TÉLÉCHARGEMENT DES ISO
# ============================================================
story.append(add_heading("7. Téléchargement des ISO", styles, 0))
story.append(Paragraph(
    "Chaque VM s'installe depuis une image ISO. On les regroupe dans un sous-répertoire "
    "<font name='CodeFont'>/var/lib/libvirt/images/iso/</font> du pool de stockage, "
    "afin que virt-manager et virt-install les trouvent au même endroit.",
    styles['body']
))
iso_data = [
    ["VM", "OS", "Source de téléchargement", "Taille"],
    ["OPNsense", "OPNsense (amd64 DVD)", "https://opnsense.org/download/", "~1,2 Go"],
    ["Wazuh / Ubuntu", "Ubuntu Server 22.04 LTS", "https://releases.ubuntu.com/22.04/", "~2,0 Go"],
    ["Bastion", "NixOS (minimal ISO)", "https://nixos.org/download/", "~0,8 Go"],
    ["Windows Server", "Windows Server 2022 (éval.)", "Portail d'évaluation Microsoft", "~5,0 Go"],
    ["Windows 10", "Windows 10 (ISO)", "Outil de création Microsoft", "~5,0 Go"],
    ["Kali", "Kali Linux (installer)", "https://www.kali.org/get-kali/", "~4,0 Go"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 5 — Images ISO requises</b>", styles['caption']))
story.append(make_table(iso_data, col_ratios=[0.16, 0.26, 0.40, 0.18]))

story.append(add_heading("7.1. Stockage des ISO", styles, 1))
story.append(Paragraph(
    "Créer le répertoire dédié, puis y télécharger (ou y copier) les ISO :",
    styles['body']
))
story.append(code_para(
    "sudo mkdir -p /var/lib/libvirt/images/iso\n"
    "sudo chown libvirt-qemu:kvm /var/lib/libvirt/images/iso\n"
    "cd /var/lib/libvirt/images/iso\n"
    "# Exemple : ISO Ubuntu Server 22.04\n"
    "sudo wget https://releases.ubuntu.com/22.04/ubuntu-22.04.X-live-server-amd64.iso\n"
    "# Renommer pour gagner en lisibilite :\n"
    "# opnsense-dvd.iso, ubuntu-22.04.iso, nixos.iso, win2022.iso, win10.iso, kali.iso"
))
story.append(Paragraph(
    "Conserver les noms courts indiqués en commentaire simplifie les commandes "
    "<font name='CodeFont'>virt-install</font> des sections suivantes.",
    styles['body']
))

# ============================================================
# 8. CRÉATION DE LA VM OPNSENSE
# ============================================================
story.append(add_heading("8. Création de la VM OPNsense", styles, 0))
story.append(Paragraph(
    "OPNsense est le <b>pare-feu/routeur</b> central : il possède 5 interfaces réseau, "
    "une par segment (WAN + 4 VLANs). C'est la première VM à créer, car toutes les "
    "autres dépendent de son routage et de son DHCP.",
    styles['body']
))

story.append(add_heading("8.1. Commande virt-install", styles, 1))
story.append(Paragraph(
    "On crée la VM avec <font name='CodeFont'>virt-install</font>, en lui attachant "
    "les 5 réseaux dans l'ordre WAN puis VLANs. Le disque est en qcow2 ; l'ISO OPNsense "
    "est montée comme CD-ROM pour l'installation.",
    styles['body']
))
story.append(code_para(
    "virt-install \\\n"
    "  --name opnsense \\\n"
    "  --memory 2048 --vcpus 2 \\\n"
    "  --disk path=/var/lib/libvirt/images/opnsense.qcow2,size=20,bus=virtio \\\n"
    "  --cdrom /var/lib/libvirt/images/iso/opnsense-dvd.iso \\\n"
    "  --network network=default      \\\n"
    "  --network network=vlan10       \\\n"
    "  --network network=vlan20       \\\n"
    "  --network network=vlan30       \\\n"
    "  --network network=vlan99       \\\n"
    "  --os-variant freebsd13.0 \\\n"
    "  --graphics spice \\\n"
    "  --noautocons"
))

story.append(add_heading("8.2. Paramètres clés", styles, 1))
params_data = [
    ["Paramètre", "Valeur", "Rôle"],
    ["--name", "opnsense", "Identifiant libvirt de la VM"],
    ["--memory", "2048", "2 Go de RAM (pare-feu peu gourmand)"],
    ["--vcpus", "2", "2 cœurs virtuels pour le filtrage et l'IDS"],
    ["--disk", "opnsense.qcow2, 20 Go, virtio", "Disque principal en qcow2, bus virtio (performances)"],
    ["--cdrom", "opnsense-dvd.iso", "ISO d'installation démarrée au premier boot"],
    ["--network (x5)", "default, vlan10-30, vlan99", "WAN (NAT) + une interface par VLAN isolé"],
    ["--os-variant", "freebsd13.0", "Optimise le type de machine (OPNsense est basé sur FreeBSD)"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 6 — Paramètres de virt-install pour OPNsense</b>", styles['caption']))
story.append(make_table(params_data, col_ratios=[0.22, 0.30, 0.48]))

story.append(add_heading("8.3. Configuration post-installation", styles, 1))
story.append(Paragraph(
    "Au premier démarrage, OPNsense attribue ses interfaces à la console. L'ordre "
    "des <font name='CodeFont'>--network</font> ci-dessus correspond à l'ordre "
    "d'énumération vu par FreeBSD. On assigne :",
    styles['body']
))
iface_data = [
    ["Interface OPNsense", "Réseau libvirt", "Rôle", "Adresse"],
    ["WAN", "default (virbr0)", "Accès Internet via NAT hôte", "DHCP (192.168.122.x)"],
    ["LAN", "vlan10", "Bureautique + passerelle du VLAN 10", "10.10.10.1/24"],
    ["OPT1", "vlan20", "DMZ", "10.10.20.1/24"],
    ["OPT2", "vlan30", "Zone critique", "10.10.30.1/24"],
    ["OPT3", "vlan99", "Admin/SIEM", "10.10.99.1/24"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 7 — Affectation des interfaces OPNsense</b>", styles['caption']))
story.append(make_table(iface_data, col_ratios=[0.18, 0.22, 0.36, 0.24]))
story.append(Paragraph(
    "On active ensuite le DHCP sur chaque interface LAN/OPT (Services " + GT + " DHCPv4), "
    "puis on applique les scripts du dépôt qui automatisent la suite : création des "
    "règles de pare-feu, du NAT, et de l'export syslog vers Wazuh.",
    styles['body']
))
story.append(code_para(
    "# Depuis l'hote, pousser puis appliquer les scripts OPNsense du depot\n"
    "cd ~/defend-the-core/opnsense/scripts\n"
    "# 00-initial-setup.sh   -> configuration de base (mot de passe, DNS)\n"
    "# 01-vlan-interfaces.sh -> declenchement des interfaces VLAN\n"
    "# 02-firewall-rules.sh  -> regles default-deny inter-VLAN\n"
    "# 03-nat-gateway.sh     -> NAT sortant et port-forwarding"
))

# ============================================================
# 9. CRÉATION DE LA VM WAZUH
# ============================================================
story.append(add_heading("9. Création de la VM Wazuh", styles, 0))
story.append(Paragraph(
    "Wazuh est le <b>SIEM/XDR</b> du VLAN 99. C'est la VM la plus gourmande (8 Go, "
    "4 vCPU) car elle héberge le Manager, l'Indexer OpenSearch et le Dashboard. On "
    "l'installe sur Ubuntu Server 22.04, puis on applique le script d'installation "
    "du dépôt qui déploie les trois composants en une passe.",
    styles['body']
))

story.append(add_heading("9.1. Commande virt-install", styles, 1))
story.append(code_para(
    "virt-install \\\n"
    "  --name wazuh \\\n"
    "  --memory 8192 --vcpus 4 \\\n"
    "  --disk path=/var/lib/libvirt/images/wazuh.qcow2,size=50,bus=virtio \\\n"
    "  --cdrom /var/lib/libvirt/images/iso/ubuntu-22.04.iso \\\n"
    "  --network network=vlan99 \\\n"
    "  --os-variant ubuntu22.04 \\\n"
    "  --graphics spice"
))
story.append(Paragraph(
    "Une seule interface sur <font name='CodeFont'>vlan99</font> : Wazuh est en zone "
    "admin, il n'a pas vocation à être exposé. On lui attribue une IP fixe "
    "(10.10.99.10) pendant l'installation Ubuntu.",
    styles['body']
))

story.append(add_heading("9.2. Installation Ubuntu de base", styles, 1))
story.append(Paragraph(
    "Installation minimale Ubuntu Server 22.04 : créer un utilisateur "
    "<font name='CodeFont'>wazuh</font>, configurer l'adresse statique "
    "<b>10.10.99.10/24</b>, passerelle <b>10.10.99.1</b> (OPNsense) et SSH activé. "
    "Aucun paquet supplémentaire n'est sélectionné (pas de snap Docker, etc.) — le "
    "script du dépôt se charge de tout.",
    styles['body']
))

story.append(add_heading("9.3. Application du script d'installation", styles, 1))
story.append(Paragraph(
    "Une fois Ubuntu installé et la VM redémarrée, on pousse le script du dépôt et "
    "on l'exécute. Il ajoute le dépôt APT officiel Wazuh, installe Manager/Indexer/"
    "Dashboard et génère les mots de passe.",
    styles['body']
))
story.append(code_para(
    "# Sur la VM Wazuh, apres transfert du depot\n"
    "cd ~/defend-the-core/wazuh/install\n"
    "sudo bash install-wazuh-manager.sh\n"
    "\n"
    "# Verification : les 3 services doivent etre 'active (running)'\n"
    "systemctl status wazuh-manager wazuh-indexer wazuh-dashboard"
))
story.append(Paragraph(
    "Le dashboard est ensuite accessible (depuis le bastion ou via un tunnel SSH) "
    "sur <font name='CodeFont'>https://10.10.99.10</font>. La configuration de "
    "l'écoute syslog pour OPNsense et le déploiement des agents sont détaillés dans "
    "le document Annexe 2 (Sécurité " + AMP + " Wazuh).",
    styles['body']
))

# ============================================================
# 10. CRÉATION DU BASTION NIXOS
# ============================================================
story.append(add_heading("10. Création du Bastion NixOS", styles, 0))
story.append(Paragraph(
    "Le bastion est le <b>Privileged Access Workstation (PAW)</b> du VLAN 99. Léger "
    "(1 Go, 1 vCPU), il tire sa force de l'<b>immuabilité déclarative</b> de NixOS : "
    "toute la configuration système vit dans <font name='CodeFont'>configuration.nix</font>, "
    "et toute modification manuelle est écrasée au prochain "
    "<font name='CodeFont'>nixos-rebuild switch</font>.",
    styles['body']
))

story.append(add_heading("10.1. Commande virt-install", styles, 1))
story.append(code_para(
    "virt-install \\\n"
    "  --name bastion \\\n"
    "  --memory 1024 --vcpus 1 \\\n"
    "  --disk path=/var/lib/libvirt/images/bastion.qcow2,size=10,bus=virtio \\\n"
    "  --cdrom /var/lib/libvirt/images/iso/nixos.iso \\\n"
    "  --network network=vlan99 \\\n"
    "  --os-variant nixos-22.05 \\\n"
    "  --graphics spice"
))

story.append(add_heading("10.2. Installation de NixOS", styles, 1))
story.append(Paragraph(
    "Démarrer sur l'ISO, puis lancer l'installation depuis la console live. On "
    "partionne le disque, on génère la configuration initiale, puis on la remplace "
    "par celle du dépôt avant le rebuild.",
    styles['body']
))
story.append(code_para(
    "# Console live NixOS\n"
    "sudo su -\n"
    "parted /dev/vda -- mklabel gpt\n"
    "parted /dev/vda -- mkpart primary 1MiB -8GiB\n"
    "parted /dev/vda -- mkpart primary linux-swap -8GiB 100%\n"
    "mkfs.ext4 -L nixos /dev/vda1\n"
    "mount /dev/disk/by-label/nixos /mnt\n"
    "nixos-generate-config --root /mnt"
))

story.append(add_heading("10.3. Configuration déclarative du dépôt", styles, 1))
story.append(Paragraph(
    "Le dépôt fournit deux fichiers : <font name='CodeFont'>configuration.nix</font> "
    "(configuration système : sshd en clés uniquement, ProxyJump, pare-feu, "
    "durcissement) et <font name='CodeFont'>hardware-configuration.nix</font> "
    "(modules matériels et points de montage). On les copie en écrasant la "
    "configuration générée, puis on reconstruit le système :",
    styles['body']
))
story.append(code_para(
    "# Copie des fichiers de configuration du depot\n"
    "cp ~/defend-the-core/bastion-nixos/configuration.nix /mnt/etc/nixos/\n"
    "cp ~/defend-the-core/bastion-nixos/hardware-configuration.nix /mnt/etc/nixos/\n"
    "\n"
    "# Reconstruction et activation (le systeme devient immuable)\n"
    "nixos-install\n"
    "reboot\n"
    "\n"
    "# Apres redemarrage, toute modification ulterieure se fait par :\n"
    "sudo nixos-rebuild switch"
))
story.append(Paragraph(
    "À partir de là, le bastion (10.10.99.20) est le <b>seul</b> hôte autorisé par "
    "OPNsense à joindre le port 22 des serveurs du VLAN 30. Toute administration "
    "passe par <font name='CodeFont'>ssh -J</font> (ProxyJump) depuis le bastion.",
    styles['body']
))

# ============================================================
# 11. CRÉATION DES SERVEURS ET POSTES CLIENTS
# ============================================================
story.append(add_heading("11. Création des serveurs et postes clients", styles, 0))
story.append(Paragraph(
    "Les quatre VMs restantes (Ubuntu Server, Windows Server, Windows 10, Kali) sont "
    "créées sur le même modèle : <font name='CodeFont'>virt-install</font> avec une "
    "interface sur le VLAN adapté, installation manuelle de l'OS, puis application "
    "des scripts d'automatisation du dépôt. Le tableau ci-dessous récapitule le "
    "rattachement réseau et le script d'installation de chacune.",
    styles['body']
))
clients_data = [
    ["VM", "OS", "VLAN", "Script(s) d'installation du dépôt"],
    ["Ubuntu Server", "Ubuntu 22.04", "30",
     "ubuntu-server/scripts/00-06 (base, web stack, harden SSH, agent Wazuh, auditd, UFW, CIS)"],
    ["Windows Server", "Windows Server 2022", "30",
     "windows-server/scripts (Install-ADForest, Configure-DNS-DHCP, Harden, Configure-GPO)"],
    ["Windows 10", "Windows 10", "10",
     "windows-client/scripts/Harden-Win10.ps1 (+ Install-WazuhAgent)"],
    ["Kali", "Kali Linux", "10",
     "kali-attacker/scripts/setup-kali.sh (outils + scénarios d'attaque)"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 8 — Serveurs et postes clients</b>", styles['caption']))
story.append(make_table(clients_data, col_ratios=[0.16, 0.18, 0.08, 0.58]))

story.append(add_heading("11.1. Ubuntu Server (VLAN 30)", styles, 1))
story.append(code_para(
    "virt-install \\\n"
    "  --name ubuntu-server \\\n"
    "  --memory 2048 --vcpus 2 \\\n"
    "  --disk path=/var/lib/libvirt/images/ubuntu-server.qcow2,size=20,bus=virtio \\\n"
    "  --cdrom /var/lib/libvirt/images/iso/ubuntu-22.04.iso \\\n"
    "  --network network=vlan30 \\\n"
    "  --os-variant ubuntu22.04 --graphics spice"
))
story.append(Paragraph(
    "Après installation (IP fixe 10.10.30.10), on enchaîne les scripts numérotés du "
    "dépôt : <font name='CodeFont'>00-base-setup.sh</font> à "
    "<font name='CodeFont'>06-cis-hardening.sh</font> configurent la pile Web (Nginx "
    "+ PostgreSQL), durcissent SSH, installent l'agent Wazuh, configurent auditd, "
    "UFW et appliquent le CIS Benchmark.",
    styles['body']
))

story.append(add_heading("11.2. Windows Server (VLAN 30)", styles, 1))
story.append(code_para(
    "virt-install \\\n"
    "  --name win-server \\\n"
    "  --memory 4096 --vcpus 2 \\\n"
    "  --disk path=/var/lib/libvirt/images/win-server.qcow2,size=40,bus=virtio \\\n"
    "  --cdrom /var/lib/libvirt/images/iso/win2022.iso \\\n"
    "  --network network=vlan30 \\\n"
    "  --os-variant win2k22 --graphics spice"
))
story.append(Paragraph(
    "Séquence PowerShell après installation (IP 10.10.30.20) : "
    "<font name='CodeFont'>Install-ADForest.ps1</font> (forêt Active Directory), "
    "<font name='CodeFont'>Configure-DNS-DHCP.ps1</font>, "
    "<font name='CodeFont'>Harden-WindowsServer.ps1</font> (SMBv1 off, Defender, NLA) "
    "puis <font name='CodeFont'>Configure-GPO.ps1</font> (politique de mots de passe, "
    "restrictions logicielles).",
    styles['body']
))

story.append(add_heading("11.3. Windows 10 et Kali (VLAN 10)", styles, 1))
story.append(code_para(
    "virt-install \\\n"
    "  --name win10 \\\n"
    "  --memory 2560 --vcpus 2 \\\n"
    "  --disk path=/var/lib/libvirt/images/win10.qcow2,size=40,bus=virtio \\\n"
    "  --cdrom /var/lib/libvirt/images/iso/win10.iso \\\n"
    "  --network network=vlan10 \\\n"
    "  --os-variant win10 --graphics spice"
))
story.append(Paragraph(
    "Windows 10 (10.10.10.50) reçoit <font name='CodeFont'>Harden-Win10.ps1</font> et "
    "l'agent Wazuh ; il simule le poste employé (vecteur d'attaque). Kali "
    "(10.10.10.100) est provisionné via <font name='CodeFont'>setup-kali.sh</font> "
    "qui installe les outils et les trois scénarios d'attaque (recon nmap, bruteforce "
    "SSH, mouvement latéral) utilisés pour les démonstrations.",
    styles['body']
))

# ============================================================
# 12. VÉRIFICATION ET TESTS
# ============================================================
story.append(add_heading("12. Vérification et tests", styles, 0))
story.append(Paragraph(
    "Une fois les VMs déployées, on valide que le zoning et la détection fonctionnent. "
    "Les tests couvrent la connectivité réseau, le bon fonctionnement du DHCP par "
    "OPNsense, et les trois scénarios de démonstration du projet.",
    styles['body']
))

story.append(add_heading("12.1. Connectivité et DHCP", styles, 1))
story.append(Paragraph(
    "OPNsense distribue les baux sur chaque VLAN. On les consulte depuis l'hôte :",
    styles['body']
))
story.append(code_para(
    "virsh net-dhcp-leases vlan10\n"
    "# Doit afficher les baux distribues par OPNsense (10.10.10.x)"
))
story.append(Paragraph(
    "Diagnostic d'une VM individuelle — son adresse MAC/IP et son état :",
    styles['body']
))
story.append(code_para(
    "virsh list --all\n"
    "virsh domifaddr ubuntu-server"
))

story.append(add_heading("12.2. Tests inter-VLAN (zero trust)", styles, 1))
story.append(Paragraph(
    "Le cœur du contrôle : un poste du VLAN 10 ne doit <b>pas</b> atteindre les VLANs "
    "30/99. Depuis Win10 (10.10.10.50), un ping vers 10.10.30.10 doit échouer — "
    "c'est OPNsense qui droppe le flux (default-deny).",
    styles['body']
))
story.append(code_para(
    "# Depuis Win10 (VLAN 10) : doit ECHOUER (OPNsense bloque)\n"
    "ping 10.10.30.10    # -> Delai d'attente depasse\n"
    "ping 10.10.99.10    # -> idem, zone admin isolee"
))
story.append(Paragraph(
    "L'administration, elle, doit fonctionner via le bastion (ProxyJump) :",
    styles['body']
))
story.append(code_para(
    "# Depuis le bastion (10.10.99.20), SSH vers le serveur (VLAN 30) :\n"
    "ssh -J admin@10.10.99.20 admin@10.10.30.10\n"
    "# Fonctionne : OPNsense autorise le bastion -> VLAN 30:22"
))

story.append(add_heading("12.3. Scénarios de validation", styles, 1))
scenarios_data = [
    ["#", "Scénario", "Action", "Résultat attendu"],
    ["1", "Détection SIEM", "Bruteforce SSH depuis Kali vers Ubuntu Server",
     "Wazuh détecte " + GT + " active response bloque l'IP automatiquement"],
    ["2", "Zero Trust", "Ping Win10 " + GT + " VLAN 30 / VLAN 99",
     "Échec : OPNsense bloque (default-deny), logs de drop visibles"],
    ["3", "PAW NixOS", "SSH direct vs ProxyJump via bastion",
     "Direct impossible ; bastion " + GT + " serveur fonctionne ; immuabilité vérifiée"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 9 — Scénarios de validation</b>", styles['caption']))
story.append(make_table(scenarios_data, col_ratios=[0.05, 0.15, 0.36, 0.44]))

# ============================================================
# 13. COMMANDES UTILES AU QUOTIDIEN
# ============================================================
story.append(add_heading("13. Commandes utiles au quotidien", styles, 0))
story.append(Paragraph(
    "Aide-mémoire des commandes <font name='CodeFont'>virsh</font> et "
    "<font name='CodeFont'>virt-manager</font> les plus utilisées pour piloter "
    "l'infrastructure au quotidien.",
    styles['body']
))
cheat_data = [
    ["Commande", "Description"],
    ["virsh list --all", "Liste toutes les VMs (allumées et éteintes)"],
    ["virsh start " + LT + "vm" + GT, "Démarre une VM éteinte"],
    ["virsh shutdown " + LT + "vm" + GT, "Arrêt propre (signal ACPI) de la VM"],
    ["virsh destroy " + LT + "vm" + GT, "Arrêt forcé (équivalent débrancher) — à éviter"],
    ["virsh reboot " + LT + "vm" + GT, "Redémarrage propre d'une VM"],
    ["virsh console " + LT + "vm" + GT, "Console série (Ctrl+] pour quitter)"],
    ["virsh net-list --all", "Liste tous les réseaux libvirt"],
    ["virsh net-start " + LT + "net" + GT, "Démarre un réseau (ex. vlan10)"],
    ["virsh domifaddr " + LT + "vm" + GT, "Adresses MAC/IP d'une VM"],
    ["virsh net-dhcp-leases " + LT + "net" + GT, "Baux DHCP actifs sur un réseau"],
    ["virsh pool-list --all", "Liste les pools de stockage"],
    ["virsh snapshot-create-as " + LT + "vm" + GT + " nom", "Crée un instantané d'une VM"],
    ["virsh snapshot-list " + LT + "vm" + GT, "Liste les instantanés d'une VM"],
    ["virsh snapshot-revert " + LT + "vm" + GT + " nom", "Restaure une VM sur un instantané"],
    ["virt-manager", "Ouvre l'interface graphique de gestion des VMs"],
    ["virt-viewer " + LT + "vm" + GT, "Ouvre la console graphique d'une VM"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 10 — Cheat sheet virsh / virt-manager</b>", styles['caption']))
story.append(make_table(cheat_data, col_ratios=[0.40, 0.60]))
story.append(Paragraph(
    "Astuce : avant toute manipulation risquée (mise à jour, test d'attaque), créer "
    "un instantané avec <font name='CodeFont'>virsh snapshot-create-as</font> permet "
    "de revenir en arrière instantanément.",
    styles['callout']
))

# ============================================================
# 14. DÉPANNAGE
# ============================================================
story.append(add_heading("14. Dépannage", styles, 0))
story.append(Paragraph(
    "Tableau récapitulatif des problèmes les plus fréquents rencontrés pendant "
    "l'installation, leur cause probable et la résolution.",
    styles['body']
))
trouble_data = [
    ["Problème", "Cause probable", "Solution"],
    ["La VM ne démarre pas",
     "Disque manquant ou chemin ISO incorrect",
     "Vérifier virsh pool-info default ; chemin .qcow2 et .iso absolus dans virt-install"],
    ["« permission denied » sur /dev/kvm",
     "Utilisateur hors du groupe kvm",
     "sudo usermod -aG kvm $USER ; newgrp kvm (ou déconnexion/reconnexion)"],
    ["virsh : « impossible de se connecter à qemu »",
     "libvirtd inactif ou ACL libvirt manquante",
     "sudo systemctl enable --now libvirtd ; ajouter l'utilisateur au groupe libvirt"],
    ["Pas d'accès réseau dans une VM",
     "Réseau libvirt non démarré ou VM sur le mauvais réseau",
     "virsh net-list --all ; virsh net-start vlan10 ; vérifier --network dans virt-install"],
    ["Pas de bail DHCP sur un VLAN",
     "DHCP libvirt désactivé (isolated) " + AMP + " OPNsense non configuré",
     "Normal : OPNsense gère le DHCP. Configurer Services " + GT + " DHCPv4 sur l'interface OPNsense"],
    ["Ping inter-VLAN réussit alors qu'il devrait échouer",
     "Règle default-deny absente ou mal ordonnée dans OPNsense",
     "Ajouter une règle block any any en fin de liste sur l'interface ; vérifier l'ordre"],
    ["Wazuh ne reçoit pas les logs OPNsense",
     "Syslog non configuré ou port 514/udp fermé",
     "Configurer ossec.conf (remote syslog 514/udp) " + AMP + " règle d'export OPNsense vers 10.10.99.10"],
    ["L'interface graphique virt-manager est lente",
     "Spice sans accel. 3D sur VM Windows",
     "Activer « Affichage Spice + GL » ou utiliser virt-viewer ; vérifier les drivers virtio"],
    ["La VM Kali est injoignable après installation",
     "IP non fixée ou sur le mauvais VLAN",
     "Assigner 10.10.10.100/24 via NetworkManager ; gw 10.10.10.1 (OPNsense)"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 11 — Problèmes courants et solutions</b>", styles['caption']))
story.append(make_table(trouble_data, col_ratios=[0.26, 0.32, 0.42]))

story.append(Spacer(1, 16))
story.append(Paragraph(
    "<i>Fin du guide d'installation. Les configurations détaillées de chaque composant "
    "(OPNsense, Wazuh, durcissement, bastion NixOS) font l'objet des annexes 1 à 4.</i>",
    styles['body_left']
))

# ============================================================
# BUILD
# ============================================================
doc.multiBuild(story)
print(f"PDF généré : {OUTPUT}")
