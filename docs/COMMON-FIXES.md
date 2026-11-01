# Suivi des correctifs communs

Base reprise : main / 0.9.3 / 684c8867ac67b6f4752743d23c88040103b19a98.

| Correctif | Commit main | Repris dans Notion | Validation |
|---|---|---|---|
| État publié 0.9.3 (propriétés, vues, fichiers et archives Anytype) | 684c886 | Oui, base du worktree | 137 tests de référence |

Pour chaque futur correctif, noter le commit d’origine, les adaptations éventuelles et les tests effectués. Une modification non commitée ou un message dans une autre conversation ne signifie pas qu’elle est intégrée ici. Éviter de dupliquer le même correctif avec des historiques divergents ; privilégier un commit commun indépendant puis la reprise de main.

## Préparation actuelle

- Profils et lanceurs : propres à develop/notion ; pas de reprise prévue dans la stable avant l’application commune.
- Frontière anytwo_backend.py : refactoring compatible, isolé dans un commit distinct pour une éventuelle reprise dans main. Pas encore intégré dans main.
- Validation de préparation : 140 tests réussis, vérification syntaxique JavaScript et deux serveurs de démonstration simultanés avec configuration stable témoin inchangée. Aucun import réel effectué.

## Lecteur Notion et analyse

- Connexion, inventaire et analyse Notion : spécifiques à develop/notion ; aucune écriture de migration Notion active. Documentation : NOTION-API.fr.md.
- Correctif commun `192d0be` : sortie UTF-8 du serveur sous Windows, notamment avec redirection ; candidat à reprise indépendante, non intégré à main.
- Validation : 157 tests réussis, contrôles syntaxiques des trois scripts JavaScript, parcours navigateur de démonstration (connexion, base, sélection, analyse et retour Anytype). Aucun appel réel Notion et aucun import réel.

## Sélection Notion par arborescence

- Parcours spécifique Notion : jeton disponible masqué, espace unique de la connexion, racines chargées après connexion, enfants à la demande, sélection/exclusions par branche. Aucun changement de la stable ni du moteur de destination.
- Les racines de l’inventaire ne sont pas présentées comme une liste exacte d’autorisations explicites. Les limites de recherche et les parents hors accès restent signalés.

- Correctif suivant : reconstruction des ancêtres de type bloc, groupe distinct pour les parents non résolus, analyse asynchrone avec progression et annulation. Cache de blocs limité à une analyse, pas de modification du moteur Anytwo.

- Validation de ce correctif : 174 tests réussis, dont parents de type bloc, parents absents de la recherche, analyse HTTP asynchrone, suivi pendant le verrou réseau, annulation et erreurs sans fuite de détails. Parcours navigateur contrôlé avec réponses fictives ralenties.

- Réactivité : validation cloud du jeton limitée à 5 secondes, attente de verrou bornée, inventaire sans blocage de toute l’interface, préchargement séquentiel des branches et réutilisation du cache de navigation. Aucun besoin du client Notion ; le client Anytwo reste nécessaire pour la destination locale.
- Validation : 177 tests réussis ; branche préchargée puis relue via HTTP en démonstration, sans appel au compte Notion réel. Contrôles syntaxiques JavaScript et diff sans erreur.

- Grandes analyses Notion : quatre lectures concurrentes avec débit global conservateur, cache partagé et déduplication des requêtes, reprise de la même sélection après interruption pendant cinq minutes, budget annulable de quinze minutes. Fonctions spécifiques Notion ; pas de reprise nécessaire dans Anytype.
- Validation : 185 tests réussis. Lectures concurrentes vérifiées, plafond global testé, temporisation 529 et annulation testées, reprise sans relire les blocs réussis, cache invalidé par actualisation. Mesure réseau fictive (41 pages, 82 requêtes) : 2,11 s en série, 1,33 s en concurrence ; ce chiffre ne prédit pas le débit du compte réel.

- Parcours Notion : popup de connexion avec contrôle automatique du jeton disponible et préparation du premier niveau ; accès aux réglages Notion/Anytwo par le statut API ; deux volets de sélection/configuration. Indicateur de recherche explicite et séparation permanente des éléments hors premier niveau, préchargés comme les autres branches. Tests de scénarios frontend : tests/test_notion_ui.cjs.

