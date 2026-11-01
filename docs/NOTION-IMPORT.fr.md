# Contrat de conversion Notion vers Anytwo

## Sélection et lecture

La navigation propose trois niveaux : racine (0), niveau 1, niveau 2. Les bases et sources de données comptent comme des niveaux structurels. Les éléments plus profonds ne sont ni affichés ni préchargés par la navigation, même si la recherche initiale les a déjà recensés. La racine d’un élément au parent inaccessible reste présentée dans la séparation des autres éléments accessibles.

Sélectionner une branche inclut tous ses descendants accessibles, sans limite de profondeur de sélection. L’analyse de compatibilité continue à lire ces descendants : la limite de navigation accélère la préparation du choix, pas une analyse complète du contenu. Les limites de volume et l’annulation restent applicables. L’inventaire initial utilise toujours la recherche Notion et la reconstruction des parents ; cette limite ne supprime pas ces requêtes.

## Destination

Après Vérifier Anytwo, l’espace portant exactement le nom du workspace Notion est proposé s’il est unique. Sinon, créer un espace avec ce nom est proposé ; le nom est modifiable. Plusieurs espaces homonymes nécessitent un choix explicite. L’utilisateur peut choisir un autre espace existant. Aucun espace n’est créé pendant cette configuration.

Une page ordinaire devient une page, sans supertag générique « Page » portant les propriétés de bases sans rapport. Chaque source de données devient une collection avec son supertag, ses propriétés et ses options/couleurs ; la définition est aussi créée pour une base vide. Tous ses membres reçoivent ce supertag. Une base Notion à plusieurs sources produit plusieurs collections pour respecter les schémas distincts. Pour une seule source, reprendre le nom de la base ; pour plusieurs, distinguer les collections par le nom des sources, en conservant les identifiants source pour éviter les collisions.

Même pour une seule base sélectionnée, créer une collection et son supertag : ne pas proposer la fusion des membres dans une collection existante dont le schéma pourrait être incompatible. Un nouvel import ne doit pas réutiliser une collection sur le seul critère de son nom ; une future reprise nécessitera une correspondance d’identifiants source/cible.

Une base intégrée à une page donne ses collections et membres, puis une vue inline à l’emplacement du bloc source. Les filtres, tris et propriétés visibles sont remappés. Une vue ne crée pas une nouvelle collection à chaque occurrence. Une condition impossible à traduire doit être signalée, sans remplacer discrètement la vue par une vue non filtrée.

## Ordre des opérations du convertisseur

1. Résoudre ou créer l’espace et enregistrer les correspondances d’identifiants.
2. Créer les collections/supertags et les propriétés simples/options, y compris pour les sources vides.
3. Créer les pages et membres avec leur appartenance ; importer les valeurs simples et les fichiers dédupliqués par identité/contenu, pas par nom seul.
4. Remapper les propriétés de relation et leurs valeurs ; créer les rollups avec les identifiants cible et vérifier les agrégations compatibles.
5. Convertir les blocs, liens internes et vues inline après disponibilité des identifiants. Conserver les blocs vides et les médias intégrés.
6. Produire un rapport des adaptations, pertes, références hors périmètre et réglages archivés.

Les écritures passent par anytwo_backend.py, moteur commun ; aucune écriture HTTP Anytwo dans le lecteur Notion. Le bouton Importer lance le convertisseur en tâche de fond, avec le même verrou de destination que les imports Anytype. Le mode démo refuse toute écriture réelle.

## Compatibilité

Le cadre visible avant l’analyse présente les limites générales. Le bilan détaillé compte séparément les blocs, propriétés et vues effectivement détectés. Table, liste, tableau par groupes et galerie sont des candidats à adaptation, pas une garantie de conversion validée. Calendrier reste à vérifier. Graphiques/statistiques, cartes, timeline/chronologie, formulaires et dashboards ne sont pas reproduits visuellement à ce stade ; conserver leurs données et archiver leurs définitions. Un journal construit avec des pages et dates reste importable comme tel ; ne pas confondre ces données avec une disposition chronologique.

La fenêtre « Limites connues de la migration » Notion présente les adaptations suivantes :

