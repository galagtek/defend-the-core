# Scénarios de validation (démonstrations entretien)

Ces trois scénarios sont la **partie la plus importante** de votre présentation en
entretien. Ce n'est pas l'installation qui impressionne, mais la **démonstration
que les défenses fonctionnent**.

## Scénarios

| # | Scénario | Fichier | Ce que ça démontre |
|---|----------|---------|--------------------|
| 1 | Détection SIEM | [scenario-1-detection.md](scenario-1-detection.md) | Bruteforce SSH détecté → IP bloquée automatiquement |
| 2 | Zero Trust / segmentation | [scenario-2-zero-trust.md](scenario-2-zero-trust.md) | Win10 ne peut pas atteindre le VLAN 30 ni le VLAN 99 |
| 3 | Administration sécurisée (PAW) | [scenario-3-paw-nixos.md](scenario-3-paw-nixos.md) | SSH via ProxyJump : Win → Bastion → Serveur ; immuabilité |

## Déroulé type d'une démo

1. **Annoncer** ce qu'on va tester et le résultat attendu (avant de lancer)
2. **Exécuter** l'attaque/depuis la machine appropriée
3. **Montrer** le résultat côté défense (dashboard Wazuh, logs OPNsense, config NixOS)
4. **Expliquer** pourquoi ça fonctionne (règle, mécanisme)

## Pitch global (structure recommandée)

> 1. **Le problème** : dans les PME, le plus grand risque est la latéralité.
>    Un poste compromis = tout le réseau exposé.
> 2. **L'architecture** : j'ai segmenté en zones (ANSSI/VLANs) avec OPNsense,
>    en appliquant le moindre privilège réseau.
> 3. **La détection** : un réseau fermé ne suffit pas, il faut surveiller.
>    Wazuh corrèle les logs et réagit en temps réel.
> 4. **L'administration** : le point critique. Bastion NixOS = immuabilité.
>    La config est déclarative, empêchant toute dérive ou persistance.
> 5. **Le bonus** : toute l'infra est Infrastructure as Code sur GitHub.
