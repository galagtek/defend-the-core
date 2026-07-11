

  

---

  

# 🏗️ Projet : Infrastructure "Defend-The-Core" (PME Critique)

  

**Le scénario :** Vous êtes recruté par une PME (ex: cabinet d'audit financier ou industriel) qui manipule des données sensibles. L'infrastructure actuelle est "plate" (tout le monde peut pinguer les serveurs de BDD). On vous demande de reconcevoir l'infrastructure selon les recommandations ANSSI, en intégrant de la surveillance avancée et en empêchant la propagation d'une attaque depuis un poste utilisateur.

  

## 1. L'Architecture Réseau (Zoning & VLANs)

  

Sous VirtualBox, vous utiliserez le réseau "NAT" pour l'accès internet, mais vous créerez des **Réseaux Internes** (Host-Only ou Internal Network) pour simuler les VLANs et le zoning.

  

* **VLAN 10 - ZONE BUREAUTIQUE (Non fiable) :** Le réseau des utilisateurs classiques.

* **VLAN 20 - ZONE DMZ (Publique) :** Les services exposés (Proxy inverse, VPN Gateway).

* **VLAN 30 - ZONE CRITIQUE (Serveurs) :** BDD, Applications métier. Aucun accès direct depuis la zone 10.

* **VLAN 99 - ZONE ADMIN / SIEM (Très Restreint) :** Le cœur de surveillance et d'administration. Seuls les administrateurs y ont accès.

  

## 2. La Topologie VirtualBox (Les VMs)

  

Avec une machine puissante (64Go RAM conseillé pour le confort), voici les VMs à déployer :

  

### 🔥 Le Pare-Feu / Routeur (Le Gardien)

* **VM : OPNsense** (Plus moderne et ouvert que pfSense).

* **Rôle :** Il a une patte dans chaque VLAN. Il assure le routage inter-VLAN avec des règles de filtrage strictes (Default Deny).

* **Règle clé :** Le VLAN 10 ne peut joindre que le VLAN 20 sur des ports spécifiques (80/443). Le VLAN 10 ne peut **jamais** joindre le VLAN 30 directement. Le VLAN 99 est isolé, seuls les flux de logs (514/1514) et SSH (22) y entrent.

  

### 🛡️ L'Infrastructure de Sécurité (Le Noyau)

* **VM : Wazuh (SIEM/XDR) + Elastic/Kibana** (Installez via le script OVA officiel pour économiser des ressources, ou sur un Ubuntu Server robuste).

* **Rôle :** Collecte les logs de toutes les VMs, corrélation, alertes.

* **VM : Le Bastion / PAW (Privileged Access Workstation) - NixOS**

* **Rôle :** C'est la star du projet. Machine durcie selon la config vue précédemment.

* **Concept :** L'admin ne se connecte **jamais** directement aux serveurs du VLAN 30 depuis son poste Windows. Il se connecte d'abord au Bastion NixOS, et du Bastion, il lance son SSH vers les serveurs critiques. (ProxyJump SSH).

  

### 🖥️ Les Serveurs Métier (La Cible)

* **VM : Windows Server 2022** (Active Directory, DNS, DHCP pour le VLAN 10).

* **VM : Ubuntu Server 22.04** (Serveur Web + BDD dans le VLAN 30).

* **Durcissement :** Installez l'agent Wazuh, configurez Auditd, désactivez le SSH par mot de passe (clés uniquement).

  

### 💻 Les Postes Clients (Les Vecteurs d'attaque)

* **VM 1 : Windows 10/11 "Standard"** (VLAN 10). Simule un employé classique. Installez l'agent Wazuh.

* **VM 2 : Kali Linux** (VLAN 10 ou depuis l'extérieur). Simule l'attaquant.

  

---

  

## 3. La Mise en Pratique (Ce que vous allez démontrer)

  

Pour un entretien, ce n'est pas l'installation qui compte, mais **les scénarios de validation**. Préparez ces démos :

  

### Scénario 1 : La Détection (Le SIEM en action)

1. Depuis la VM Kali, lancez un scan Nmap ou un bruteforce SSH contre le serveur Ubuntu.

2. **Résultat attendu :** Montrez le dashboard Kibana/Wazuh. L'alerte "Bruteforce détecté" s'allume. Montrez que Wazuh a automatiquement bloqué l'IP de Kali via l'intégration Firewall (Active Response).

  

### Scénario 2 : Le Zéro Trust (Segmentation)

1. Depuis le poste Windows 10 (VLAN 10), essayez de pinguer le serveur Ubuntu (VLAN 30) ou le serveur Wazuh (VLAN 99).

2. **Résultat attendu :** Ça ne passe pas. Montrez les logs OPNsense qui "Drop" le paquet. L'utilisateur ne voit que ce qu'il doit voir.

  

### Scénario 3 : L'Administration Sécurisée (Le PAW NixOS)

1. Montrez que l'admin ne peut pas SSH directement depuis Windows vers le serveur Ubuntu.

2. Montrez la connexion sécurisée : Windows -> (SSH avec clé FIDO2) -> Bastion NixOS -> (SSH avec clé) -> Serveur Ubuntu.

3. **Le "Waouh" effect :** Ouvrez le `configuration.nix` de votre NixOS lors de l'entretien. Montrez la ligne `PermitRootLogin = "no"`, `PasswordAuthentication = false`, et expliquez que si quelqu'un modifie la config SSH à la main, NixOS l'écrasera au prochain redémarrage ou déploiement (Immuabilité).

  

---

  

## 4. Comment présenter ce projet en entretien ?

  

Ne parlez pas technique d'abord, parlez **bénéfice métier**. Utilisez cette structure :

  

1. **Le Problème :** *"J'ai conçu ce labo car dans les PME, le plus grand risque est la latéralité. Si un poste utilisateur est compromis par un phishing, l'attaquant accède souvent à tout le réseau."*

2. **L'Architecture :** *"J'ai donc segmenté l'infrastructure en Zones (ANSSI/VLANs) avec OPNsense, en appliquant le principe du moindre privilège réseau."*

3. **La Détection :** *"Un réseau fermé ne suffit pas, il faut surveiller. J'ai déployé Wazuh pour avoir un SIEM centralisé capable de corréler les logs et de réagir (bloquer une IP en temps réel)."*

4. **La Gestion des Administrateurs :** *"Enfin, le point critique : l'accès privilégié. J'ai déployé un Bastion sous NixOS durci. NixOS me garantit l'immuabilité du système : la configuration est déclarative, empêchant toute dérive ou persistance d'un attaquant sur le poste d'administration."*

  

**Le petit plus qui tue (Bonus GitOps) :**

Mettez votre configuration NixOS (`configuration.nix`), vos règles OPNsense exportées, et vos dashboards Wazuh sauvegardés sur un **dépôt Git (GitHub/GitLab)**. Dire en entretien : *"Toute mon infra est 'Infrastructure as Code', vous pouvez consulter le dépôt Git ici"* vous classe directement dans la catégorie des administrateurs modernes (DevSecOps).