- Vues : formats graphique, fil d’actualité, carte et chronologie non reproduits ; calendrier à étudier. Couleurs conditionnelles, sous-éléments et automatisations non reproduits.
- Propriétés : formules figées sans recalcul ; boutons non reproduits ; texte riche adapté en texte brut ; fichiers et médias conservés sous forme de liens vers les pièces jointes récupérées.
- Pages : aperçu visuel des liens, boutons, fil d’Ariane et onglets non reproduits ; colonnes de blocs au-delà de quatre à adapter ; dates de rappel non conservées ; couverture adaptée en image dans le contenu ; couleurs de texte/fond et soulignement non conservés.
- Historique non importé. Imports à étudier : wikis et calendriers.

Les relations, rollups compatibles et blocs synchronisés natifs Anytwo sont pris en charge et ne figurent plus comme limitations générales. Le bilan de chaque import conserve les avertissements précis lorsqu’une configuration particulière ne peut pas être reproduite.

Références : https://developers.notion.com/reference/create-view et docs/ANYTWO-RELATIONS-ROLLUPS.fr.md.

## Première version opérationnelle

Le lecteur termine la lecture des propriétés paginées (titres, textes, personnes, relations, formules et rollups) avant de créer la destination. La conversion conserve les types numériques, booléens, dates, choix et couleurs, les références internes et l’appartenance aux collections. Les médias sont téléchargés sans transmettre le jeton à leur hébergeur, avec un plafond de 100 Mo par fichier ; les adresses réseau privées et les redirections vers ces adresses sont refusées. Les fichiers sont réutilisés par nom et contenu, pas par nom seul. Les images, lecteurs audio et vidéos YouTube utilisent le dialecte natif déjà employé par l’importeur Anytype. Les légendes d’image utilisent l’extension image-caption et restent attachées à l’image ; le texte de légende cible est en texte brut.

Les blocs vides, listes, cases, titres, toggles, colonnes, tableaux, code et équations sont convertis. Les callouts utilisent l’enveloppe native any:callout, avec leur cadre, leur icône et leur contenu imbriqué. Le soulignement et les couleurs de texte/fond restent signalés comme perdus. Le sommaire est reconstruit comme une liste de liens vers les identifiants réels des blocs de titre ; il reste statique. Les blocs synchronisés deviennent des originaux et références natifs Anytwo, partagés entre les occurrences importées ; ils ne restent pas synchronisés avec Notion. Si l’original Notion est hors sélection, sa première occurrence sélectionnée devient l’original Anytwo. Les liens vers les pages enfants sont conservés à leur emplacement source. Aucun lien artificiel vers la page parente n’est ajouté ; les favoris et la barre latérale Notion ne sont pas reconstruits.

Les vues de collection sont enregistrées avec leurs filtres, tris et propriétés visibles compatibles. Le client cible limite actuellement les dispositions inline : table et tableau sont adaptés en liste avec avertissement, galerie conservée. Un filtre non traduisible empêche la création de cette vue ; un lien vers la collection est présenté à sa place. Les paramètres originaux sont conservés dans le bilan. Les liens entre bases sont remappés vers la collection si la source est unique ; une référence ambiguë à une base multisource reste signalée.

Les formules sont des résultats figés typés, avec expression archivée. Les rollups somme et valeurs originales sont configurés en natif si leur relation et propriété cible sont disponibles ; sinon résultat et définition sont archivés sous forme figée. La persistance de la configuration est vérifiée par API, mais le recalcul visuel dans le client n’est pas validé automatiquement. Les formats monétaires (dont EUR), pourcentages et séparateurs numériques sont traduits en descripteurs natifs sans changer les valeurs. Les intervalles et fuseaux de date, groupes de statuts et textes enrichis de propriétés demandent encore une adaptation signalée. Les propriétés fichiers deviennent des liens vers les pièces jointes récupérées.

Chaque création est suivie d’un checkpoint dans le profil actif, sous reports/notion-<id>.json (APPDATA/any2any pour la version commune) ; le bilan contient les identifiants source/cible, les définitions de propriétés/vues et les pertes signalées, sans jeton API. Ne pas diffuser ces rapports sans vérifier les données personnelles qu’ils contiennent. L’annulation garde les objets déjà créés et rend le bilan disponible. Le bouton Importer lance un nouvel import, sans mise à jour ni reprise automatique ; relancer crée des copies supplémentaires. Les POST répétés avec le même request_id ne lancent pas un deuxième travail dans la même session.

## Vérification réelle

