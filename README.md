# Any2Any — Anytype / Notion → Anytwo

**[Français](README.md) · [English](README.en.md)**

**Any2Any** est un outil de migration permettant de transférer des données d’**Anytype** ou de **Notion** vers **Anytwo**. Il utilise les API locales d’Anytype et d’Anytwo, et l’API Internet de Notion.

Une **interface web locale** permet de choisir la source au démarrage, de vérifier les accès, de sélectionner les éléments et de configurer leur destination Anytwo. Anytype et Notion réutilisent le même moteur de destination.

> [!WARNING]
> **Outil expérimental — versions alpha d’Anytwo**
>
> Any2Any a été développé et utilisé pour **tester les versions alpha d’Anytwo**, et non comme solution de migration stable ou officiellement prise en charge. Il est fonctionnel sur certains scénarios, mais **aucune garantie n’est donnée quant à sa compatibilité avec les versions futures d’Anytwo, au bon déroulement d’un import ou à la qualité et à la fidélité des éléments transférés**. Les API et les formats peuvent évoluer sans préavis.
>
> **Ne migrez pas vos seules copies de données importantes.** Sauvegardez vos données, commencez avec quelques objets dans un **espace Anytwo de test**, puis vérifiez manuellement les résultats. Il n’y a ni annulation automatique ni garantie d’absence de doublons.

## Fonctionnalités

- **Sélection Anytype** : espaces, collections, types et objets ; ajout facultatif des éléments liés.
- **Sélection Notion** : pages et bases dans une arborescence sélectionnable sur trois niveaux ; les descendants d’un élément coché sont aussi importés. L’option des éléments liés concerne ceux hors de cette arborescence.
- **Vues Notion** : vues inline et vues de collections, filtres, tris, regroupements compatibles et réglages de galerie. Relations bidirectionnelles et rollups compatibles sont configurés dans Anytwo.
- **Choix des destinations** : espaces et collections Anytwo existants ou à créer.
- **Import de contenu** : pages, propriétés et relations, textes mis en forme, liens, images et autres fichiers, dans la limite des capacités de conversion actuelles.
- **Archives des chats (option)** : chats exclus par défaut ; une page d’archive par chat de l’espace source, avec auteurs, dates, réponses, réactions et pièces jointes selon l’option fichiers.
- **Sources en lecture seule** : aucune modification d’Anytype ou de Notion. Les fichiers Notion sont récupérés sur Internet ; leurs téléchargements ne reçoivent pas le jeton API.
- **Simulation avant import** : bouton **Tester** pour examiner le périmètre prévu sans écrire dans Anytwo.
- **Rapport après import** : objets importés, raisons de leur sélection, adaptations, limitations et erreurs, exportable en JSON.
- **Interface multilingue** : français, anglais et allemand ; la langue choisie est mémorisée dans le navigateur.

## Installation et utilisation

**Prérequis :** Python **3.10+** et le client **Anytwo** ouvert. Pour Anytype, ouvrez aussi son client et autorisez son API. Pour Notion, utilisez un jeton de connexion autorisé à lire les pages voulues ; le client Notion n’a pas besoin d’être ouvert. Aucune bibliothèque Python supplémentaire n’est nécessaire.

1. Téléchargez et décompressez le projet.
2. Ouvrez Anytwo et, si vous importez depuis Anytype, son client.
3. Sous Windows, lancez `demarrer.bat` ; sinon, exécutez `python server.py` depuis le dossier du projet.
4. Choisissez **Anytype** ou **Notion** dans la fenêtre d’accueil, puis vérifiez les accès. Un jeton Notion mémorisé est contrôlé automatiquement. La source peut ensuite être changée dans le sélecteur en haut de l’écran.
5. Sélectionnez les données à importer et la destination Anytwo.
6. Utilisez **Tester**, puis **Importer** après avoir vérifié la destination.

Pour consulter l’interface sans ouvrir les applications : lancez normalement `demarrer.bat`, laissez les vérifications API se terminer, puis fermez la fenêtre de connexion avec la croix. Le statut API reste rouge, les imports sont désactivés et le sélecteur FR/EN/DE reste disponible. Pour explorer des données fictives, utilisez `demo.bat` ou `python server.py --demo` (aucun import réel en démonstration).

L’interface écoute uniquement sur `127.0.0.1` (port local à partir de `8766`). Les réglages sont conservés dans `%APPDATA%/any2any` sous Windows. Les autorisations mémorisées des profils de développement sont reprises à la première ouverture, sans modifier les anciennes configurations. Les secrets mémorisés sont protégés par Windows DPAPI. Le port Anytwo habituel est `31310` et le port Anytype habituel `31009`.

## Limitations connues

Les applications ont des modèles différents. Formules figées, boutons, couleurs de texte/fond, rappels, historique et certains formats de vues ou de blocs peuvent être adaptés ou non repris. Les limites affichées dans l’application sont propres à la source choisie ; les bilans précisent les pertes détectées. Consultez aussi [le fonctionnement de l’import Notion](docs/NOTION-IMPORT.fr.md).

L’import simple crée de nouvelles copies à chaque lancement. Une relance peut donc créer des doublons. Les lectures Notion interrompues peuvent être réutilisées en mémoire pendant 30 minutes ; cela ne reprend pas automatiquement les écritures et ne constitue pas une synchronisation. Il n’y a pas d’annulation globale.

## À propos du projet

Ce projet est indépendant et **n’est ni officiel ni affilié à Anytype ou à Anytwo**. Any2Any est distribué sous [licence GNU GPLv3](LICENSE). Copyright (c) 2026 Shampra.

Pour le fonctionnement détaillé et les notes de versions actuelles : [Notes techniques en français](docs/NOTES-TECHNIQUES.fr.md).
