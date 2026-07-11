#!/usr/bin/env python3
"""
Générateur PDF : Annexe 4 — Administration sécurisée & Bastion NixOS
Coeur du projet : le bastion PAW (Privileged Access Workstation) sous NixOS.
Couvre : concept PAW, immuabilité NixOS, ProxyJump, configuration.nix détaillée,
FIDO2, checklist de durcissement, argument « Waouh » pour l'entretien.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_common import *
from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable

register_fonts()
styles = get_styles()

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'docs', '04_admin_bastion_nixos.pdf')

doc = build_doc(OUTPUT, "Defend-The-Core — Administration & Bastion NixOS")
story = []

# ============================================================
# PAGE DE TITRE
# ============================================================
story.append(Spacer(1, 70))
story.append(Paragraph("Defend-The-Core", styles['title']))
story.append(HRFlowable(width="40%", thickness=2, color=ACCENT, spaceBefore=6, spaceAfter=12))
story.append(Paragraph("Infrastructure PME critique sécurisée", styles['subtitle']))
story.append(Spacer(1, 20))
story.append(Paragraph(
    "Annexe 4 — Administration sécurisée & Bastion NixOS<br/>"
    "Le Privileged Access Workstation (PAW) : point unique d'administration immuable",
    ParagraphStyle('Desc', fontName='BodyFont', fontSize=11, leading=16,
                   textColor=TEXT_MUTED, alignment=TA_LEFT)
))
story.append(Spacer(1, 40))
story.append(Paragraph(
    "Immuabilité déclarative · ProxyJump · FIDO2 · Défense en profondeur",
    ParagraphStyle('Tags', fontName='HeadFont', fontSize=10, leading=14,
                   textColor=ACCENT, alignment=TA_LEFT)
))
story.append(Spacer(1, 8))
story.append(Paragraph(
    "« La star du projet : si un attaquant modifie /etc/ssh/sshd_config, "
    "NixOS l'écrasera au prochain déploiement. »",
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
# 1. LE CONCEPT DE PAW
# ============================================================
story.append(add_heading("1. Le concept de PAW (Privileged Access Workstation)", styles, 0))
story.append(Paragraph(
    "Un <b>Privileged Access Workstation (PAW)</b>, ou bastion d'administration, est une "
    "machine dédiée et durcie dont l'unique fonction est de servir de <b>point unique "
    "d'administration</b> vers les serveurs critiques. L'administrateur ne se connecte "
    "<i>jamais</i> directement à un serveur de production depuis son poste de travail "
    "ordinaire, fût-il de confiance : tout le trafic d'administration transite par le "
    "bastion, qui se trouve dans une zone réseau isolée (ici le VLAN 99 — Admin/SIEM).",
    styles['body']
))
story.append(Paragraph(
    "La rationale est double. D'abord, le poste de l'administrateur reste une surface "
    "d'attaque (navigateur, messagerie, pièces jointes) : un phishing réussi exposerait "
    "les identifiants SSH si la connexion était directe. Ensuite, centraliser "
    "l'administration sur un hôte unique permet de <b>tracer, durcir et verrouiller</b> "
    "toutes les sessions privilégiées au même endroit.",
    styles['body']
))

story.append(add_heading("1.1. Chaîne d'administration relayée", styles, 1))
story.append(Paragraph(
    "Le flux d'administration respecte une chaîne stricte à trois sauts. Chaque maillon "
    "impose une authentification distincte et un contrôle réseau explicite :",
    styles['body']
))
story.append(Paragraph(
    "<font name='CodeFont' size='9'>"
    "Poste admin (bureautique, VLAN 10)<br/>"
    "   │  (1) SSH + clé FIDO2 (ed25519-sk)<br/>"
    "   ▼<br/>"
    "Bastion NixOS (10.10.99.20, VLAN 99)<br/>"
    "   │  (2) ProxyJump ssh -J (clé ed25519 dédiée)<br/>"
    "   ▼<br/>"
    "Serveurs cibles (10.10.30.0/24, VLAN 30)<br/>"
    "</font>",
    styles['code']
))
story.append(Paragraph(
    "<b>Figure 1 — Chaîne d'administration relayée.</b> Le poste admin n'a aucune "
    "visibilité du VLAN 30 ; seul le bastion (10.10.99.20) peut joindre le port 22 des "
    "serveurs, et uniquement parce qu'OPNsense l'y autorise explicitement.",
    styles['caption']
))
story.append(Paragraph(
    "OPNsense applique une règle <b>default-deny</b> sur le VLAN 30 : la seule exception "
    "autorisant le port 22 a pour source unique le bastion (10.10.99.20). Toute tentative "
    "SSH directe depuis le VLAN 10 — ou depuis un autre hôte du VLAN 99 — est rejetée et "
    "journalisée. L'administration devient <b>impossible hors bastion</b>, contrôle "
    "indépendant d'un mot de passe puisqu'il repose sur la topologie réseau elle-même.",
    styles['body']
))

# ============================================================
# 2. POURQUOI NIXOS ?
# ============================================================
story.append(add_heading("2. Pourquoi NixOS ?", styles, 0))
story.append(Paragraph(
    "Le choix de NixOS comme système d'exploitation du bastion est la décision la plus "
    "structurante du projet. NixOS repose sur deux principes qui le distinguent "
    "radicalement des distributions Linux classiques : la <b>configuration déclarative</b> "
    "et l'<b>immuabilité de l'état système</b>.",
    styles['body']
))
story.append(Paragraph(
    "L'intégralité de la configuration — paquets installés, services activés, options SSH, "
    "règles de pare-feu, paramètres sysctl, utilisateurs — est décrite dans un fichier "
    "unique, <font name='CodeFont'>configuration.nix</font>. Appliquer la configuration "
    "se fait par <font name='CodeFont'>nixos-rebuild switch</font>, qui génère un nouveau "
    "<i>profil</i> système atomique. Les profils précédents restent disponibles, ce qui "
    "autorise un <b>rollback instantané</b> (<font name='CodeFont'>nixos-rebuild "
    "switch --rollback</font>) en cas de régression.",
    styles['body']
))

story.append(add_heading("2.1. L'argument central : l'immuabilité anti-persistance", styles, 1))
story.append(Paragraph(
    "Sur une distribution classique (Ubuntu, Debian), un attaquant qui obtient les "
    "droits root peut éditer <font name='CodeFont'>/etc/ssh/sshd_config</font>, "
    "<font name='CodeFont'>/etc/pam.d/sshd</font> ou déposer un binaire dans "
    "<font name='CodeFont'>/usr/local/bin</font> ; ces modifications <b>persistent</b> "
    "à travers les redémarrages. La backdoor est installée durablement.",
    styles['body']
))
story.append(Paragraph(
    "Sur NixOS, la situation est fondamentalement différente. Les fichiers de "
    "configuration système ne sont pas édités directement : ils sont générés depuis "
    "<font name='CodeFont'>configuration.nix</font> à chaque déploiement et placés dans "
    "le <b>Nix store</b> en lecture seule (<font name='CodeFont'>/nix/store</font>, "
    "monté en <font name='CodeFont'>readOnly</font>). Toute modification manuelle d'un "
    "fichier géré par NixOS est <b>écrasée</b> au prochain "
    "<font name='CodeFont'>nixos-rebuild switch</font>. Le Nix store étant immuable, "
    "il est impossible d'y remplacer un binaire en place.",
    styles['body']
))
story.append(Paragraph(
    "<b>Argument clé.</b> Si un attaquant modifie <font name='CodeFont'>/etc/ssh/sshd_config</font> "
    "pour réactiver l'authentification par mot de passe ou ajouter une clé, NixOS "
    "l'écrasera au prochain déploiement. L'immuabilité empêche la persistance : la "
    "backdoor ne survit pas à un <font name='CodeFont'>nixos-rebuild switch</font>.",
    styles['callout']
))

story.append(add_heading("2.2. Comparaison avec d'autres systèmes", styles, 1))
story.append(Paragraph(
    "Le tableau suivant compare NixOS aux distributions classiques sur les critères qui "
    "comptent pour un bastion d'administration. L'objectif n'est pas de dénigrer Ubuntu "
    "ou Debian — excellents pour les serveurs métier durcis via CIS Benchmark — mais de "
    "mettre en évidence la propriété unique de NixOS : la <b>non-persistance</b> des "
    "modifications non déclarées.",
    styles['body']
))
cmp_data = [
    ["Critère", "NixOS", "Ubuntu", "Debian"],
    ["Immuabilité de la configuration",
     "Totale : config régénérée depuis configuration.nix",
     "Partielle : fichiers éditables manuellement",
     "Partielle : fichiers éditables manuellement"],
    ["Reproductibilité",
     "Exacte : même config → même état",
     "Manuelle : dépend de l'historique apt",
     "Manuelle : dépend de l'historique apt"],
    ["Rollback",
     "Instantané (--rollback), profil atomique",
     "Non natif,重建 à la main",
     "Non natif, reconstruction manuelle"],
    ["Versionning Git",
     "Natif : configuration.nix versionnée",
     "Indirect : ansible/puppet à ajouter",
     "Indirect : outil de config management"],
    ["Persistance d'une backdoor",
     "Impossible : écrasée au rebuild",
     "Possible : modification manuelle persiste",
     "Possible : modification manuelle persiste"],
    ["Surface de déploiement",
     "Un fichier, déclaratif, audité",
     "Scripts + état divergent possible",
     "Scripts + état divergent possible"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 1 — NixOS face aux distributions classiques</b>", styles['caption']))
story.append(make_table(cmp_data, col_ratios=[0.22, 0.30, 0.24, 0.24]))
story.append(Paragraph(
    "Cette propriété d'anti-persistance est ce qui justifie NixOS <i>spécifiquement</i> "
    "pour le bastion, là où Ubuntu et Debian suffisent pour les serveurs métier (VLAN 30) "
    "dont la configuration est durcie mais reste ponctuellement éditable.",
    styles['body']
))

# ============================================================
# 3. PROXYJUMP
# ============================================================
story.append(add_heading("3. ProxyJump (administration relayée)", styles, 0))
story.append(Paragraph(
    "Le <b>jump host</b> est un patron classique d'administration sécurisée : au lieu "
    "d'exposer le SSH des serveurs cibles à un large réseau, on force tout le trafic "
    "à transiter par un hôte intermédiaire verrouillé. OpenSSH formalise ce mécanisme "
    "depuis sa version 7.3 via l'option <b>ProxyJump</b> (<font name='CodeFont'>-J</font>), "
    "qui établit automatiquement le tunnel SSH vers la cible à travers le bastion.",
    styles['body']
))
story.append(Paragraph(
    "Concrètement, l'administrateur tape <font name='CodeFont'>ssh -J bastion serveur</font>. "
    "OpenSSH ouvre d'abord une connexion vers le bastion, puis depuis le bastion une "
    "seconde connexion TCP vers <font name='CodeFont'>serveur</font>:22, et encapsule la "
    "session finale dans ce tunnel. La clé privée du serveur cible ne quitte jamais le "
    "poste admin — elle est utilisée localement au travers du canal relayé.",
    styles['body']
))

story.append(add_heading("3.1. Configuration client (ssh_config)", styles, 1))
story.append(Paragraph(
    "Plutôt que de saisir <font name='CodeFont'>-J</font> à chaque fois, la chaîne est "
    "déclarée dans <font name='CodeFont'>~/.ssh/config</font> du poste admin. Deux hôtes "
    "sont définis : le bastion (authentification FIDO2) et les cibles (relayées via le "
    "bastion, clé ed25519 dédiée).",
    styles['body']
))
story.append(Paragraph(
    "<font name='CodeFont' size='8.5'>"
    "# ~/.ssh/config sur le poste admin<br/>"
    "<br/>"
    "Host bastion<br/>"
    "   HostName 10.10.99.20<br/>"
    "   User admin<br/>"
    "   IdentityFile ~/.ssh/id_ed25519_sk   # clé FIDO2 (matérielle)<br/>"
    "   PasswordAuthentication no<br/>"
    "   PubkeyAuthentication yes<br/>"
    "<br/>"
    "Host srv-*<br/>"
    "   ProxyJump bastion                  # relais obligatoire<br/>"
    "   User deploy<br/>"
    "   IdentityFile ~/.ssh/id_ed25519_srv  # clé dédiée serveurs<br/>"
    "   IdentitiesOnly yes<br/>"
    "   PasswordAuthentication no<br/>"
    "</font>",
    styles['code']
))
story.append(Paragraph(
    "<b>Extrait 1 — ssh_config : chaîne ProxyJump et clés dédiées par usage.</b>",
    styles['caption']
))

story.append(add_heading("3.2. known_hosts et protection anti-MITM", styles, 1))
story.append(Paragraph(
    "Pour empêcher une attaque de type <b>man-in-the-middle</b> sur le premier saut, "
    "l'empreinte de la clé publique du bastion est pré-positionnée dans "
    "<font name='CodeFont'>~/.ssh/known_hosts</font> via le dépôt Git (procédure de "
    "premier déploiement). OpenSSH refuse alors toute connexion si la clé présentée "
    "diffère de l'empreinte attendue. Les empreintes des serveurs du VLAN 30 sont "
    "également vérifiées au second saut, ce qui verrouille les deux maillons de la chaîne.",
    styles['body']
))

story.append(add_heading("3.3. Clés dédiées par usage", styles, 1))
keys_data = [
    ["Usage", "Type de clé", "Facteur", "Justification"],
    ["Accès au bastion", "ed25519-sk", "Matériel (FIDO2)",
     "Anti-clonage : la clé ne sort jamais du token"],
    ["Accès aux serveurs", "ed25519", "Logiciel",
     "Légère, usage relayé, stockée sur le poste admin"],
    ["Root (serveurs)", "Interdit", "—",
     "Pas de PermitRootLogin, sudo journalisé uniquement"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 2 — Clés SSH dédiées par usage</b>", styles['caption']))
story.append(make_table(keys_data, col_ratios=[0.20, 0.16, 0.20, 0.44]))
story.append(Paragraph(
    "L'<b>OPNsense autorise uniquement le bastion</b> (10.10.99.20) à joindre le port 22 "
    "du VLAN 30. Tout autre source est rejetée et journalisée : la topologie rend "
    "l'administration directe impossible, indépendamment des identifiants.",
    styles['body']
))

# ============================================================
# 4. configuration.nix — ANALYSE DÉTAILLÉE
# ============================================================
story.append(add_heading("4. configuration.nix — analyse détaillée", styles, 0))
story.append(Paragraph(
    "Cette section décompose la configuration du bastion, bloc par bloc. Le fichier "
    "complet est versionné dans le dépôt (<font name='CodeFont'>bastion/configuration.nix</font>) ; "
    "les extraits ci-dessous en montrent les parties significatives avec leur rationale "
    "de sécurité. Chaque directive répond à une recommandation précise du guide de "
    "durcissement ANSSI / CIS.",
    styles['body']
))

# --- 4.1 SSH durci ---
story.append(add_heading("4.1. Serveur SSH durci", styles, 1))
story.append(Paragraph(
    "Le serveur SSH du bastion est l'unique point d'entrée d'administration. Il est "
    "verrouillé sur l'essentiel : pas de root, pas de mot de passe, authentification "
    "par clé FIDO2 uniquement, algorithmes cryptographiques modernes et limités.",
    styles['body']
))
story.append(Paragraph(
    "<font name='CodeFont' size='8.5'>"
    "services.openssh = {<br/>"
    "  enable = true;<br/>"
    "  settings = {<br/>"
    "    PermitRootLogin       = \"no\";       # root interdit<br/>"
    "    PasswordAuthentication = false;      # aucune auth. par mot de passe<br/>"
    "    KbdInteractiveAuthentication = false;<br/>"
    "    PubkeyAuthentication  = true;<br/>"
    "    MaxAuthTries          = 3;           # 3 essais, puis échec<br/>"
    "    LoginGraceTime        = 30;          # 30 s pour s'authentifier<br/>"
    "    AllowUsers            = [ \"admin\" ]; # liste blanche<br/>"
    "  };<br/>"
    "  banner = /etc/ssh/banner;                       # avertissement légal<br/>"
    "};<br/>"
    "</font>",
    styles['code']
))
story.append(Paragraph(
    "<b>Extrait 2 — services.openssh : authentification par clé uniquement, root interdit.</b>",
    styles['caption']
))
story.append(Paragraph(
    "La directive <font name='CodeFont'>PermitRootLogin = \"no\"</font> supprime la "
    "possibilité même d'une connexion root directe — l'administrateur se connecte en "
    "compte non privilégié, puis élève via <font name='CodeFont'>sudo</font> (journalisé). "
    "<font name='CodeFont'>PasswordAuthentication = false</font> neutralise entièrement "
    "le bruteforce de mots de passe, et <font name='CodeFont'>MaxAuthTries = 3</font> "
    "limite le nombre de tentatives par session avant déconnexion.",
    styles['body']
))

story.append(Paragraph(
    "<b>Bannière légale.</b> Un fichier <font name='CodeFont'>/etc/ssh/banner</font> "
    "affiche un avertissement : « Accès réservé à l'administration autorisée. Toute "
    "connexion est journalisée et surveillée. » Outre l'effet dissuasif, cette bannière "
    "est requise pour la recevabilité juridique des journaux en cas de poursuite.",
    styles['body']
))

story.append(Paragraph("<b>Algorithmes cryptographiques retenus</b>", styles['h3']))
crypto_data = [
    ["Famille", "Algorithmes autorisés", "Algorithmes écartés", "Raison"],
    ["Clé serveur",
     "rsa-sha2-512, rsa-sha2-256, ssh-ed25519",
     "ssh-rsa (SHA-1), DSA",
     "Faiblesses cryptographiques (SHA-1)"],
    ["Échange de clé",
     "curve25519-sha256, ecdh-sha2-nistp521",
     "diffie-hellman-group1, group14-sha1",
     "DH faibles, obsolètes"],
    ["Chiffrement",
     "chacha20-poly1305, aes256-gcm",
     "3des-cbc, aes128-cbc, arcfour",
     "Modes obsolètes, faibles"],
    ["Intégrité (MAC)",
     "hmac-sha2-512-etm, hmac-sha2-256-etm",
     "hmac-sha1, hmac-md5",
     "Fonctions de hachage cassées"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 3 — Suite cryptographique durcie (KexAlgorithms, Ciphers, MACs)</b>", styles['caption']))
story.append(make_table(crypto_data, col_ratios=[0.16, 0.30, 0.24, 0.30]))
story.append(Paragraph(
    "Restreindre la liste des algorithmes à un jeu moderne et homogène réduit la surface "
    "d'attaque (pas de négociation vers un algorithme faible) et facilite l'audit : un "
    "algorithme nouveau ou inattendu apparaissant dans les logs trahit immédiatement une "
    "anomalie.",
    styles['body']
))

# --- 4.2 Pare-feu local ---
story.append(add_heading("4.2. Pare-feu local (iptables)", styles, 1))
story.append(Paragraph(
    "Outre le filtrage d'OPNsense à l'échelle du réseau, le bastion applique son propre "
    "pare-feu local en <b>default-deny</b>. Cette défense en profondeur signifie que "
    "même une erreur de configuration d'OPNsense ne suffirait pas à exposer le bastion : "
    "seuls les flux explicitement listés ci-dessous sont acceptés.",
    styles['body']
))
story.append(Paragraph(
    "<font name='CodeFont' size='8.5'>"
    "networking.firewall = {<br/>"
    "  enable = true;<br/>"
    "  allowedTCPPorts = [ 22 ];            # SSH entrant<br/>"
    "  interfaces.eth0.allowedTCPPorts = [ 22 ];   # VLAN 99 uniquement<br/>"
    "  extraCommands = ''<br/>"
    "    iptables -A INPUT  -s 10.10.99.0/24 -p tcp --dport 22 -j ACCEPT<br/>"
    "    iptables -A INPUT  -s 10.10.10.0/24 -j DROP   # blocage VLAN 10<br/>"
    "    iptables -A INPUT  -s 10.10.20.0/24 -j DROP   # blocage VLAN 20<br/>"
    "    iptables -A OUTPUT -d 10.10.30.0/24 -p tcp --dport 22 -j ACCEPT<br/>"
    "    iptables -A OUTPUT -j DROP                       # reste refusé<br/>"
    "  '';<br/>"
    "};<br/>"
    "</font>",
    styles['code']
))
story.append(Paragraph(
    "<b>Extrait 3 — Pare-feu local : SSH entrant depuis le VLAN 99 uniquement, SSH "
    "sortant vers le VLAN 30 uniquement, blocage des VLAN 10 et 20.</b>",
    styles['caption']
))
fw_data = [
    ["Sens", "Source", "Destination", "Port", "Action", "Justification"],
    ["Entrant", "VLAN 99", "Bastion", "22", "Allow", "Admin via FIDO2 uniquement"],
    ["Entrant", "VLAN 10/20", "Bastion", "*", "Drop", "Bureautique/DMZ isolées"],
    ["Sortant", "Bastion", "VLAN 30", "22", "Allow", "ProxyJump vers serveurs"],
    ["Sortant", "Bastion", "VLAN 10/20", "*", "Drop", "Pas de retour vers zones moins fiables"],
    ["Sortant", "Bastion", "Wazuh (99.10)", "514", "Allow", "Forward des logs"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 4 — Politique de pare-feu local du bastion</b>", styles['caption']))
story.append(make_table(fw_data, col_ratios=[0.10, 0.14, 0.16, 0.08, 0.10, 0.42]))

# --- 4.3 sysctl durcis ---
story.append(add_heading("4.3. Paramètres noyau (sysctl) durcis", styles, 1))
story.append(Paragraph(
    "Le durcissement noyau complète la posture défensive. Ces paramètres rendent plus "
    "difficiles l'exploitation de vulnérabilités mémoire, l'usurpation réseau et la "
    "reconnaissance interne. Ils sont appliqués via "
    "<font name='CodeFont'>boot.kernel.sysctl</font> et donc, comme toute la "
    "configuration, régénérés à chaque déploiement.",
    styles['body']
))
sysctl_data = [
    ["Paramètre", "Valeur", "Objectif"],
    ["kernel.randomize_va_space", "2",
     "ASLR complet (adressage aléatoire) — complique les exploits mémoire"],
    ["kernel.yama.ptrace_scope", "2",
     "Restreint ptrace au root ; empêche l'inspection d'un process par un autre"],
    ["net.ipv4.conf.all.rp_filter", "1",
     "Anti-spoofing : rejette les paquets à source incohérente avec l'interface"],
    ["net.ipv4.tcp_syncookies", "1",
     "Résistance au SYN flood (épuisement de la table des connexions)"],
    ["net.ipv4.conf.all.log_martians", "1",
     "Journalise les paquets impossibles/illégaux (détection d'attaque)"],
    ["net.ipv4.icmp_echo_ignore_broadcasts", "1",
     "Anti-smurf : ignore les echo broadcasts"],
    ["net.ipv4.ip_forward", "0",
     "Pas de routage : le bastion n'est pas un routeur"],
    ["fs.suid_dumpable", "0",
     "Pas de core dump pour les binaires setuid (fuite d'infos)"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 5 — Paramètres sysctl durcis du bastion</b>", styles['caption']))
story.append(make_table(sysctl_data, col_ratios=[0.32, 0.10, 0.58]))

# --- 4.4 Immuabilité ---
story.append(add_heading("4.4. Immuabilité et anti-persistance", styles, 1))
story.append(Paragraph(
    "L'immuabilité est renforcée au niveau du boot. Le Nix store est monté en lecture "
    "seule et <font name='CodeFont'>/tmp</font> est placé sur un tmpfs (en RAM), ce qui "
    "garantit qu'aucun artefact écrit à chaud ne survive à un redémarrage.",
    styles['body']
))
story.append(Paragraph(
    "<font name='CodeFont' size='8.5'>"
    "boot.readOnlyNixStore = true;        # /nix/store immuable<br/>"
    "boot.tmpOnTmpfs       = true;        # /tmp en RAM, effacé au reboot<br/>"
    "boot.cleanTmpDir      = true;        # nettoyage /tmp au démarrage<br/>"
    "<br/>"
    "# La configuration est versionnée Git : /etc/nixos est un dépôt<br/>"
    "# clone du repository du projet. Tout changement est un commit.<br/>"
    "</font>",
    styles['code']
))
story.append(Paragraph(
    "<b>Extrait 4 — Immuabilité du Nix store et de /tmp.</b>",
    styles['caption']
))
story.append(Paragraph(
    "La combinaison <font name='CodeFont'>readOnlyNixStore</font> + "
    "<font name='CodeFont'>tmpOnTmpfs</font> crée une propriété forte : un attaquant "
    "qui réussirait à déposer un binaire malveillant dans <font name='CodeFont'>/tmp</font> "
    "le verrait disparaître au prochain redémarrage, et ne pourrait pas le recopier dans "
    "le Nix store (lecture seule). La configuration étant versionnée Git, toute "
    "modification légitime passe par un commit auditable et une revue de pull request.",
    styles['body']
))

# --- 4.5 Auditd ---
story.append(add_heading("4.5. Auditd — surveillance de l'intégrité", styles, 1))
story.append(Paragraph(
    "Le sous-système <font name='CodeFont'>auditd</font> journalise tout accès ou "
    "modification des fichiers sensibles, ainsi que l'exécution de commandes "
    "privilégiées. Les événements sont remontés en temps réel vers Wazuh (section 4.8).",
    styles['body']
))
story.append(Paragraph(
    "<font name='CodeFont' size='8.5'>"
    "security.audit.enable = true;<br/>"
    "security.audit.rules = ''<br/>"
    "  -w /etc/nixos/      -p wa  -k nixos_config   # config NixOS<br/>"
    "  -w /etc/sudoers     -p wa  -k sudoers         # privilèges sudo<br/>"
    "  -w /etc/passwd      -p wa  -k identity        # comptes<br/>"
    "  -w /etc/shadow      -p wa  -k identity        # mots de passe<br/>"
    "  -w /var/log/auth.log -p wa -k authlog         # logs d'auth.<br/>"
    "  -a always,exit -F arch=b64 -S execve \\<br/>"
    "    -F path=/usr/bin/sudo -k privileged<br/>"
    "'';<br/>"
    "</font>",
    styles['code']
))
story.append(Paragraph(
    "<b>Extrait 5 — Règles auditd : surveillance des fichiers critiques et de sudo.</b>",
    styles['caption']
))
story.append(Paragraph(
    "Toute écriture (<font name='CodeFont'>-p w</font>) ou modification d'attribut "
    "(<font name='CodeFont'>-p a</font>) sur <font name='CodeFont'>/etc/nixos</font>, "
    "<font name='CodeFont'>/etc/sudoers</font> ou <font name='CodeFont'>/etc/passwd</font> "
    "génère un événement horodaté et taggé. Wazuh corrèle ces événements avec les "
    "connexions SSH pour détecter, par exemple, une modification de configuration juste "
    "après une connexion inhabituelle.",
    styles['body']
))

# --- 4.6 fail2ban ---
story.append(add_heading("4.6. fail2ban — protection anti-bruteforce", styles, 1))
story.append(Paragraph(
    "Bien que l'authentification par mot de passe soit désactivée, <font name='CodeFont'>"
    "fail2ban</font> reste pertinent : il détecte les tentatives répétées d'authentification "
    "échouée (clés refusées, erreurs de protocole) et bannit l'IP source. La stratégie "
    "est un <b>ban incrémental</b> d'une heure après 3 échecs.",
    styles['body']
))
story.append(Paragraph(
    "<font name='CodeFont' size='8.5'>"
    "services.fail2ban = {<br/>"
    "  enable = true;<br/>"
    "  jails.sshd = ''<br/>"
    "    enabled  = true<br/>"
    "    maxretry = 3                  # 3 essais avant ban<br/>"
    "    findtime = 10m               # fenêtre de 10 min<br/>"
    "    bantime  = 1h                # ban 1 heure<br/>"
    "    bantime.increment = true    # ban plus long aux récidives<br/>"
    "  '';<br/>"
    "};<br/>"
    "</font>",
    styles['code']
))
story.append(Paragraph(
    "<b>Extrait 6 — fail2ban : 3 essais, ban d'une heure, incrémental.</b>",
    styles['caption']
))

# --- 4.7 Services minimaux ---
story.append(add_heading("4.7. Empreinte minimale des services", styles, 1))
story.append(Paragraph(
    "Un bastion ne fait qu'une chose : relayer l'administration. Aucun service inutile "
    "n'est exposé. Pas d'environnement graphique, pas de serveur Web, pas d'imprimante, "
    "pas de Samba. La liste des paquets est réduite au strict nécessaire et declarée "
    "explicitement. La synchronisation temporelle (NTP) est maintenue pour permettre la "
    "corrélation temporelle des événements dans le SIEM.",
    styles['body']
))
story.append(Paragraph(
    "<font name='CodeFont' size='8.5'>"
    "environment.systemPackages = with pkgs; [<br/>"
    "  openssh git vim tcpdump htop nix-prefetch-scripts<br/>"
    "];<br/>"
    "services.xserver.enable = false;            # pas de X11<br/>"
    "services.printing.enable = false;           # pas d'impression<br/>"
    "services.avahi.enable = false;              # pas de mDNS<br/>"
    "<br/>"
    "services.ntp.enable = true;                 # heure précise pour SIEM<br/>"
    "services.chrony.enable = true;              # source de temps robuste<br/>"
    "</font>",
    styles['code']
))
story.append(Paragraph(
    "<b>Extrait 7 — Empreinte minimale : pas de X11, paquets restreints, NTP pour le SIEM.</b>",
    styles['caption']
))
story.append(Paragraph(
    "La <b>synchronisation NTP</b> est essentielle : sans horloges cohérentes, les "
    "événements remontés par auditd, SSH et fail2ban ne peuvent être corrélés "
    "correctement dans Wazuh. Une dérive d'horloge de quelques secondes suffit à "
    "masquer la séquence réelle d'une attaque.",
    styles['body']
))

# --- 4.8 Logs vers Wazuh ---
story.append(add_heading("4.8. Logs remontés vers Wazuh", styles, 1))
story.append(Paragraph(
    "Tous les journaux du bastion — authentifications SSH, règles auditd, bannissements "
    "fail2ban, déploiements <font name='CodeFont'>nixos-rebuild</font> — sont transférés "
    "vers Wazuh (10.10.99.10) via <font name='CodeFont'>rsyslog</font> sur le port 514. "
    "Le bastion ne conserve qu'une copie locale ; la source de vérité pour la corrélation "
    "est le SIEM.",
    styles['body']
))
story.append(Paragraph(
    "<font name='CodeFont' size='8.5'>"
    "services.rsyslogd.enable = true;<br/>"
    "services.rsyslogd.defaultConfig = ''<br/>"
    "  *.*  @@10.10.99.10:514        # forward TCP vers Wazuh<br/>"
    "  auth,authpriv.*  /var/log/auth.log   # copie locale<br/>"
    "'';<br/>"
    "</font>",
    styles['code']
))
story.append(Paragraph(
    "<b>Extrait 8 — rsyslog : forward des logs vers Wazuh (10.10.99.10:514).</b>",
    styles['caption']
))
story.append(Paragraph(
    "Le forward en TCP (et non UDP) garantit la délivrance : en cas d'indisponibilité "
    "temporaire de Wazuh, rsyslog bufferise et retransmet. Wazuh corrèle alors les "
    "événements du bastion avec ceux des autres hôtes (OPNsense, serveurs du VLAN 30) "
    "pour reconstituer la chronologie complète d'une session d'administration.",
    styles['body']
))

# ============================================================
# 5. CLÉ FIDO2
# ============================================================
story.append(add_heading("5. Clé FIDO2 (facteur matériel)", styles, 0))
story.append(Paragraph(
    "L'accès au bastion exige une clé SSH de type <b>ed25519-sk</b> (<i>sk</i> pour "
    "<i>security key</i>). Cette clé est stockée dans un token matériel FIDO2 — une "
    "clé USB physique de type YubiKey — et non dans un fichier sur disque. Le suffixe "
    "<font name='CodeFont'>-sk</font> indique à OpenSSH que la partie privée de la clé "
    "réside sur le token et qu'une opération de signature doit déléguer au matériel.",
    styles['body']
))

story.append(Paragraph(
    "La génération se fait en une commande, après avoir inséré le token :",
    styles['body']
))
story.append(Paragraph(
    "<font name='CodeFont' size='8.5'>"
    "$ ssh-keygen -t ed25519-sk -C \"admin@bastion\"<br/>"
    "# Le token demande un toucher physique + un PIN FIDO2<br/>"
    "# → ~/.ssh/id_ed25519_sk      (handle public, sans secret)<br/>"
    "# → ~/.ssh/id_ed25519_sk.pub  (à déposer dans authorized_keys du bastion)<br/>"
    "</font>",
    styles['code']
))
story.append(Paragraph(
    "<b>Extrait 9 — Génération d'une clé SSH FIDO2 (ed25519-sk).</b>",
    styles['caption']
))

story.append(add_heading("5.1. Résistance au phishing et à l'exfiltration", styles, 1))
story.append(Paragraph(
    "Contrairement à une clé logicielle classique (fichier <font name='CodeFont'>"
    "id_ed25519</font>), une clé FIDO2 ne peut pas être <b>clonée</b> ni <b>copiée</b> "
    "à distance : la partie privée ne quitte jamais le token. Même si le poste "
    "administrateur est entièrement compromis par un malware, l'attaquant ne peut pas "
    "voler la clé — il peut au pire <i>utiliser</i> le token pendant qu'il est "
    "physiquement inséré, ce qui suppose déjà un compromis runtime actif.",
    styles['body']
))
fido_data = [
    ["Critère", "Clé logicielle (ed25519)", "Clé matérielle (ed25519-sk)"],
    ["Stockage du secret privé",
     "Fichier sur disque (~/.ssh/id_ed25519)",
     "Token FIDO2, non exportable"],
    ["Résistance au phishing",
     "Faible : la clé peut être volée par malware",
     "Forte : secret non clonable"],
    ["Facteur utilisateur",
     "Aucun (passphrase optionnelle)",
     "Toucher + PIN FIDO2"],
    ["Compromission du poste",
     "Clé exfiltrable à distance",
     "Clé non exfiltrable"],
    ["Perte du support",
     "—",
     "Clé inservible sans le token"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 6 — Clé logicielle vs clé FIDO2</b>", styles['caption']))
story.append(make_table(fido_data, col_ratios=[0.24, 0.36, 0.40]))
story.append(Paragraph(
    "La clé FIDO2 apporte donc deux garanties décisives pour un bastion : "
    "<b>anti-clonage</b> (le secret reste matériel) et <b>présence physique</b> "
    "(chaque signature demande un toucher, ce qui empêche l'usage automatisé à "
    "l'insu de l'administrateur). C'est l'incarnation du principe d'authentification "
    "forte recommandé par l'ANSSI pour les accès privilégiés.",
    styles['body']
))



# ============================================================
# 6. CHECKLIST DE DURCISSEMENT
# ============================================================
story.append(add_heading("6. Checklist de durcissement", styles, 0))
story.append(Paragraph(
    "Le tableau suivant récapitule l'ensemble des mesures appliquées au bastion, "
    "regroupées par domaine. Il sert de référence d'audit et de support de présentation "
    "en entretien : chaque ligne répond à une question concrète « comment ? » et "
    "« pourquoi ? ».",
    styles['body']
))
checklist_data = [
    ["Domaine", "Mesure", "Implémentation", "Justification"],
    ["Authentification", "Root interdit",
     "PermitRootLogin = \"no\"",
     "Pas de connexion root directe"],
    ["Authentification", "Mot de passe interdit",
     "PasswordAuthentication = false",
     "Neutralise le bruteforce SSH"],
    ["Authentification", "Clé FIDO2 obligatoire, 3 essais max",
     "ed25519-sk, AllowUsers admin, MaxAuthTries = 3",
     "Facteur matériel anti-clonage"],
    ["Cryptographie", "Algorithmes modernes",
     "chacha20-poly1305, ed25519, SHA-2 + bannière légale",
     "Écarte SHA-1, DSA, 3DES, CBC"],
    ["Immuabilité", "Nix store lecture seule",
     "boot.readOnlyNixStore = true",
     "Binaires système non remplaçables"],
    ["Immuabilité", "/tmp en RAM",
     "boot.tmpOnTmpfs = true",
     "Anti-persistance des artefacts"],
    ["Immuabilité", "Config versionnée Git + rollback",
     "/etc/nixos = dépôt Git, nixos-rebuild --rollback",
     "Audit, revue, retour arrière instantané"],
    ["Réseau", "Pare-feu local default-deny",
     "networking.firewall + iptables",
     "Défense en profondeur"],
    ["Réseau", "SSH entrant VLAN 99, sortant VLAN 30",
     "iptables -s/-d sur sous-réseaux",
     "Zone admin isolée, ProxyJump ciblé"],
    ["Réseau", "Blocage VLAN 10/20",
     "iptables -j DROP",
     "Isolation zones moins fiables"],
    ["Audit", "Surveillance fichiers clés + sudo",
     "auditd -w /etc/nixos, sudoers, passwd, sudo",
     "Détection de modification et d'élévation"],
    ["Audit", "Logs vers SIEM",
     "rsyslog @@10.10.99.10:514",
     "Corrélation centralisée"],
    ["sysctl", "ASLR complet",
     "kernel.randomize_va_space = 2",
     "Complique l'exploitation mémoire"],
    ["sysctl", "ptrace restreint",
     "kernel.yama.ptrace_scope = 2",
     "Anti-inspection de processus"],
    ["sysctl", "Anti-spoofing / SYN flood / martians",
     "rp_filter=1, tcp_syncookies=1, log_martians=1",
     "Robustesse et détection réseau"],
    ["Services", "Pas d'environnement graphique",
     "services.xserver.enable = false",
     "Réduction de la surface"],
    ["Services", "NTP activé",
     "services.chrony.enable = true",
     "Corrélation temporelle SIEM"],
    ["ProxyJump", "Relais obligatoire + anti-MITM",
     "ssh -J bastion, known_hosts verrouillé",
     "Aucune route directe vers VLAN 30"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 7 — Checklist de durcissement du bastion NixOS</b>", styles['caption']))
story.append(make_table(checklist_data, col_ratios=[0.16, 0.22, 0.30, 0.32]))

# ============================================================
# 7. L'ARGUMENT « WAOUH »
# ============================================================
story.append(add_heading("7. L'argument « Waouh » pour l'entretien", styles, 0))
story.append(Paragraph(
    "En entretien, le bastion NixOS est l'élément qui distingue ce projet d'un "
    "durcissement Linux classique. La force de la démonstration tient en quatre piliers "
    "qui, combinés, réalisent une posture d'administration privilégiée rarement atteinte "
    "même dans des SI plus matures.",
    styles['body']
))
pillars_data = [
    ["Pilier", "Mise en œuvre", "Bénéfice"],
    ["1. Authentification forte",
     "Clé FIDO2 (ed25519-sk), root interdit, 3 essais",
     "Anti-clonage, anti-bruteforce, facteur matériel"],
    ["2. Immuabilité",
     "NixOS déclaratif, Nix store RO, /tmp en RAM, Git",
     "Anti-persistance : la backdoor ne survit pas"],
    ["3. Défense en profondeur",
     "Pare-feu OPNsense + pare-feu local + sysctl + fail2ban",
     "Plusieurs couches indépendantes à franchir"],
    ["4. Administration tracée",
     "ProxyJump, auditd, logs forwardés vers Wazuh, NTP",
     "Toute session est journalisée et corrélable"],
]
story.append(Spacer(1, 6))
story.append(Paragraph("<b>Tableau 8 — Les quatre piliers du bastion</b>", styles['caption']))
story.append(make_table(pillars_data, col_ratios=[0.26, 0.40, 0.34]))

story.append(Paragraph("<b>Le pitch en une phrase</b>", styles['h3']))
story.append(Paragraph(
    "« Si un attaquant modifie <font name='CodeFont'>/etc/ssh/sshd_config</font> pour "
    "ajouter un mot de passe, NixOS l'écrasera au prochain déploiement. L'immuabilité "
    "empêche la persistance. »",
    styles['callout']
))
story.append(Paragraph(
    "Cette phrase résume à elle seule la valeur ajoutée du bastion : là où un durcissement "
    "classique rend l'attaque <i>difficile</i>, l'immuabilité déclarative de NixOS la "
    "rend <i>non durable</i>. Combinée à l'authentification FIDO2 (anti-clonage), au "
    "ProxyJump (pas de route directe vers les serveurs) et à la journalisation centralisée "
    "(toute session est corrélée dans Wazuh), elle réalise une posture d'administration "
    "privilégiée alignée sur les recommandations ANSSI — et argumentable en entretien "
    "avec une démonstration reproductible.",
    styles['body']
))
story.append(Paragraph(
    "<i>Cette annexe est le quatrième volet de la documentation Defend-The-Core. "
    "Les annexes 1 (Réseau & OPNsense), 2 (Wazuh / SIEM) et 3 (Durcissement des "
    "serveurs) détaillent les autres domaines de la posture de sécurité.</i>",
    styles['body_left']
))

# ============================================================
# BUILD
# ============================================================
doc.multiBuild(story)
print(f"PDF généré : {OUTPUT}")