Le modèle « Modèle de test — Any2Any » de Sri / Test pour Anytwo a été importé dans l’espace « Test import Notion — Any2Any 2026-10-31 19-49-19 » : 7 pages, 2 collections et 4 fichiers distincts. Relecture des corps (toggles, médias et inline views), des propriétés, des dates, des valeurs numériques/booléennes et des relations réussie. Aucun contenu source n’a été modifié. Le premier essai a révélé des tris de vues null ; après correction, le même espace a été repris sans recréer les pages ni les propriétés, et les fichiers ont été réutilisés. Les adaptations attendues sont listées dans le bilan privé.

L’utilitaire tools/import_notion_fixture.py est limité à ce modèle et requiert --apply pour écrire. Sans ce flag il effectue seulement la prélecture ; --resume réutilise le bilan local de cet essai technique. Cette reprise explicite n’est pas encore proposée par l’interface d’import générale.

## Vérification des formats du client

Après le retour utilisateur sur le modèle importé, le convertisseur réel du client desktop installé a été exécuté dans un DOM isolé, sans réseau et sans lancer l’application. Les bibliothèques ont été lues dans l’exécutable installé (assets Brotli LexicalMarkdownEditor-hfMXhO7O.js, useSpellingHighlights-PDgIE7KF.js et format-z9cldY3U.js) ; aucune modification de l’installation. Les copies d’analyse et les résultats restent dans reports/client-inspection, hors Git.

Le défaut de gras/italique/barré venait des espaces inclus dans les annotations source : **Gras ** n’est pas un marqueur valide pour ce client. Les espaces sont désormais sortis des délimiteurs. La relecture réelle du modèle corrigé confirme les bits de format bold/italic/strikethrough, un nœud callout, deux extensions image-caption canoniques, l’original synchronisé et sa référence vers le bloc API réel, ainsi que les liens de sommaire.

Le soulignement reste indisponible par le pont Markdown actuel : le test montre aussi qu’un paragraphe HTML avec une balise u est conservé comme texte littéral, sans soulignement. Ne pas contourner cela avec du faux texte Unicode ou un tableau artificiel. Cette perte reste signalée. Les objets supports de vues sont sans nom, comme les supports natifs ; leurs données restent présentes, mais ils ne sont plus présentés comme des pages « Vues Anytype ».

Les références de synchronisation et de sommaire sont finalisées après création des corps, via PATCH des blocs ; ne pas refaire un PUT global ensuite, au risque de changer les identifiants ciblés. Les identifiants des blocs créés en lot contiennent « : » ; cette version de la route PATCH exige que ce caractère légal de segment reste non encodé, sinon elle répond blocks.not_found.

La page modèle de l’espace de test fourni a été corrigée sur place, avec sauvegarde préalable du Markdown et des supports techniques dans reports/before-notion-native-repair-*.json. Aucune page, collection ou pièce jointe supplémentaire créée, aucun contenu Notion modifié. tools/repair_notion_fixture.py limite cette opération au modèle et à cet espace précis, avec --apply explicite.

## Relations, rollups et nombres

Les collections sont toutes créées avant leurs propriétés. Une relation vers une source Notion est limitée au supertag cible via xFormat.relation.targetTypes : cette liste contient le handle xKey de la collection, pas son identifiant ni son nom. Les identifiants restent utilisés pour le propriétaire des propriétés et pour les références de valeurs. Si seule la collection portant la relation est sélectionnée, les schémas cibles accessibles sont lus et créés sans récupérer leurs membres ; l’option de liens contrôle toujours l’ajout de pages hors sélection. Une cible inaccessible ou ambiguë donne une propriété texte avec références archivées et avertissement, plutôt qu’une relation faussement non restreinte.

Les sélecteurs de rollup ne proposent que les relations aux cibles résolues. Le titre cible est identifié par ownerId = identifiant de la collection cible et propertyId = any.name. Ce couple doit aussi être utilisé pour le choix affiché dans l’éditeur ; any / name ne correspond pas au choix natif. Les identifiants de propriété Notion sont comparés après décodage de leur échappement URL, avec priorité à l’identité plutôt qu’à un ancien nom.

Les propriétés numériques conservent le kind number. Le descripteur devient currency avec config.currency = EUR pour euro, percent pour percent, ou number avec config.separators = true pour number_with_commas. Les autres devises connues sont traduites vers leur code ISO ; les formats inconnus restent archivés et signalés. Les valeurs ne sont ni converties dans une autre devise ni multipliées pour un pourcentage. Les filtres et tris de ces propriétés restent numériques.

