# Import Anytype vers Anytwo

Any2Any lit l’API locale Anytype v2 et écrit dans Anytwo via le moteur de destination partagé. L’application commune propose Anytype ou Notion au démarrage. Le [guide Notion](NOTION-IMPORT.fr.md) décrit l’autre source.

## Connexion et lancement

L’archive Windows autonome se lance avec `Any2Any.exe`. La version source demande Python 3.10 ou ultérieur et se lance avec `demarrer.bat` ou `python app/server.py`. L’interface écoute sur `127.0.0.1`, à partir du port `8766`.

Anytype et Anytwo doivent être ouverts. Anytype utilise normalement le port `31009`, avec une clé obtenue par appairage. Le bouton d’état des API permet de vérifier ou modifier les accès. Le port Anytwo est détecté automatiquement lorsque possible, avec `31310` comme port habituel.

Les réglages et bilans du profil commun sont conservés dans `%APPDATA%/any2any` sous Windows. Les secrets mémorisés sont protégés par Windows DPAPI. Les profils de développement utilisent leurs propres répertoires. Le mode `--demo` permet d’explorer les deux sources avec des données fictives et désactive les imports réels.

## Sélection et destination

L’utilisateur peut choisir un espace, une collection, des types ou des objets. L’option des éléments liés ajoute les références accessibles dans le même espace, y compris les documents de vues intégrées dont les filtres sont évaluables. Pour un espace entier, cette option est désactivée dans l’interface. Le bilan précise la raison de chaque inclusion.

La destination est un espace existant ou un nouvel espace. Les collections source deviennent des collections Anytwo, avec leurs supertags et leurs propriétés. Une collection de type sert de repli aux objets qui ont des propriétés et ne sont membres d’aucune collection importée, ou lorsqu’une destination par type est explicitement choisie.

Les pages sont créées avant la reconstruction de leurs liens. Les liens vers une collection ciblent directement la collection. Les collections référencées par une vue peuvent aussi être reprises lorsqu’elles sont archivées côté Anytype. Leurs vues restent limitées au périmètre des objets effectivement importés.

## Contenu et propriétés

Les textes mis en forme, titres, paragraphes vides, listes, cases à cocher, toggles, citations, callouts, code, équations, tableaux et colonnes sont convertis selon les possibilités du client Anytwo. Les images, fichiers, lecteurs audio et vidéos YouTube emploient les formats natifs compatibles. Les mentions deviennent des liens inline et les liens internes sont remappés vers les nouveaux identifiants.

Les propriétés texte, numériques, booléennes, dates, selects et relations compatibles sont transférées dans les collections cibles. Les options et leurs couleurs sont lues dans le vocabulaire source. Une date contenant une heure reste en datetime, même si les métadonnées source annoncent une date simple. Les colonnes sans valeur déclarées par le type sont également créées, sauf les propriétés fichiers/images non portables.

Les propriétés fichiers/images deviennent du contenu en début de page, sous leur libellé, lorsque la récupération des fichiers est activée. Elles ne créent pas de colonnes texte de remplacement. Les noms des fichiers sont recherchés dans leurs métadonnées. Un même fichier est réutilisé entre pages, et un fichier existant n’est réutilisé qu’après vérification du nom normalisé, de la taille et du contenu.

Les templates des types importés et ceux référencés par les vues de collection deviennent des templates natifs Anytwo. Leur contenu, leur icône et leurs propriétés sont repris. Le défaut de la vue active prend priorité sur celui du type. Les défauts concurrents et les différences avec un défaut cible existant sont signalés.

Les sommaires de premier niveau utilisent le bloc dynamique natif lorsque la version Anytwo le permet. Les sommaires imbriqués utilisent des liens statiques vers les identifiants réels des titres.

## Vues et widgets

Les dispositions table, liste, galerie et kanban compatibles sont reprises. Les filtres ET/OU imbriqués, comparaisons simples, sélections, conditions de valeurs vides et comparaisons texte compatibles sont remappés avec les propriétés, options et références. Les tris, regroupements, propriétés visibles et ordre des colonnes sont appliqués lorsque leur configuration est transposable. La vue active incompatible est signalée.

Une vue inline doit reposer sur une seule collection Anytwo. Plusieurs vues peuvent réutiliser cette collection avec leurs propres configurations. Les versions Anytwo compatibles acceptent les tables et kanbans inline ; les anciens clients peuvent nécessiter une adaptation en liste. Une mise en page avancée, notamment une vue dans un callout ou une colonne, peut perdre son emplacement ou sa présentation.

Les widgets Anytype fondés sur une page ou une collection importée sont ajoutés à l’Overview partagé, dans l’ordre source. Le mode Link reste Link et les autres modes utilisent Views. Les sections et widgets système sont ignorés. Les doublons de cible entre widgets partagés et personnels sont évités.

## Chats, limites et bilan

Les chats et discussions sont exclus de l’import ordinaire. L’option d’archive des chats crée une page par chat exposé par l’API de l’espace, avec auteurs, dates, réponses, réactions et pièces jointes selon l’option fichiers. Les discussions d’objets absentes de cette liste ne sont pas découvertes séparément.

Certaines fonctionnalités sont absentes d’Anytwo ou ont un modèle différent. Cela concerne les couleurs de texte, de fond, de blocs, de cellules et de callouts, les types, la portée locale/globale des propriétés, les propriétés fichiers/images, les bookmarks enrichis, les discussions, les mini-apps et les dispositions Graph/Calendar. L’alignement et certaines compositions de blocs ne sont pas conservés. Les dates relatives, tris personnalisés, restrictions de relation hors périmètre et autres conditions non transposables sont signalés dans le bilan.

L’import simple crée de nouvelles copies à chaque lancement. Il ne fournit pas de synchronisation ni d’annulation globale. La limite actuelle est de 500 objets, templates inclus, et de 100 Mio par fichier. La simulation examine le périmètre sans écrire dans Anytwo.

Le bilan JSON contient les correspondances source/cible, les vues, les paramètres archivés, les transferts de fichiers, les adaptations et les erreurs. Il peut contenir le contenu source. Il est enregistré dans le profil actif.

Les [détails de fidélité](IMPORT-FIDELITE.fr.md) précisent les conversions et les limites. L’[historique bilingue](../CHANGELOG.md) décrit les changements publiés et en préparation.
