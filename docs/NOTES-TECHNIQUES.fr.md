# Any2Any — Migrateur Anytype → Anytwo (v0.9.1-beta)

**Version du projet : 0.9.1-beta.** Les sections « Changements v0.8 » et « Changements v0.9 » ci-dessous constituent un historique des évolutions, pas la version actuelle du projet. Le moteur d’import provient de la v0.8, tandis que les traductions et l’identité Any2Any ont été ajoutées en v0.9.

Application Python + interface web locale permettant d'importer des espaces, collections, types et objets Anytype dans Anytwo. **L'import simple crée réellement des données dans Anytwo.** La source Anytype est toujours interrogée en lecture seule. L'option « Avec synchronisation » n'est **pas encore opérationnelle** et ne permet pas l'import réel.

> **À lire avant un premier essai** : cette version a été testée avec des API HTTP locales simulées et un navigateur automatisé, **pas** avec les clients Anytype et Anytwo réellement installés chez les utilisateurs. L'API Anytype v2 est une préversion évolutive. Commencez avec 1 ou 2 pages et un **espace Anytwo de test**, sauvegardez vos données et comparez le résultat. Il n'existe **aucun retour arrière automatique**. Un deuxième import simple créera de nouvelles copies.

## Démarrer sous Windows

1. Installer Python **3.10 ou plus récent** si nécessaire.
2. Décompresser toute l'archive.
3. Ouvrir **Anytype** et **Anytwo** et laisser les espaces charger.
4. Double-cliquer sur **`demarrer.bat`**, ou exécuter `python server.py`.
5. Dans le navigateur local, autoriser Anytype (code à quatre chiffres dans sa fenêtre), puis sélectionner la source et la destination.
6. Lancer **Tester** pour une simulation de périmètre, puis **Importer** pour les écritures réelles (confirmation supplémentaire).

Pour explorer l'interface sans application ouverte : `demo.bat` ou `python server.py --demo`. Le bouton d'import **reste désactivé en démonstration**.

Aucune dépendance Python supplémentaire n'est obligatoire. L'application web se limite à `127.0.0.1`, sur un port à partir de `8765`. Laisser ouverte la fenêtre console pendant l'utilisation.

**Connexion** : Anytype écoute normalement sur `31009` avec une clé API obtenue par appairage. Anytwo est détecté automatiquement (`31310`, `7001`, `2657`, `5344`, puis ports en écoute de `any.exe` sous Windows), ou via le bouton de statut « API ». Les ports sont mémorisés sous `%APPDATA%\anytype-anytwo-importer\settings.json`. La clé Anytype est protégée par Windows DPAPI (permissions de fichier utilisateur sous macOS/Linux).

## Ce que fait l'import