Le 1 novembre 2026, le nouvel import du modèle dans Sri a été corrigé en place : restriction de Projet vers Projets de test, formats EUR de Budget et Prix, configurations de Noms liés et Budget lié, et suppression des deux liens parents générés dans le modèle et sa sous-page. Les propriétés ajoutées manuellement par l’utilisateur sont restées intactes. Sauvegarde privée avant modification et vérification que les valeurs de toutes les propriétés importées sont inchangées. Aucune réécriture globale des pages : seuls les blocs de liens artificiels ont été retirés, préservant les identifiants utilisés par sommaires et blocs synchronisés.

Les fonctions de choix et de calcul du client installé ont été exécutées dans le DOM isolé sur les définitions réellement relues après correction : Projet est proposé avec un seul supertag cible, les propriétés Name et Budget sont reconnues, les noms des projets sont calculés et les sommes sont 100, 180 et 0 ; l’affichage numérique est currency / EUR. Les résultats restent dans reports/client-inspection/property-check-results.json. L’utilitaire tools/repair_notion_properties.py requiert --space-id et --apply pour écrire ; il se limite à l’import du modèle identifié par son bilan, sauvegarde les définitions et retire uniquement les liens parents reconnaissables générés par l’importeur.


## Réduction des lectures et reprise (1 novembre 2026)

Les titres/textes courts, petites listes de personnes, relations explicitement complètes et résultats numériques/de date déjà fournis par Notion ne sont plus systématiquement relus propriété par propriété. Les listes potentiellement tronquées, les relations sans preuve de complétude et les calculs complexes restent relus avec pagination. Les lectures complémentaires de propriétés se font avec quatre workers, sous le plafond global de débit existant.

Les branches décochées sont écartées avant leur parcours, sans requêter leurs bases ni lire leurs pages pour les retirer ensuite. Une inclusion explicite sous une branche exclue conserve sa priorité. Les métadonnées de schémas cibles nécessaires aux relations restent récupérées sans leurs membres.

Navigation, analyse et import partagent un cache en mémoire de 32 Mo maximum, renouvelé au plus tard après 30 minutes. « Mettre à jour » et une nouvelle connexion invalident les lectures. Après une interruption pendant la lecture, relancer la même sélection avec les mêmes options et destination sous 30 minutes réutilise son cache, sans fermer l’application. Ce mécanisme reprend les lectures retenues en mémoire ; il ne constitue pas une reprise automatique des écritures ni une synchronisation. Si des objets ont déjà été créés, le message le signale et demande de consulter le bilan avant relance pour éviter les doublons.

Le suivi affiche la phase, les pages/blocs repérés, les requêtes par catégorie et les lectures réutilisées. Les tentatives réseau, y compris les nouvelles tentatives après limitation, sont comptabilisées. Les métriques accompagnent les bilans enregistrés de l’import. L’expiration du budget ou d’une requête n’est plus présentée comme une absence de connexion Internet. La limite globale de lecture demeure de quinze minutes par lancement ; le gain recherché est une réduction du nombre d’appels, pas une augmentation aveugle du débit.

### Image de l’espace

Le client Anytwo accepte une image d’espace : téléchargement public sans jeton, attachement à l’objet index de l’espace créé, puis PATCH iconCid avec l’URI any://f de ce fichier, comme son sélecteur natif. L’espace est enregistré avant cette opération optionnelle ; un échec de l’image ne bloque pas les pages. Un espace existant conserve son icône.

La connexion actuelle utilise un jeton interne Notion. GET /users/me expose le nom de l’espace, mais sa documentation ne fournit pas son image. avatar_url désigne l’intégration, pas l’espace : il n’est jamais réutilisé à sa place. L’importeur peut transmettre workspace_icon si les métadonnées de connexion le fournissent ; sinon il signale explicitement l’indisponibilité et conserve l’icône par défaut. La récupération automatique de l’image avec le jeton actuel reste donc indisponible, et n’est pas présentée comme validée.


## Vues liées, callouts et icônes (1 novembre 2026)

Un child_database n’est pas toujours une base propriétaire : les vues liées inspectées ont data_sources vide, mais chaque vue renseigne son data_source_id. L’importeur résout ce schéma et utilise les vues propres à l’emplacement, sans créer de supertag pour le conteneur de vues. Si la base est hors arborescence, ses membres ne sont ajoutés qu’avec l’option des éléments liés ; son schéma reste nécessaire à la vue. Les bases is_inline=false deviennent des liens vers leur collection ; elles ne sont plus remplacées par une vue que le client déplace hors du callout.

