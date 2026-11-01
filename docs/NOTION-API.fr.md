# Notion → Anytwo : API, connexion et stratégie de conversion

Analyse du 30 octobre 2026, version d’API retenue : `2026-03-11`.

## Ce qui fonctionne dans cette branche

Le parcours local propose le choix Anytype / Notion. Pour Notion : validation de la connexion, inventaire, ajout par lien, choix du périmètre, arborescence avec sélection et exclusion de branches, lecture des schémas et vues, analyse exportable. Le parcours permet maintenant de lancer un import réel vers Anytwo, avec téléchargement optionnel des fichiers, liens hors arborescence, progression, annulation et bilan exportable. Le lecteur Notion reste en lecture seule. Un modèle réel a été importé et relu dans un espace Anytwo de test dédié ; les limites restantes figurent dans NOTION-IMPORT.fr.md.

Le lecteur est `notion_source.py`, les routes locales sont `notion_routes.py`, l’interface est `static/notion.js`. Le moteur de destination reste `anytwo_backend.py`, commun à Anytype et Notion ; aucun second client d’écriture Anytwo n’est créé.

## Modèle et périmètres

Un espace Notion n’est pas un objet exportable en un appel. La connexion voit le contenu qui lui est autorisé. Une base est un conteneur, avec une ou plusieurs **sources de données**, chacune portant son schéma et ses pages (lignes). Les pages contiennent des blocs, parfois imbriqués. Les bases liées réutilisent leur source originale : autoriser seulement la page qui les affiche ne suffit pas nécessairement ; partager aussi la base originale. [Modèle des bases](https://developers.notion.com/guides/data-apis/working-with-databases).

L’interface présente l’espace associé à la connexion, puis une arborescence : pages, bases, sources de données et pages de ces sources. Une connexion interne concerne un seul workspace ; plusieurs espaces demanderont des connexions distinctes. L’API ne fournit pas le détail fiable des autorisations explicites contre les autorisations héritées. Les racines affichées sont donc les éléments dont aucun parent n’est connu dans l’inventaire accessible ; un parent absent n’est jamais inventé.

Le parcours commence par une popup de connexion Notion et Anytwo. Un jeton disponible est contrôlé automatiquement ; sans jeton, le formulaire s’affiche. La popup affiche ensuite la récupération du premier niveau. La liste reste sur « Choisir un espace… » sans présélection ; le choix explicite de l’espace affiche les données déjà préparées. « Mettre à jour » relance la recherche avec un indicateur, sans afficher prématurément un état vide. « Mettre à jour » relit cet inventaire. Déplier un élément charge ses enfants à la demande, sans parcourir tout son contenu à l’avance. Cocher une branche inclut tous ses descendants ; décocher une sous-branche les exclut, même si elle n’est pas entièrement dépliée. Une sélection plus profonde peut être réincluse. « Tout sélectionner dans cet espace » prend les racines accessibles et leurs descendants, pas le contenu privé non autorisé. L’analyse matérialise cette sélection et compte les pages obtenues.

La recherche n’est pas un inventaire garanti exhaustif : son index peut être en retard. L’ajout manuel d’une URL ou d’un identifiant permet de retrouver un élément connu. L’outil ne promet donc pas un export complet du workspace. [Limites de recherche](https://developers.notion.com/reference/search-optimizations-and-limitations).

## Connexion : ce qu’il faut préparer

1. Dans le portail développeur Notion, créer une **connexion interne** pour l’espace concerné. Sa création demande les droits de propriétaire de workspace. Lui donner la capacité **Read content**, sans création ni modification de contenu. La lecture des commentaires sera une capacité distincte si leur archivage est développé.
2. Autoriser les pages et bases via **Content access**, ou ajouter la connexion depuis le menu de la page Notion. L’accès aux enfants est hérité ; autoriser aussi les bases originales des vues liées.
3. Lancer `demarrer.bat`, puis choisir **Notion** dans la fenêtre d’accueil (interface locale à partir du port 8766). Saisir le jeton secret dans le champ local et cliquer sur **Valider la connexion**. Ne pas envoyer le jeton dans une conversation, une capture ou un dépôt Git.
4. Choisir explicitement un espace, attendre le chargement des racines, puis cocher tout l’espace ou déplier des branches pour choisir les éléments et lancer leur analyse. Une page ou base connue peut aussi être ajoutée par son lien. Une page de test avec propriétés, relations, fichiers et vues aidera à vérifier les différences réelles.

La connexion appelle `/users/me` puis la recherche de contenu. Aucun jeton n’est renvoyé au navigateur par les réponses API. Lorsqu’un jeton est disponible, un message remplace le champ de saisie ; « Oublier le jeton » efface la session et la copie mémorisée, puis réaffiche le champ. Par défaut il reste en mémoire du processus ; la mémorisation facultative utilise la protection Windows DPAPI dans la configuration du profil Notion. La révocation dans Notion reste possible indépendamment.

Un jeton d’accès personnel existe aussi, mais une connexion interne en lecture seule permet de limiter explicitement le périmètre. OAuth sera pertinent pour une diffusion multi-utilisateur ultérieure ; il n’est pas nécessaire pour ce premier usage personnel. [Connexion interne](https://developers.notion.com/guides/get-started/internal-connections), [capacités](https://developers.notion.com/reference/capabilities), [types de connexion](https://developers.notion.com/guides/get-started/quick-start).

## Appels utilisés et prochaines lectures

| Besoin | API |
|---|---|
| Identité | `GET /users/me` |
| Recherche | `POST /search` — lecture malgré POST |
| Conteneur et schéma | `GET /databases/{id}`, `GET /data_sources/{id}` |
| Lignes d’une source | `POST /data_sources/{id}/query` — lecture |
| Métadonnées et contenu | `GET /pages/{id}`, `GET /blocks/{id}/children`, récursivement |
| Vues | `GET /views?database_id=…`, puis `GET /views/{id}` |
| Propriétés complètes, importeur | `GET /pages/{id}/properties/{property_id}`, avec pagination |

Les listes sont paginées, y compris les enfants de blocs. Une limite ou un curseur bloqué produit une erreur explicite plutôt qu’un inventaire présenté comme complet. Le prototype plafonne une sélection à 2 000 pages et un parcours à 5 000 blocs. Les quotas Notion dépendent désormais du plan et du workspace ; le lecteur espace les requêtes et traite les réponses 429. Les longues attentes demandent une nouvelle tentative. [Requête de source](https://developers.notion.com/reference/query-a-data-source), [quotas](https://developers.notion.com/reference/request-limits).

## Correspondances prévues avec Anytwo

| Notion | Proposition pour Anytwo / point à vérifier |
|---|---|
| Page, titre, icône, couverture | Page et métadonnées ; récupérer les fichiers concernés |
| Source de données | Supertag propriétaire de son schéma ; chaque ligne reçoit ce supertag |
| Texte, listes, cases, titres, toggles | Blocs natifs via le moteur commun ; vérifier les annotations |
| Colonnes, tableaux, callouts | Adapter à la structure native, contrôler le rendu |
| Select / multiselect | Préserver vocabulaire et couleurs, avec correspondance de palette |
| Status | Choix simple ; conserver en archive les groupes du workflow Notion |
| Nombre | Valeur inchangée, format monétaire avec devise, pourcentage et séparateurs natifs ; formats inconnus archivés |
| Date | Respecter heure, fuseau et intervalle ; ne pas réduire silencieusement à un jour |
| Relation | Remapper les pages, restreindre au handle du supertag cible ; schémas de dépendance sans leurs membres hors sélection |
| Formula | Résultat figé ; expression archivée, sans prétendre recréer le calcul actif |
| Rollup | Définition native à adapter : relation et propriété cible remappées, opérateur compatible ; archiver le résultat si le calcul ne peut pas être traduit |
| Personnes, auteurs, identifiant unique | Valeurs archivées ; ne pas inventer de comptes ni d’auteurs Anytwo |
| Image, fichier, audio, vidéo | Télécharger puis utiliser les blocs et pièces jointes Anytwo, préserver noms et dimensions disponibles |
| Embed / bookmark / mention | Réécrire les liens internes, utiliser un embed si compatible, sinon signaler l’adaptation |
| Bloc synchronisé | Original et références synchronisés dans Anytwo ; aucun lien vivant avec Notion |
| Boutons, automatisations, formulaires, permissions, historique | Pas de recréation active prévue ; signalement et métadonnées quand accessibles |
| Blocs inconnus / unsupported | Avertissement explicite, jamais remplacement inventé |

Ces choix sont des décisions de conversion. Les types exacts accessibles sont décrits dans [les blocs Notion](https://developers.notion.com/reference/block) et [les propriétés de page](https://developers.notion.com/reference/page-property-values). La destination est contrainte par [l’éditeur Anytwo](https://docs.any.org/types/editor.html) et [ses types et propriétés](https://docs.any.org/database/types-and-properties.html). Le soulignement et les couleurs de texte/fond demandent notamment un contrôle des capacités du pont Markdown cible ; une représentation HTML littérale serait incorrecte.

### Vues et propriétés affichées

L’API Notion actuelle possède une API de vues : lire leur configuration permet d’étudier le type, les filtres, tris, propriétés visibles et leur ordre. Une vue n’est pas un nouveau supertag ; elle doit viser le supertag de sa source. Les vues liées et leur placement dans la page nécessiteront une vérification spécifique du contenu retourné par l’API. Une condition non traduisible doit faire refuser la conversion de la vue entière, afin de ne pas élargir silencieusement son résultat. [Guide des vues](https://developers.notion.com/guides/data-apis/working-with-views), [lecture d’une vue](https://developers.notion.com/reference/retrieve-a-view), [liste des vues](https://developers.notion.com/reference/list-views).

### Exhaustivité et fichiers

La lecture simple d’une page peut tronquer certaines propriétés : relations et personnes, mentions dans les titres/textes, calculs. L’import lit les éléments de propriété avec pagination avant les écritures et signale les limites des formules/rollups ; une analyse simple peut rester partielle sur ces valeurs. [Valeurs des propriétés](https://developers.notion.com/reference/page-property-values).

Les fichiers hébergés par Notion utilisent des URL temporaires (environ une heure). Il faut les relire au moment du transfert, télécharger puis téléverser dans Anytwo, et ne pas conserver leur URL comme pièce jointe définitive. Aucun en-tête d’autorisation Notion ne doit être envoyé à un hébergeur de fichiers externe. [Fichiers Notion](https://developers.notion.com/reference/file-object).

## Validation avant un vrai import

Le mode `--demo` vérifie le parcours sans appeler Notion ni Anytwo. Les tests couvrent pagination, autorisations de routes en lecture seule, erreurs sans secrets, invalidation des sélections et analyse. La connexion réelle et le convertisseur ont été vérifiés sur le modèle demandé par l’utilisateur, dans un espace Anytwo dédié ; la validation visuelle des rendus reste à faire dans le client.

La validation utilise une recherche limitée à un élément, indépendamment de l’inventaire complet. Celui-ci est chargé après le choix explicite de l’espace, puis peut être relu avec Mettre à jour. Les opérations affichent un compteur d’attente ; connexion et inventaire ont des budgets respectifs de 5 et 90 secondes ; le navigateur limite son attente à 7 secondes pour la connexion et à 120 secondes pour les autres appels.


## Parents intermédiaires et analyse longue

Les parents de type bloc (toggle, colonne, etc.) sont remontés par `GET /blocks/{id}` pour retrouver la page ou base ancêtre, même si le bloc n’est pas un élément de la recherche. Les ancêtres lisibles absents de l’index sont récupérés. Un parent inaccessible ou une chaîne cyclique reste signalé après un petit titre grisé « Autres éléments accessibles qui ne sont pas des pages de premier niveau ». Cette séparation est toujours visible et ne se replie pas lors d’une sélection. Ces éléments participent au même préchargement et à la même lecture à la demande que les autres branches. [Parents Notion](https://developers.notion.com/reference/parent-object), [lecture d’un bloc](https://developers.notion.com/reference/retrieve-a-block).

L’analyse est un travail en arrière-plan, conservé uniquement en mémoire du serveur. L’interface interroge son état séparément et affiche près du bouton l’étape, le temps écoulé et le nombre de requêtes ; une erreur reste visible à cet endroit. L’annulation interrompt le parcours après la requête réseau en cours (délai réseau maximal de 25 secondes). Le budget total est de 900 secondes ; un dépassement produit un résultat d’erreur explicite, sans présenter une analyse partielle comme complète. Les blocs lus pour établir la sélection sont réutilisés pendant l’analyse, dans un cache borné à cette opération. La lecture des propriétés utilise le même instantané de sélection ; les limitations d’exhaustivité restent signalées.


## Réactivité de la connexion et préchargement

La connexion utilise `https://api.notion.com`, sans détection du client Notion installé. La validation du jeton a un budget de 5 secondes ; le navigateur abandonne son attente après 7 secondes. Le chargement de l’inventaire est distinct et se poursuit avec un indicateur, sans verrouiller toute l’interface. Un serveur occupé renvoie une réponse explicite plutôt que de laisser une nouvelle validation attendre son verrou réseau. [Authentification cloud](https://developers.notion.com/reference/authentication).

Les branches sont ensuite préchargées en arrière-plan, en commençant par les niveaux supérieurs. Cette anticipation est bornée à 60 branches ou deux minutes, avec une seule requête en vol ; elle s’interrompt au profit des actions de l’utilisateur. Les branches prêtes se déplient immédiatement sans nouvel appel réseau. Une branche encore en lecture est réutilisée plutôt que téléchargée deux fois. Les résultats restent dans la session et sont invalidés par « Mettre à jour ». Les branches non préchargées ou en erreur restent consultables à la demande. Ce cache concerne la navigation ; l’analyse relit les données sélectionnées.

« Tester » produit un bilan en lecture seule ; il n’écrit pas dans Anytwo. La destination est chargée après le choix du workspace si Anytwo est disponible et peut être actualisée. « Importer » crée une copie réelle dans Anytwo, sans modifier Notion. Une interruption conserve les objets déjà créés ; un nouveau lancement ordinaire crée une autre copie.


## Parallélisation et reprise des grandes analyses

Le parcours lit jusqu’à quatre pages simultanément. Un régulateur unique espace les départs d’environ 0,35 seconde, y compris les nouvelles tentatives : quatre tâches n’autorisent donc pas quatre fois plus de trafic. Les pauses `Retry-After` sur 429 ou 529 sont communes à tous les lecteurs ; les attentes restent annulables. Les limites courantes sont de 180 requêtes/minute (600 sur Business/Enterprise), avec une limite séparée pour les requêtes de source. Le mode conservateur est utilisé sans supposer le forfait. [Quotas Notion](https://developers.notion.com/reference/request-limits).

Un cache de lecture partagé évite les demandes identiques dans une analyse, y compris celles lancées simultanément. Après erreur, dépassement ou annulation, il reste réutilisable pour la même sélection pendant cinq minutes. La reprise est signalée dans le rapport : elle utilise l’instantané récent, pas une relecture complète de chaque objet. « Mettre à jour », l’ajout manuel d’un élément, une reconnexion ou un changement de sélection invalident la reprise. Une analyse réussie efface ce point de reprise. Le cache reste en mémoire et est borné à 32 Mio ; les réponses excédentaires restent lisibles mais ne sont pas conservées. Aucune clé n’est enregistrée dans ce cache, aucun fichier de reprise n’est créé.

Le délai de quinze minutes est une borne de sécurité, pas une estimation de durée. Une grande sélection peut nécessiter plus de trois minutes au débit autorisé. La concurrence masque une partie de la latence réseau ; elle ne supprime pas les quotas. Aucun gain précis n’est promis sur le compte réel avant mesure.

Le statut API en haut à droite rouvre à tout moment la popup. Elle permet de modifier le jeton Notion, d’oublier sa mémorisation et de régler/tester le port Anytwo. L’espace reste explicitement choisi par l’utilisateur. L’écran principal comporte « 01 · Choix des éléments à importer » et « 02 · Configuration de l’import ». Le second volet propose la destination, les options fichiers et liens hors arborescence, puis Tester (sans écriture) et Importer (copie réelle vers Anytwo).

La connexion validée s’affiche explicitement en vert et son bouton n’est plus réactivable. Le chargement initial utilise une popup dédiée et fermable ; fermer la popup laisse la recherche continuer en arrière-plan. Les réglages API peuvent être rouverts pendant ce chargement sans être refermés automatiquement à son achèvement. Voir aussi ANYTWO-RELATIONS-ROLLUPS.fr.md et SOURCE-FIXTURES.fr.md.
