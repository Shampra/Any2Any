# Développement isolé Anytype / Notion

## État de départ

- Base commune : main, commit `684c8867ac67b6f4752743d23c88040103b19a98`, release 0.9.3.
- Stable Anytype : `F:/Documents/ChatGPT/Any2Any`, branche main, fichiers inchangés.
- Prototype : `F:/Documents/ChatGPT/Anytwo/Any2Any`, branche develop/notion.
- Worktree Git créé séparément. L’application Codex a refusé son rattachement comme worktree géré car le dépôt stable est hors des racines déclarées du chat. Utiliser explicitement le dossier prototype dans les commandes ; ce n’est pas un échec d’isolation Git.

## Lancer

| Version | Lanceur | Port par défaut | Configuration et rapports |
|---|---|---|---|
| Stable Anytype | dossier stable, demarrer.bat | 8765 | APPDATA/anytype-anytwo-importer |
| Application commune | demarrer.bat | 8766 | APPDATA/any2any |
| Prototype Notion | dev/tools/development/demarrer-notion.bat | 8876 | APPDATA/any2any-dev/notion-dev |
| Vérification Anytype du moteur en développement | dev/tools/development/demarrer-anytype-dev.bat | 8877 | APPDATA/any2any-dev/anytype-dev |

Dans ce worktree, server.py et demarrer.bat utilisent désormais le profil unified et une fenêtre de choix Anytype/Notion avant toute vérification. Les lanceurs spécialisés déplacés dans tools/development forcent leurs anciens profils. La première ouverture de unified reprend les secrets protégés des deux profils de développement, sans modifier ces fichiers ; la configuration stable n’est jamais lue ni écrite.

Le profil notion-dev ouvre le parcours Notion : connexion interne, inventaire, sélection par base/source/page et analyse de compatibilité en lecture seule. Le choix Anytype reste disponible pour les régressions. Le convertisseur Notion est actif via notion_migration.py ; les écritures utilisent anytwo_backend.py et le verrou partagé avec Anytype. Voir NOTION-IMPORT.fr.md pour les limites et le test réel autorisé. Voir [l’analyse API et la connexion](NOTION-API.fr.md).

## Code commun et reprises

`anytwo_backend.py` est le point d’entrée de destination, utilisé par migration.py, view_conversion.py et file_transfer.py. Il réexporte la seule implémentation existante de api_clients.py afin de garder la compatibilité et les tests pendant une extraction progressive. Les fonctions de lecture Anytype et sa conversion de document restent spécifiques à Anytype. Le lecteur Notion utilise cette API de destination et ses formats natifs, sans copier ses écritures HTTP.

Un correctif de main est repris ici par fusion de main après un commit ou une mise à l’abri des travaux en cours. Les modifications communes trouvées pendant Notion doivent être isolées des fonctions Notion : préparer un commit compatible avec main, le valider côté Anytype, puis intégrer main dans develop/notion. Si un correctif dépend d’un refactoring encore expérimental, noter une adaptation à faire dans COMMON-FIXES.md plutôt que prétendre qu’il est déjà repris. Résoudre les conflits et relancer les tests ; les reprises ne sont pas automatiques.

Conserver deux branches durables. Les branches temporaires de correction peuvent partir de main. Ne pas changer main depuis cette conversation ni publier sans demande. La future fusion Notion sera une étape explicite, après validation des deux sources.

## Vérifier

Depuis ce dossier : `python -B dev/run_tests.py`, puis `node dev/tests/test_notion_ui.cjs`, `node --check app/static/app.js` et `node --check app/static/i18n.js` et `node --check app/static/notion.js`. Pour une démonstration sans API : `demarrer-notion.bat --demo`. Toujours vérifier le profil affiché par /api/config et la console avant un essai réel.

Le parcours Notion utilise sa propre popup de connexion et de réglage des deux API ; le formulaire Anytype reste indépendant. Dans ce dossier, demarrer.bat force le profil unified ; les deux lanceurs sous tools/development forcent leur profil et leur port respectifs.


## Préparation de la version commune

Branche locale release/unified issue de develop/notion, même worktree physique. Le dossier stable et main restent inchangés. Les sources Anytype et Notion utilisent la frontière Anytwo commune ; les tests des deux restent obligatoires. Aucune publication n’est faite par la préparation.

Construire : python -B dev/tools/build_release.py. L’archive dev/dist/Any2Any-<version>.zip contient uniquement les modules applicatifs, static, les README/licence/changelog, les guides utilisateurs et les deux lanceurs principal/démo. BUILD.json porte les empreintes des fichiers publics et le ZIP a son SHA-256 séparé. Une liste autorisée explicite exclut rapports, secrets, métadonnées Git, tests et outils de diagnostic. La construction est reproductible et ne dépend pas des fichiers de reports.

Les rapports/audits privés restent dans reports, ignoré par Git et exclu de la distribution. Ne pas effacer les sauvegardes utilisateur pour nettoyer le dépôt. Les caches __pycache__ du code et des tests peuvent être retirés ; les autres projets du dossier parent ne sont pas concernés.


## Dossier actif et construction Windows

Le worktree actif est F:/Documents/ChatGPT/Anytwo/Any2Any. Le dossier historique Any2Any-Notion est vidé ; aucun rapport n’a été supprimé. Les données privées sont dans dev/reports et dev/.local, toujours ignorées par Git. Le code actif est dans app, les tests et builders dans dev. Le dossier Anytype historique n’est plus le lanceur de référence et ses fichiers ne sont pas modifiés.

Lancer demarrer.bat ou python app/server.py. Tester : python -B dev/run_tests.py, node dev/tests/test_notion_ui.cjs et node dev/tests/test_startup_ui.cjs. Archive source : python -B dev/tools/build_release.py. Construction Windows sur Windows : installer la dépendance de développement pyinstaller==6.22.3 puis python -B dev/tools/build_windows.py. Le builder extrait son ZIP et démarre l’EXE en démo avec des réglages temporaires ; les deux sources sont contrôlées sans accéder aux comptes utilisateur.

GitHub Actions vérifie Linux et Windows, construit le binaire Windows x64, puis publie les deux ZIP et leurs SHA-256 dans une nouvelle préversion. La release 0.10.0 reste intacte. Les fichiers compilés sont sous dev/build et ne sont pas versionnés.