- Parcourt l'espace source, sa collection ou les types/objets choisis. Avec « Importer également les éléments liés », ajoute les objets référencés retrouvés dans cet espace et enregistre la **raison de leur inclusion**.
- Recrée les collections Anytype choisies ; une collection supplémentaire par **type** est créée lorsqu'il y a des propriétés à préserver (y compris des colonnes de type sans valeur). Les correspondances vers des collections Anytwo existantes sont respectées selon les choix de l'interface.
- Crée les pages **avant** de reconstruire les liens afin de réécrire les références vers leurs nouveaux identifiants Anytwo.
- Tente de transférer propriétés (`texte`, `numérique`, `booléen`, `dates`, `select`, `multi-select`, `relations`) et options. Les champs sans correspondance certaine sont convertis en texte **avec un avertissement**.
- Transcrit les blocs AnyBlock v2 en Markdown Anytwo : titres, paragraphes, emphases, listes, cases cochées, citations, callouts simplifiés, code, liens, fichiers et médias. Colonnes, tableaux enrichis, dimensions d’images et vidéos YouTube : tentative de restitution par HTML intégré au Markdown, avec repli en contenu simplifié si rejeté (le rendu Anytwo doit être contrôlé). Les blocs inconnus incluent leur JSON d'origine pour éviter une disparition silencieuse.
- Transfère des fichiers binaires par les API si l'option est cochée ; une image de couverture peut être ajoutée au début de la page, mais **pas** reproduite comme bannière d'origine. Les icônes emoji sont tentées comme métadonnée de l’objet (champ en cours de validation) : elles ne sont plus ajoutées au corps de page.
- Insère un **avertissement dans la page Anytwo** en présence de blocs/contenus majeurs non transposables : collection ou vue intégrée, bloc inconnu, fichier absent, lien non reconstruit, etc. Les pertes de présentation purement cosmétiques restent dans le rapport.
- Affiche un bilan avec chaque objet, les motifs (sélection manuelle, appartenance à une collection, objet lié), les adaptations et les erreurs ; regroupe les catégories d'incompatibilités. Permet d'**exporter un JSON**.
- Enregistre les bilans dans `%APPDATA%\anytype-anytwo-importer\reports\` (Windows), même en cas d'interruption lorsque l'opération a pu être suivie.

## Changements v0.6

- Le bouton « API » sert d’accès unique aux paramètres : engrenage supprimé.
- Les objets identifiés comme **chats ou discussions** sont exclus de la sélection et de la migration (y compris via les liens). Les messages/discussions ne sont pas importés.
- Les champs Anytype internes tels que `resolved_layout`, `Origin`, `created_in_context` et `created_in_context_ref` sont filtrés avant la création des colonnes et l’écriture des valeurs. Ne pas rejeter arbitrairement toutes les propriétés de format inconnu : elles peuvent être personnalisées.
- Les bookmarks complets sont transformés en **lien cliquable portant leur titre** ; leurs métadonnées enrichies ne sont plus reproduites. Les blocs bookmark dans les pages suivent la même règle.
- Les colonnes, tableaux et largeurs d’images disposent d’un chemin HTML structuré (moins destructeur que l’aplatissement précédent) ; les couleurs des cellules ne sont pas reprises. Ce chemin n’est **pas encore une garantie de création de blocs natifs Anytwo**.
- Les vidéos YouTube valides sont représentées par une intégration HTML plutôt qu’un lien simple, sous réserve du rendu Anytwo. L’emoji source est envoyé à la création de l’objet et jamais inséré artificiellement dans le contenu.
- Si le Markdown enrichi est refusé, un repli plus simple est tenté ; le bilan signale la perte de présentation. L’import reste non destructif côté Anytype.

## Changements v0.7 — après le premier essai réel

- **Actualisation des listes** : bouton « ↻ Mettre à jour » près de l'espace source. Recharge les espaces Anytype/Anytwo, les objets et types Anytype et les collections de l'espace de destination. La sélection et les destinations sont conservées lorsque les objets existent toujours.
- **Après chaque import** : recharge automatique des listes. L'import renseigne dans le bilan l'ID de l'espace et des collections créés afin que la configuration cible réutilise les **bons identifiants**, et pas seulement des noms identiques.
- **Tableaux dans des colonnes** : correction d'une omission du parcours imbriqué ; la structure HTML de colonne contient désormais les vrais `<table>` des cellules imbriquées, avec leurs données. Le rendu final dépend encore du parser/éditeur Anytwo, à vérifier sur une page de test.
- **Bookmarks intégrés** : recherche du libellé dans le bloc, puis dans le nom de l'objet bookmark référencé, avec lecture de ses métadonnées par l'API locale Anytype en dernier recours. Le lien porte ce titre lorsque la source le fournit.
- **YouTube** : le Markdown Anytwo rendait le code `<iframe>` comme texte. Le convertisseur le sépare maintenant du Markdown et tente un **bloc natif `html`** de l'éditeur au bon emplacement, avant de poursuivre la page. Si l'API refuse ce bloc, il insère un lien cliquable. Le client peut néanmoins afficher le HTML différemment : **la lecture vidéo intégrée n'est pas encore validée sur le client réel**.
- Aucun changement aux modes d'import : l'import simple crée de nouvelles copies. Tester n'écrit rien dans Anytwo.

## Changements v0.8 — reconnaissance des fichiers CSV

- **CSV** : l'import transmet désormais explicitement `Content-Type: text/csv` pour un fichier dont le nom finit par `.csv`, même si Anytype annonçait `application/octet-stream`, `text/plain` ou `application/vnd.ms-excel`.
- **Nom original conservé** : les pièces jointes issues d'une propriété Anytype pouvaient être transmises sous un nom artificiel (par exemple `Documents-<id>`), ce qui empêchait Anytwo d'identifier leur extension. L'importeur tente maintenant de retrouver le vrai nom dans l'inventaire ou dans les métadonnées de l'objet fichier Anytype.
- **Autres formats conservés** : pour `.bat`, `.xls`, `.ics`, `.log` et les autres extensions, un MIME spécifique fourni par Anytype est conservé. Le script ne complète que les types génériques lorsqu'il dispose d'une extension fiable.
- **Vérification CSV après upload** : lorsque l'API de la version Anytwo installée le permet, le script relit la fiche du fichier CSV importé (`GET /v1/spaces/:spaceId/files/:fileId`). Si le MIME enregistré diffère de `text/csv`, le problème apparaît dans le bilan de l'objet. Si cette route est absente, le transfert n'est pas marqué en erreur.
- **Limite** : ces corrections concernent les nouveaux imports. Elles ne modifient pas les fichiers précédemment importés. Le rendu et la prévisualisation dans le client Anytwo doivent encore être confirmés par un essai réel. L'import simple crée de nouveaux objets, il ne faut pas relancer un import vers le même espace sans prendre en compte les doublons.

## Limites et précautions

- **Aucune synchronisation, reprise automatique, résolution de doublons ou annulation.** Import simple = nouvelle copie à chaque lancement.
- Les imports sont limités à **500 objets** et à **100 Mio par fichier** pour prévenir les erreurs de périmètre et les transferts excessifs (limites modifiables dans le code). La préparation lit les documents avant la première création mais ne peut pas anticiper toutes les erreurs d'écriture.
- Les collections et types Anytype ne sont pas équivalents à ceux d'Anytwo : les types sont **convertis en collections** lorsqu'il le faut, les paramètres de vues dynamiques et filtres restent non reproduits.
- Il existe des écarts importants pour les couleurs de fonds, templates, propriétés globales/locales, table des matières, bookmarks enrichis, queries/vues, filtres avancés, collections intégrées, propriétés intégrées dans les pages et discussions. La liste affichée par **Voir plus** n'est pas exhaustive.
- Les blocs sont transposés au mieux, mais **la mise en page exacte et le rendu des médias ne sont pas garantis** (colonnes / tableaux / médias avec HTML à vérifier, toggles non repliables). Certains attributs des relations et les métadonnées système ne sont pas récupérables.
- Les fichiers originaux doivent être disponibles par l'API locale Anytype ; la présence d'une référence ne garantit pas leur téléchargement.
- Un objet source illisible, une propriété refusée ou une API interrompue peut créer un **import partiel**. Consultez le bilan **avant tout nouvel import**, pour éviter des doublons.
- Le mode d'import ne modifie pas la source, mais les clés d'API Anytype accordent l'accès aux espaces approuvés : conservez les fichiers de configuration de votre compte utilisateur.

## Tests effectués

- `python -m unittest discover -s tests -v` : **45 tests** (dont un test d'intégration HTTP contre **deux serveurs locaux simulés** avec écriture des blocs, propriétés et transfert binaire ; neuf tests spécifiques aux métadonnées fichiers et CSV).
- `node --check static/app.js`, `node --check static/i18n.js` et `node --check static/pair.js` : validation syntaxique JavaScript.
- Test automatisé Chromium de l'interface : vérification du dialogue, des sélections, des destinations et du mode simulation.

**Ce qui reste à valider avec vos deux applications** : rendu HTML des colonnes et tableaux enrichis (sans garantie de conversion en blocs natifs), emoji d’icône (`iconEmoji` est tenté mais non confirmé par la documentation), rendu iframe YouTube via bloc natif HTML, dimensions d’images, et  schémas réels des colonnes, chargement des types et collections, création d'un espace et d'une collection, rendu des images via les URI `any://f`, rendu des liens `any://o`, et migration des collections de grande taille. Certains endpoints peuvent avoir évolué depuis la documentation.