- Validation du nouveau parcours : 185 tests Python et 5 scénarios JavaScript réussis ; structure HTML équilibrée et identifiants uniques. Le module de vérification visuelle Windows ne démarre pas dans cet environnement. Aucun test du compte Notion réel et aucun import effectué.

- État de connexion Notion confirmé en vert, bouton désactivé après validation, popup de chargement distincte et fermable sans annulation. Six scénarios d’interface vérifiés. Rapport rollup corrigé après lecture des descripteurs réels du client Anytwo (sum/original).
- Modèles demandés créés puis relus dans Notion (page parente Test pour Anytwo) et dans un nouvel espace Anytype Test pour Anytwo. L’utilisateur a accordé lui-même l’écriture Anytype ; aucun réglage stable n’a été modifié par l’agent. Création isolée dans tools/create_test_pages.py, jamais utilisée par l’importeur. Journal privé dans reports/source-fixtures.json, exclu de Git.

- Vérification finale : 185 tests Python, six scénarios frontend, balises HTML équilibrées et identifiants uniques. Les modèles source ont été relus via API ; aucun objet Anytwo n’a été modifié pour tester les rollups.

- Sélection Notion limitée à racine + deux niveaux, sans préchargement plus profond ; les branches sélectionnées restent parcourues intégralement pour analyse/import. Configuration des espaces de destination par nom du workspace, politique de création systématique des collections et bilan par type de vue. Contrat : NOTION-IMPORT.fr.md. Validation : 188 tests Python et sept scénarios frontend. Écritures Notion → Anytwo toujours inactives ; aucun changement de la stable.

- Écran Notion aligné sur « Importer vos données » : bandeau de compatibilité et fenêtre commune adaptés à la source, configuration avec état vide/résumé/destination, options fichiers et liens hors arborescence, actions Tester/Importer. L’option chats reste propre à Anytype. Destination chargée automatiquement au choix du workspace si Anytwo est disponible. L’écriture Notion reste indisponible et le bouton Importer le signale ; ces options ne déclenchent aucune écriture.

- Import Notion opérationnel : notion_migration.py, notion_content.py, notion_views.py et notion_files.py réutilisent la frontière Anytwo commune. Tâche de fond avec verrou partagé, progression, annulation, checkpoints privés et bilan ; intégration du bouton Importer et options, avec aperçu Tester du même périmètre lié. Les sources vides, exclusions, tris null, propriétés paginées, formules figées, relations et configurations rollup sont traités. Aucun changement de main ni publication. Validation : 207 tests Python, huit scénarios frontend, import réel autorisé du modèle (7 pages, 2 collections, 4 fichiers distincts), relecture API des dates, relations, propriétés, couleurs et vues. Recalcul rollup et rendu visuel final à vérifier dans le client.

- Correctif commun `3e2fa1d` des vues : les objets techniques dataview sont créés sans any.name, comme le client natif. Les nommer « Vues Anytype » les faisait apparaître dans la navigation comme des documents parasites. Identifiants et jeux de vues conservés. Correctif isolé sur develop/notion, candidat à reprise indépendante dans main ; stable non modifiée. Régression de création de vue complétée et suite Anytype vérifiée.

- Formats Notion corrigés après inspection du client installé : espaces des annotations hors marqueurs de gras/italique/barré ; enveloppes natives callout, image-caption et synced-block ; références de synchronisation et sommaires finalisées vers les vrais identifiants de blocs après le PUT. Soulignement toujours indisponible dans le pont et explicitement signalé. La page modèle existante a été corrigée avec sauvegarde préalable, sans créer de nouvelles pages ni modifier Notion. Validation : 214 tests Python, huit scénarios frontend, puis conversion du Markdown réellement relu avec les bibliothèques du client dans un DOM isolé (réseau désactivé) : formats 1/2/4, callout, deux captions canoniques, original/référence synchronisés et liens du sommaire confirmés. Les trois supports techniques ont perdu uniquement leur nom artificiel, conservant leurs données.

- Propriétés Notion : collections créées avant les propriétés, restriction des relations par xKey cible, titre de rollup via collection cible / any.name, identités source décodées et prioritaires aux noms ; devises, pourcentages et séparateurs numériques natifs. Aucun lien parent artificiel. Correction en place du modèle réimporté par l’utilisateur dans Sri, avec sauvegarde, valeurs inchangées et retrait ponctuel des deux liens générés (aucun PUT de document). Vérification avec les fonctions du client : sélecteurs Projet/Name/Budget, résultats des rollups 100/180/0 et noms des projets, format currency/EUR. Tests : 221 Python et huit scénarios frontend. Stable Anytype inchangée ; correctif spécifique Notion.