Les propriétés retirées du schéma mais encore référencées dans la présentation d’une vue sont ignorées avec avertissement. Un filtre ou tri visant une propriété introuvable reste bloquant pour cette vue. Les quick_filters non vides sont combinés au filtre principal ; les sélections multiples restent des listes plates. Une vue groupée peut être adaptée en liste, avec avertissement, tout en conservant son filtre et son tri. Une vue de collection non convertible ne fait plus disparaître les autres vues compatibles.

Les callouts sans texte propre commencent directement par leurs blocs enfants, sans paragraphes vides générés. Les paragraphes vides réellement présents dans la source restent conservés. Les icônes des pages et collections utilisent le format natif icon:v2 ; les emoji composés (par exemple le chef cuisinier) restent un seul graphème. Les images de collection sont transférées lorsque les fichiers sont activés. Les icônes nommées Notion connues ont une table de correspondance déterministe vers des emoji ; aucune reconnaissance d’image ni appel IA. Les icônes de propriétés et vues sont transmises quand leur métadonnée est fournie par l’API ; l’API actuelle peut omettre ces informations.

Vérification en lecture seule sur les pages signalées de Gastronomie, puis rejeu hors ligne avec toutes les écritures simulées : un lien Cave dans le callout, une vue inline dans Recettes et Idées repas, trois dans le tableau de bord de la cave et Le bar, sept vues enregistrées pour Base recettes avec leurs filtres rapides. Le convertisseur du client installé confirme trois callouts sans paragraphe vide initial, le lien objet Cave dans son callout et le chef comme un seul graphème natif. Cela ne remplace pas la vérification visuelle du prochain import. Aucun nouvel import et aucune correction en place de Sri n’ont été lancés.


## Regroupements de collections, relations Two-way et moyennes (1 novembre 2026)

Les regroupements de collections ne sont plus aplatis comme ceux des vues inline. Les vues tableau/liste/galerie utilisent query.groupBy = {propId: …} et query.anyUi.group ; les Kanban utilisent layoutSettings.boardColumns. Les identifiants des propriétés sont remappés, avec ordre des groupes et hideEmpty. Les vues inline gardent leur adaptation signalée en liste lorsque le client n’offre pas cette présentation.

Les filtres texte Notion « contient / ne contient pas » sont convertis en regex littérales insensibles à la casse et en conditions natives du client. Cette conversion est propre à Notion ; les réserves de collation de l’import Anytype sont inchangées. Les collections Notion nouvellement créées sont ciblées par leur appartenance native, sans injecter une liste de centaines d’identifiants dans le filtre affiché. Une vue Notion sans nom significatif reçoit un libellé de son format : notamment Tableau Kanban au lieu d’Untitled. Les formats non importables, dont graphique, restent exclus et signalés.

Les relations dual_property sont appariées après création de toutes les propriétés, avec xFormat.anyui.inverseOwner et inverseProperty de chaque côté. Les identifiants Notion échappés sont décodés pour retrouver la propriété inverse. Aucun doublon de propriété inverse n’est inventé ; une référence absente ou incohérente est signalée. Ces paramètres activent le mode Two-way dans le client, indépendamment des valeurs de relations importées.

Les rollups prennent maintenant en charge average, ainsi que min/max/median/range et les décomptes compatibles, en plus de sum et original. Une moyenne est une propriété native object/rollup avec ses identifiants de relation et de propriété cible remappés ; le résultat JSON source n’est pas écrit comme valeur texte. Les références propres à chaque objet limitent le calcul aux objets réellement liés.

Validation sur le bilan utilisateur : 12 vues Cave conservées sur 13, graphique exclu ; LPB et Kanban présents, paramètres de groupes reconnus par le parseur du client. Requête LPB exécutée en lecture seule : six résultats dans Notion et six dans Anytwo. Les fonctions réelles du client reconnaissent les deux sens appariés et reproduisent 53 moyennes numériques du bilan source, dont 11,5. Suite : 252 tests Python et huit scénarios frontend. Aucun import réel ni modification de l’espace existant.


## Présentation des galeries et ouverture des pages

Le réglage cover_aspect=contain devient layoutSettings.galleryFitImage=true ; cover devient false. Ce paramètre est conservé dans les vues de collection et inline. Le mode cible est side-peek par défaut, y compris lorsque l’API Notion omet son mode d’ouverture ; seules des métadonnées explicites de pleine page donnent full-screen. Aucun mode central alternatif n’est créé. Les réglages appliqués restent ceux stockés par le client Anytwo (openMode et galleryFitImage).
