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
- **Destination Anytwo** : espace existant ou nouvel espace. Pour Anytype, une collection existante peut aussi être choisie lorsque ce mode est proposé. Pour Notion, chaque source de données importée crée sa collection/supertag et ses propriétés ; les schémas ne sont pas fusionnés avec une collection existante.
- **Import de contenu** : pages, propriétés et relations, textes mis en forme, liens, images et autres fichiers, dans la limite des capacités de conversion actuelles.
- **Archives des chats Anytype (option)** : chats exclus par défaut ; une page d’archive par chat de l’espace source, avec auteurs, dates, réponses, réactions et pièces jointes selon l’option fichiers.
- **Sources en lecture seule** : aucune modification d’Anytype ou de Notion. Les fichiers Notion sont récupérés sur Internet ; leurs téléchargements ne reçoivent pas le jeton API.
- **Simulation avant import** : bouton **Tester** pour examiner le périmètre prévu sans écrire dans Anytwo.
- **Rapport après import** : objets importés, raisons de leur sélection, adaptations, limitations et erreurs, exportable en JSON.
- **Interface multilingue** : français, anglais et allemand ; la langue choisie est mémorisée dans le navigateur.

## Installation et utilisation

**Prérequis :** Python **3.10+** et le client **Anytwo** ouvert. Pour Anytype, ouvrez aussi son client et autorisez son API. Pour Notion, utilisez un jeton de connexion autorisé à lire les pages voulues ; le client Notion n’a pas besoin d’être ouvert. Aucune bibliothèque Python supplémentaire n’est nécessaire.

1. Ouvrez les [releases GitHub](https://github.com/Shampra/Any2Any/releases) et téléchargez l’archive **de l’application** jointe à la publication souhaitée. Décompressez-la et ouvrez le dossier `Any2Any`. L’empreinte SHA-256 jointe permet de vérifier le téléchargement.
2. Ouvrez Anytwo et, si vous importez depuis Anytype, son client.
3. Sous Windows, lancez `demarrer.bat` ; sinon, exécutez `python server.py` depuis le dossier du projet.
4. Choisissez **Anytype** ou **Notion** dans la fenêtre d’accueil, puis vérifiez les accès. Un jeton Notion mémorisé est contrôlé automatiquement. La source peut ensuite être changée dans le sélecteur en haut de l’écran.
5. Sélectionnez les données à importer et la destination Anytwo.
6. Utilisez **Tester**, puis **Importer** après avoir vérifié la destination.

### Connexion à la source

- **Anytype** : laissez Anytype et Anytwo ouverts. Utilisez **Autoriser dans Anytype**, puis terminez l’association demandée. Les échanges source passent par l’API locale.
- **Notion** : créez une connexion interne avec accès en lecture et partagez avec elle les pages et bases à importer. Saisissez le jeton uniquement dans le formulaire de l’outil ; le partage d’une page qui contient une vue liée ne garantit pas l’accès à sa base d’origine. Le jeton peut être mémorisé sous Windows, puis oublié depuis les réglages. Internet est nécessaire ; le client Notion peut rester fermé. Voir [le guide de connexion Notion](docs/NOTION-API.fr.md).

Le bouton d’état des API, en haut à droite, permet de rouvrir les réglages de connexion. Les options **Récupérer les fichiers** et **Importer les éléments liés** sont adaptées à la source et au périmètre choisis.

Pour explorer des données fictives sans connexion ni import réel, utilisez `demo.bat` ou `python server.py --demo`.


L’interface écoute uniquement sur `127.0.0.1` (port local à partir de `8766`). Les réglages sont conservés dans `%APPDATA%/any2any` sous Windows. Les autorisations mémorisées dans les profils de développement peuvent être reprises à la première ouverture, sans modifier les anciennes configurations. Les secrets mémorisés sont protégés par Windows DPAPI. Le port Anytwo habituel est `31310` et le port Anytype habituel `31009`.

## Limitations connues

Les applications ont des modèles différents. Les formules Notion deviennent des résultats figés. Les boutons, couleurs de texte/fond, rappels, historique et certains formats de vues ou de blocs peuvent être adaptés ou non repris. Les graphiques Notion ne sont pas importés ; certains regroupements de vues inline sont adaptés en listes. Les vues de collection compatibles conservent leurs regroupements, leurs filtres et leur tri. Les galeries reprennent **Fit image**, et l’ouverture se fait en **side peek**, sauf indication explicite de pleine page fournie par la source. Les limites affichées dans l’application sont propres à la source choisie ; les bilans précisent les pertes détectées. Consultez aussi [le fonctionnement de l’import Notion](docs/NOTION-IMPORT.fr.md).

L’import simple crée de nouvelles copies à chaque lancement. Une relance peut donc créer des doublons. Les lectures Notion interrompues peuvent être réutilisées en mémoire pendant 30 minutes ; cela ne reprend pas automatiquement les écritures et ne constitue pas une synchronisation. Il n’y a pas d’annulation globale.

## À propos du projet

Ce projet est indépendant et **n’est ni officiel ni affilié à Anytype, Notion ou Anytwo**. Any2Any est distribué sous [licence GNU GPLv3](LICENSE). Copyright (c) 2026 Shampra.

Fonctionnement détaillé : [import Anytype](docs/NOTES-TECHNIQUES.fr.md), [import Notion](docs/NOTION-IMPORT.fr.md) et [connexion/API Notion](docs/NOTION-API.fr.md). L’historique des changements est disponible dans le [changelog](CHANGELOG.md).
