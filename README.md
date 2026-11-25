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
- **Widgets Anytype** : les raccourcis vers les pages et collections importées sont repris dans l’Overview, avec leur ordre et les modes Link ou Views.
- **Destination Anytwo** : espace existant ou nouvel espace. Pour Anytype, une collection existante peut aussi être choisie lorsque ce mode est proposé. Pour Notion, chaque source de données importée crée sa collection/supertag et ses propriétés ; les schémas ne sont pas fusionnés avec une collection existante.
- **Import de contenu** : pages, propriétés et relations, textes mis en forme, liens, images et autres fichiers, dans la limite des capacités de conversion actuelles.
- **Archives des chats Anytype (option)** : chats exclus par défaut ; une page d’archive par chat de l’espace source, avec auteurs, dates, réponses, réactions et pièces jointes selon l’option fichiers.
- **Sources en lecture seule** : aucune modification d’Anytype ou de Notion. Les fichiers Notion sont récupérés sur Internet ; leurs téléchargements ne reçoivent pas le jeton API.
- **Simulation avant import** : bouton **Tester** pour examiner le périmètre prévu sans écrire dans Anytwo.
- **Rapport après import** : objets importés, raisons de leur sélection, adaptations, limitations et erreurs, exportable en JSON.
- **Interface multilingue** : français, anglais et allemand ; la langue choisie est mémorisée dans le navigateur.

## Installation et utilisation

**Prérequis :** le client **Anytwo** ouvert. L’archive **Windows autonome** inclut Python ; l’archive **source** demande Python **3.10+**. Pour Anytype, ouvrez aussi son client et autorisez son API. Pour Notion, utilisez un jeton de connexion autorisé à lire les pages voulues ; le client Notion n’a pas besoin d’être ouvert. Aucune bibliothèque Python supplémentaire n’est nécessaire.