## Sources

- API Anytype v2 : https://developers.anytype.io/docs/reference/v2/anytype-api/
- AnyBlock JSON 2.0 : https://github.com/anyproto/any-block/blob/main/format/v2/SPEC.md
- API Anytwo / any v1 : https://docs.any.org/reference/http-api.html
- Markdown Anytwo : https://docs.any.org/database/markdown-import-export.html

## Organisation

- `server.py` : serveur web local et configuration, simulation, import, sauvegarde des bilans.
- `api_clients.py` : clients des API, détection du port, lecture/écriture HTTP, transferts binaires.
- `logic.py` : inventaire, groupes et simulation.
- `migration.py` : découverte des références, correspondances, conversion et rapport.
- `static/` : interface web sans framework JavaScript.
- `tests/` : tests du traitement et des appels HTTP simulés.

## Changements v0.9 — identité et langues

- Projet renommé **Any2Any**. Les sources et destinations restent Anytype et Anytwo.
- Documentation publique en français et en anglais ; avertissement renforcé sur le caractère expérimental des versions alpha.
- Sélecteur de langue FR / EN / DE pour les libellés de l’interface et la fenêtre d’appairage, avec mémorisation locale. Les données des utilisateurs et les messages techniques des API ne sont pas traduits.
- Aucune modification apportée au moteur d’import depuis la v0.8.

**Contrôle de traduction v0.9 :** les affichages FR / EN / DE des deux pages ont été testés avec Chromium hors connexion ; les restrictions réseau de l’environnement ont empêché un scénario navigateur complet contre le serveur local.

## Changements v0.9.1 — aperçu sans API

- L’écran de connexion devient **fermable par une croix dès que les contrôles sont terminés**, même lorsque Anytype ou Anytwo est indisponible. Il reste fermé jusqu’à ce que l’utilisateur clique sur l’indicateur d’état des API.
- En cas d’échec, l’indicateur en haut à droite est **rouge avec un symbole d’avertissement** et la page affiche un bandeau expliquant le mode de consultation. Le sélecteur FR/EN/DE et les informations de compatibilité restent disponibles.
- Aucun test de données ni import ne peut être déclenché lorsque les API ne sont pas toutes les deux accessibles ; les contrôles de l’espace de travail deviennent inactifs.
- Lorsque les API redeviennent accessibles via « Enregistrer et vérifier », l’interface charge les données et réactive les fonctions de migration.
- Le moteur de migration n’est pas modifié. L’identifiant HTTP du client a été actualisé de `Anytype-Anytwo-Importer/0.8` à `Any2Any/0.9.1`.
