# Any2Any — préparation de l’application commune

Ce worktree est `F:/Documents/ChatGPT/Anytwo/Any2Any-Notion`, branche de préparation `release/unified` (issue de `develop/notion`).
La version Anytype stable est `F:/Documents/ChatGPT/Any2Any`, branche `main`.

- Vérifier `git branch --show-current` et `git status` avant chaque modification. Si le chat démarre dans le dossier parent Anytwo, utiliser explicitement ce worktree pour toutes les commandes du développement Notion.
- Ne pas modifier les fichiers, réglages ou rapports de la version Anytype stable. Les métadonnées Git du dépôt sont partagées ; les fichiers des worktrees restent distincts.
- Ne jamais lancer ce développement dans le dossier stable. `demarrer.bat` lance désormais l’application commune (profil unified, port 8766, APPDATA/any2any). Les lanceurs spécialisés sont dans tools/development et gardent leurs profils any2any-dev indépendants. La stable anytype-anytwo-importer n’est ni modifiée ni utilisée comme source de réglages.
- Le lecteur Notion reste strictement en lecture seule. L’import vers Anytwo est activé via notion_migration.py et notion_import_jobs.py, avec le verrou d’écriture partagé et des bilans de progression. Aucun import réel pour un simple test technique sans autorisation ; le modèle « Test pour Anytwo » a été explicitement autorisé pour la vérification de cette fonctionnalité.
- L’API de destination commune est `anytwo_backend.py`. Les implémentations existantes restent dans `api_clients.py` avec compatibilité ; ne pas dupliquer les écritures Anytwo dans un futur lecteur Notion.
- Les tests de régression Anytype restent obligatoires pour une modification commune. Maintenir également les tests du lecteur et des routes Notion.
- Isoler les correctifs communs dans des commits indépendants de Notion. Les intégrer d’abord dans main après validation/autorisations de publication, puis reprendre main dans develop/notion. Ne jamais fusionner globalement develop/notion dans main avant validation de la version commune.
- Consulter `docs/DEVELOPMENT.fr.md` et `docs/COMMON-FIXES.md` au début du travail. Les conversations ne partagent pas automatiquement leur contexte ; noter les décisions utiles dans ces documents.
- Ne pas publier de branche/release sans demande. Ne pas démarrer de migration réelle pour une simple vérification technique.

- L’utilisateur a demandé la préparation de l’application commune et un choix Anytype/Notion au démarrage. Préparer une archive publique nettoyée, sans pousser ni publier sans nouvelle demande. Les fichiers privés reports restent exclus et sont conservés ; le nettoyage vise les caches et la séparation des outils de développement.

- Publication explicitement autorisée par l’utilisateur : PR complet vers main et préversion v0.10.0, notes anglais puis français, archive et SHA-256. Le PR reste ouvert pour revue ; le tag pointe sur le commit complet de release/unified. Les fichiers du worktree stable ne sont pas modifiés.