1. Ouvrez les [releases GitHub](https://github.com/Shampra/Any2Any/releases) et téléchargez l’archive **de l’application** jointe à la publication souhaitée. Décompressez-la dans un dossier dédié, puis ouvrez ce dossier. L’empreinte SHA-256 jointe permet de vérifier le téléchargement.
2. Ouvrez Anytwo et, si vous importez depuis Anytype, son client.
3. Lancez l’application selon votre système :
   - **Windows autonome** : double-cliquez sur **`Any2Any.exe`**, directement à la racine de l’archive.
   - **Windows source** : double-cliquez sur **`demarrer.bat`**.
   - **macOS** : double-cliquez sur **`Any2Any.command`**. Si macOS bloque l’ouverture, cliquez avec le bouton droit sur le fichier, choisissez **Ouvrir**, puis confirmez. Le terminal affiche l’adresse locale.
   - **Linux ou terminal** : `./Any2Any.command` ou `python3 app/server.py --profile unified`.
4. Le navigateur s’ouvre sur `http://127.0.0.1:8766`. Si ce n’est pas le cas, ouvrez cette adresse à la main ; elle est aussi affichée dans le terminal.
5. Choisissez **Anytype** ou **Notion** dans la fenêtre d’accueil, puis vérifiez les accès. Un jeton Notion mémorisé est contrôlé automatiquement. La source peut ensuite être changée dans le sélecteur en haut de l’écran.
6. Sélectionnez les données à importer et la destination Anytwo.
7. Utilisez **Tester**, puis **Importer** après avoir vérifié la destination.
8. Fermez la fenêtre du terminal (ou `Ctrl+C`) pour arrêter l’application ; les réglages sont conservés pour la prochaine ouverture.

### Organisation du dossier

L’archive Windows contient `Any2Any.exe` à la racine, les dépendances dans `_internal/` et la documentation dans `documentation/`. Gardez ces dossiers avec l’exécutable.

Le dépôt et l’archive source conservent les lanceurs à la racine (`demarrer.bat`, `demo.bat`, `Any2Any.command`) ; les fichiers nécessaires sont regroupés dans `app/`. Le dossier `dev/`, présent dans le dépôt mais exclu de l’archive de l’application, rassemble les tests et les outils de développement.

Si le port `8766` est déjà utilisé, l’application choisit le suivant : l’adresse réellement utilisée est affichée dans le terminal. Aucun droit administrateur n’est demandé, et rien n’est exposé en dehors de `127.0.0.1`.

### Premier lancement de l’exécutable

L’exécutable **`Any2Any.exe`** est produit par GitHub Actions pour chaque publication et joint au release. Il n’installe rien et ne demande pas Python, mais Windows peut afficher un avertissement SmartScreen (éditeur non signé) : cliquez sur **Informations complémentaires**, puis **Exécuter quand même**. Les fichiers `_internal/`, `documentation/` et l’exécutable doivent rester ensemble. Un raccourci vers `Any2Any.exe` peut être placé sur le bureau.

### Connexion à la source

- **Anytype** : laissez Anytype et Anytwo ouverts. Utilisez **Autoriser dans Anytype**, puis terminez l’association demandée. Les échanges source passent par l’API locale.
- **Notion** : créez une connexion interne avec accès en lecture et partagez avec elle les pages et bases à importer. Saisissez le jeton uniquement dans le formulaire de l’outil ; le partage d’une page qui contient une vue liée ne garantit pas l’accès à sa base d’origine. Le jeton peut être mémorisé sous Windows, puis oublié depuis les réglages. Internet est nécessaire ; le client Notion peut rester fermé. Voir [le guide de connexion Notion](docs/NOTION-API.fr.md).

Le bouton d’état des API, en haut à droite, permet de rouvrir les réglages de connexion. Les options **Récupérer les fichiers** et **Importer les éléments liés** sont adaptées à la source et au périmètre choisis.

Pour explorer des données fictives sans connexion ni import réel, utilisez `demo.bat` (Windows), `Any2Any.command --demo` (macOS) ou `python app/server.py --demo`, selon votre archive. L’import reste désactivé dans ce mode, mais l’interface et la langue se testent librement.


L’interface écoute uniquement sur `127.0.0.1` (port local à partir de `8766`). Les réglages sont conservés dans `%APPDATA%/any2any` sous Windows. Les autorisations mémorisées dans les profils de développement peuvent être reprises à la première ouverture, sans modifier les anciennes configurations. Les secrets mémorisés sont protégés par Windows DPAPI. Le port Anytwo habituel est `31310` et le port Anytype habituel `31009`.

## Limitations connues

Les applications ont des modèles différents. Les formules Notion deviennent des résultats figés. Les boutons, couleurs de texte/fond, rappels, historique et certains formats de vues ou de blocs peuvent être adaptés ou non repris. Les graphiques Notion ne sont pas importés ; certains regroupements de vues inline sont adaptés en listes. Les vues de collection compatibles conservent leurs regroupements, leurs filtres et leur tri. Les galeries reprennent **Fit image**, et l’ouverture se fait en **side peek**, sauf indication explicite de pleine page fournie par la source. Les limites affichées dans l’application sont propres à la source choisie ; les bilans précisent les pertes détectées. Consultez aussi [le fonctionnement de l’import Notion](docs/NOTION-IMPORT.fr.md).

Certaines fonctionnalités Anytype ne sont pas encore disponibles dans Anytwo ou ont un fonctionnement différent qui empêche leur reprise à l’identique. Cela concerne les couleurs (texte, fond, blocs, cellules, callouts), les types, les propriétés locales et globales, les propriétés de type fichier ou image, les bookmarks, les discussions, les mini-apps et les affichages de collection Graph et Calendar. L’alignement dans les blocs et les cellules, ainsi que les mises en page avancées avec vues dans des callouts ou des colonnes, ne sont pas toujours conservés. Les propriétés fichiers/images sont remplacées par leur contenu en début de page lorsque les fichiers sont récupérés. Les vues en ligne globales sont limitées à une seule collection Anytwo. Elles ne restent pas dans des colonnes de blocs. Certains filtres dynamiques et restrictions de relation ne sont pas transposables. Les widgets système Anytype sont ignorés et la configuration de la barre latérale Notion n’est pas accessible via son API publique. Les templates Anytype sont importés comme templates Anytwo avec leurs propriétés, leur contenu et leur défaut de collection lorsque celui-ci est déterminable. Les sommaires Anytype utilisent le bloc dynamique natif sur les versions Anytwo compatibles ; les sommaires imbriqués et ceux de Notion restent des liens statiques. Les filtres compatibles conservent leurs groupes ET/OU, les sélections simples et les conditions de valeurs vides. Les dates relatives et certaines conditions avancées restent signalées si elles ne peuvent pas être transposées exactement. Le soulignement et certaines présentations de vues dépendent de la version d’Anytwo.

L’import simple crée de nouvelles copies à chaque lancement. Une relance peut donc créer des doublons. Les lectures Notion interrompues peuvent être réutilisées en mémoire pendant 30 minutes ; cela ne reprend pas automatiquement les écritures et ne constitue pas une synchronisation. Il n’y a pas d’annulation globale.

## À propos du projet

Ce projet est indépendant et **n’est ni officiel ni affilié à Anytype, Notion ou Anytwo**. Any2Any est distribué sous [licence GNU GPLv3](LICENSE). Copyright (c) 2026 Shampra.

Fonctionnement détaillé : [import Anytype](docs/NOTES-TECHNIQUES.fr.md), [import Notion](docs/NOTION-IMPORT.fr.md) et [connexion/API Notion](docs/NOTION-API.fr.md). Chaque guide existe aussi en anglais (`.en.md`). L’historique des changements est disponible dans le [changelog](CHANGELOG.md).
