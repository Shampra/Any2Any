# Any2Any — Migrateur Anytype → Anytwo

**[Français](README.md) · [English](README.en.md)**

**Any2Any** est un outil communautaire de migration permettant de transférer des données d’**Anytype** vers **Anytwo**, à partir des API locales des deux applications.

Il propose une **interface web locale** pour parcourir les espaces Anytype, sélectionner un espace entier, une collection, plusieurs types ou des objets précis, puis choisir leur destination dans Anytwo.

> [!WARNING]
> **Outil expérimental — versions alpha d’Anytwo**
>
> Any2Any a été développé et utilisé pour **tester les versions alpha d’Anytwo**, et non comme solution de migration stable ou officiellement prise en charge. Il est fonctionnel sur certains scénarios, mais **aucune garantie n’est donnée quant à sa compatibilité avec les versions futures d’Anytwo, au bon déroulement d’un import ou à la qualité et à la fidélité des éléments transférés**. Les API et les formats peuvent évoluer sans préavis.
>
> **Ne migrez pas vos seules copies de données importantes.** Sauvegardez vos données, commencez avec quelques objets dans un **espace Anytwo de test**, puis vérifiez manuellement les résultats. Il n’y a ni annulation automatique ni garantie d’absence de doublons.

## Fonctionnalités

- **Sélection ciblée** : espaces, collections, types et objets Anytype ; ajout facultatif des objets liés.
- **Choix des destinations** : espaces et collections Anytwo existants ou à créer.
- **Import de contenu** : pages, propriétés et relations, textes mis en forme, liens, images et autres fichiers, dans la limite des capacités de conversion actuelles.
- **Archives des chats (option)** : chats exclus par défaut ; une page d’archive par chat de l’espace source, avec auteurs, dates, réponses, réactions et pièces jointes selon l’option fichiers.
- **Import local** : les échanges passent par les API ouvertes par les applications sur votre machine ; Anytype reste en lecture seule.
- **Simulation avant import** : bouton **Tester** pour examiner le périmètre prévu sans écrire dans Anytwo.
- **Rapport après import** : objets importés, raisons de leur sélection, adaptations, limitations et erreurs, exportable en JSON.
- **Interface multilingue** : français, anglais et allemand ; la langue choisie est mémorisée dans le navigateur.

## Installation et utilisation

**Prérequis :** Python **3.10+**, les clients **Anytype** et **Anytwo** ouverts sur le même ordinateur, et l’autorisation d’accès à l’API Anytype.

1. Téléchargez et décompressez le projet.
2. Ouvrez Anytype et Anytwo.
3. Sous Windows, lancez `demarrer.bat` ; sinon, exécutez `python server.py` depuis le dossier du projet.
4. L’interface s’ouvre dans le navigateur. Vérifiez les connexions aux API et autorisez Anytype si nécessaire.
5. Sélectionnez les données à importer et la destination Anytwo.
6. Utilisez **Tester**, puis **Importer** après avoir vérifié la destination.

Pour consulter l’interface sans ouvrir les applications : lancez normalement `demarrer.bat`, laissez les vérifications API se terminer, puis fermez la fenêtre de connexion avec la croix. Le statut API reste rouge, les imports sont désactivés et le sélecteur FR/EN/DE reste disponible. Pour explorer des données fictives, utilisez `demo.bat` ou `python server.py --demo` (aucun import réel en démonstration).

L’interface écoute uniquement sur `127.0.0.1` (port local à partir de `8765`). Les ports des API et l’autorisation sont mémorisés sur cet ordinateur. Le port Anytwo habituel est `31310` et le port Anytype habituel `31009`.

## Limitations connues

Les applications n’utilisent pas toujours les mêmes modèles de données. Certaines informations peuvent être simplifiées, transformées ou perdues : **types, modèles, propriétés globales ou locales, vues dynamiques et requêtes, filtres avancés, éléments de collection intégrés aux pages, table des matières, discussions, bookmarks enrichis et réglages de présentation**. Cette liste n’est pas exhaustive.

Les embeds, les mises en page complexes et certains formats peuvent ne pas être reconstruits comme des blocs natifs Anytwo, même lorsque l’application sait les afficher manuellement. Les rapports d’import signalent les adaptations détectées, mais **ne peuvent pas prouver à eux seuls que toutes les données ont été fidèlement restituées**.

Le mode **Import simple** crée de nouveaux objets à chaque exécution. La **synchronisation**, la reprise automatique après interruption, la déduplication et l’annulation ne sont **pas encore disponibles**.

## À propos du projet

Ce projet est indépendant et **n’est ni officiel ni affilié à Anytype ou à Anytwo**. Any2Any est distribué sous [licence GNU GPLv3](LICENSE). Copyright (c) 2026 Shampra.

Pour le fonctionnement détaillé et les notes de versions actuelles : [Notes techniques en français](docs/NOTES-TECHNIQUES.fr.md).