- Optimisation des lectures Notion : propriétés déjà complètes non relues, parcours des exclusions évité, cache partagé et reprise des lectures interrompues en mémoire, métriques par catégorie, délais distingués des erreurs réseau. Pas de modification de main. Ajout à la frontière Anytwo d’un helper set_space_icon : fichier attaché à l’objet index et URI native dans iconCid ; candidat indépendant à reprise si nécessaire. La récupération de l’image d’espace reste indisponible dans les métadonnées documentées du jeton interne Notion ; aucun avatar de bot substitué.

- Validation de cette optimisation : 233 tests Python et huit scénarios frontend réussis, dont douze régressions sur lectures inutiles, exclusions/réinclusions, cache partagé, reprise après délai et icône native. Aucun import réel déclenché pour ces tests ; performances sur le périmètre utilisateur encore à mesurer. Version Anytype stable propre et inchangée.


- Vues liées Notion : sources résolues via les vues lorsque data_sources est vide, distinction base pleine page / vue inline, filtres rapides et colonnes supprimées, adaptation signalée des regroupements ; callouts sans paragraphes initiaux artificiels et icônes natives. Modification commune minimale : inline_records et create_saved_views transmettent le champ icon optionnel des vues converties, sans changer les vues sans icône. Candidat à reprise indépendante dans main, non appliqué à la stable. Données privées d’audit et replays sous reports uniquement, non versionnées.

- Validation des vues liées : suite complète de 245 tests Python et huit scénarios frontend réussis, puis 13 tests ciblés des vues/icônes et 25 du moteur après les derniers ajustements. Rejeu privé des cinq pages source : nombres de vues attendus confirmés, sept vues de Base recettes et filtres rapides présents. Conversion par les bibliothèques réelles du client dans un DOM isolé : callouts sans vide initial, Cave comme lien objet interne au callout, emoji composé reconnu. Aucun import réel ni écriture dans Sri.


- Groupes/relations/rollups Notion : conservation des regroupements de collection et colonnes Kanban, filtre texte contient (LPB), libellés par défaut, relations dual_property appariées Two-way et moyenne native. NotionViewConverter garde ces adaptations propres à Notion ; la sélection native par collection évite les longs filtres d’identifiants. Le moteur commun collection_presentation accepte un champ group_settings optionnel et traduit le schéma UI natif, sans changer les autres vues ; ui_clause accepte les deux conditions texte préfixées notion_. À isoler pour une éventuelle reprise du schéma de regroupement dans main ; stable non modifiée. Validation : 252 tests Python + huit scénarios frontend, parseur du client sur 12 vues, requête LPB six objets des deux côtés, paire bidirectionnelle reconnue et 53 moyennes conformes. Aucun import réel ni écriture sur Sri.


- Préparation commune autorisée : profil unified indépendant, choix source avant contrôle des accès, un lanceur principal, reprise locale des secrets protégés de développement et archive publique reproductible. Paramètres de présentation facultatifs openMode / galleryFitImage transportés par le convertisseur partagé, sans modifier les vues qui ne les précisent pas. Le profil et les fichiers de la version Anytype stable restent inchangés ; aucun push ni release.

- Correctif commun isolé dans le commit local 21592f3 (sur release/unified) : présentation facultative des vues, group_settings natif, icônes de vues et helper icône d’espace. Non intégré à main ; dépend de la frontière anytwo_backend déjà présente dans cette branche. Validation finale : 258 tests Python, quatre scénarios de démarrage et huit scénarios Notion réussis ; Fit image/openMode reconnus par le parseur réel du client. Archive extraite puis démarrée en démo : deux sources accessibles, écritures désactivées. Aucun import réel, aucune publication.


- Organisation 0.10.1 : dossier actif F:/Documents/ChatGPT/Anytwo/Any2Any, modules et static déplacés sous app, tests/outils/exemples/rapports privés regroupés sous dev. Lanceurs et imports de tests adaptés ; profils utilisateur inchangés. Archive source propre et distribution Windows x64 autonome (Any2Any.exe, _internal, documentation) ; contrôle de l’EXE après extraction avant publication, sans import réel. Réorganisation autorisée pour le local, GitHub et une nouvelle release, sans réécriture de 0.10.0.
