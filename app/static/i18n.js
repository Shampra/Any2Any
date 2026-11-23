'use strict';
/* UI-only translations. Source data (names, property values, content) is never translated.
   French strings are source keys to preserve compatibility with the existing UI. */
(function(global){
  const STORAGE_KEY='any2any.language';
  const LEGACY_STORAGE_KEY='type2two.language';
  const messages={
    'Any2Any · Importer':['Any2Any · Import','Any2Any · Importieren'],
    'Any2Any · Autorisation Anytype':['Any2Any · Anytype authorization','Any2Any · Anytype-Autorisierung'],
    'Anytype → Anytwo · Outil de migration · Bêta 0.11.0':['Anytype → Anytwo · Migration tool · Beta 0.11.0','Anytype → Anytwo · Migrationstool · Beta 0.11.0'],
    'Autorisation Anytype · Importateur':['Anytype authorization · Importer','Anytype-Autorisierung · Importer'],
    'Outil de migration · Bêta 0.11.0':['Migration tool · Experimental beta 0.11.0','Migrationstool · Experimentelle Beta 0.11.0'],
    'Ce client Anytwo affiche les marqueurs de mise en page : blocs repliables, colonnes et intégrations sont écrits en Markdown simple.':['This Anytwo client displays layout markers, so toggles, columns and embeds are written as plain Markdown.','Dieser Anytwo-Client zeigt Layout-Marker an, daher werden Umschalter, Spalten und Einbettungen als einfaches Markdown geschrieben.'],
    'D’où souhaitez-vous importer ?':['Where would you like to import from?','Aus welcher App möchten Sie importieren?'],
    'Choisissez votre application source. Nous vérifierons ensuite les accès nécessaires.':['Choose your source app. We will then check the required connections.','Wählen Sie Ihre Quell-App. Anschließend prüfen wir die benötigten Zugänge.'],
    'Depuis l’application sur cet ordinateur':['From the app on this computer','Aus der App auf diesem Computer'],
    'Depuis votre espace en ligne':['From your online workspace','Aus Ihrem Online-Arbeitsbereich'],
    'Choisir une source':['Choose a source','Quelle wählen'],
    'Ouverture de la connexion…':['Opening connection settings…','Verbindungseinstellungen werden geöffnet…'],
    'Anytype / Notion → Anytwo · Outil expérimental':['Anytype / Notion → Anytwo · Experimental tool','Anytype / Notion → Anytwo · Experimentelles Tool'],
    'Mode démo':['Demo mode','Demomodus'],
    'Vérification des API':['Checking APIs','APIs werden geprüft'],
    'MIGRATION LOCALE':['LOCAL MIGRATION','LOKALE MIGRATION'],
    'Importer vos données':['Import your data','Daten importieren'],
    'Choisissez précisément ce que vous souhaitez transférer depuis Anytype vers Anytwo.':['Choose exactly what to transfer from Anytype to Anytwo.','Wählen Sie genau aus, was von Anytype nach Anytwo übertragen werden soll.'],
    'Import local · source inchangée':['Local import · source unchanged','Lokaler Import · Quelle bleibt unverändert'],
    'Attention : certains éléments Anytype ne pourront pas être importés dans Anytwo.':['Warning: some Anytype items cannot be imported into Anytwo.','Achtung: Einige Anytype-Elemente können nicht nach Anytwo importiert werden.'],
    'Des différences de fonctionnement peuvent aussi empêcher une restitution identique.':['Differences between the applications may also affect fidelity.','Unterschiede zwischen den Anwendungen können die originalgetreue Übertragung beeinträchtigen.'],
    'Voir plus':['Learn more','Mehr erfahren'],
    'Type d’import':['Import mode','Importmodus'],
    'Définit comment les objets seront identifiés à l’avenir.':['Defines how objects will be identified in the future.','Legt fest, wie Objekte künftig identifiziert werden.'],
    'Import simple':['Simple import','Einfacher Import'],
    'Avec synchronisation':['With synchronization','Mit Synchronisierung'],
    ': crée une copie sans conserver les identifiants sources.':[': creates a copy without preserving source IDs.',': erstellt eine Kopie, ohne die Quell-IDs zu speichern.'],
    ': prévoit les propriétés techniques « ID Anytype » et « Espace Anytype » pour identifier les objets lors des mises à jour ultérieures. La synchronisation effective sera développée plus tard.':[': plans to use the “Anytype ID” and “Anytype space” technical properties for future updates. Actual synchronization is not yet available.',': sieht die technischen Eigenschaften „Anytype-ID“ und „Anytype-Bereich“ für spätere Aktualisierungen vor. Die Synchronisierung ist noch nicht verfügbar.'],
    'Choix des éléments à importer':['Choose items to import','Zu importierende Elemente auswählen'],
    'SÉLECTIONNER UN ESPACE ANYTYPE':['SELECT AN ANYTYPE SPACE','ANYTYPE-BEREICH AUSWÄHLEN'],
    '↻ Mettre à jour':['↻ Refresh','↻ Aktualisieren'],
    'Importer tout l’espace':['Import entire space','Gesamten Bereich importieren'],
    'Tous les objets et toutes les collections de cet espace':['All objects and collections in this space','Alle Objekte und Sammlungen dieses Bereichs'],
    'Chargement de l’espace, des collections et des appartenances…':['Loading space, collections and memberships…','Bereich, Sammlungen und Zuordnungen werden geladen …'],
    'Collections disponibles':['Available collections','Verfügbare Sammlungen'],
    'Types disponibles':['Available types','Verfügbare Typen'],
    'Cochez plusieurs types pour tout importer, ou utilisez l’œil pour choisir des objets individuels.':['Select multiple types to import them all, or use the eye icon to choose individual objects.','Wählen Sie mehrere Typen für den vollständigen Import oder öffnen Sie die Einzelobjekte mit dem Augensymbol.'],
    'Sélectionnez un espace pour afficher son contenu.':['Select a space to see its contents.','Wählen Sie einen Bereich aus, um dessen Inhalt anzuzeigen.'],
    'Configuration de l’import':['Import configuration','Import konfigurieren'],
    'Aucun élément sélectionné':['No items selected','Keine Elemente ausgewählt'],
    'Sélectionnez un espace, une collection, un type ou des objets à gauche pour configurer sa destination.':['Select a space, collection, type or individual objects on the left to configure their destination.','Wählen Sie links einen Bereich, eine Sammlung, einen Typ oder einzelne Objekte aus, um das Ziel festzulegen.'],
    'SÉLECTION ACTUELLE':['CURRENT SELECTION','AKTUELLE AUSWAHL'],
    'CHOIX DE L’ESPACE DE DESTINATION':['DESTINATION SPACE','ZIELBEREICH'],
    'NOM DU NOUVEL ESPACE':['NEW SPACE NAME','NAME DES NEUEN BEREICHS'],
    'DESTINATION PAR TYPE':['DESTINATION BY TYPE','ZIEL NACH TYP'],
    'Les propriétés d’un type sont conservées dans une collection Anytwo. Pour éviter les pertes, une collection est requise si des propriétés existent ou si leur absence ne peut pas être confirmée.':['Type properties are preserved in an Anytwo collection. To prevent data loss, a collection is required if properties exist or cannot be ruled out.','Typ-Eigenschaften werden in einer Anytwo-Sammlung aufbewahrt. Um Datenverluste zu vermeiden, ist eine Sammlung erforderlich, wenn Eigenschaften vorhanden sind oder nicht ausgeschlossen werden können.'],
    'CHOIX DE LA COLLECTION':['DESTINATION COLLECTION','ZIELSAMMLUNG'],
    'Importer dans une collection':['Import into a collection','In eine Sammlung importieren'],
    'NOM DE LA NOUVELLE COLLECTION':['NEW COLLECTION NAME','NAME DER NEUEN SAMMLUNG'],
    'OPTIONS COMPLÉMENTAIRES':['ADDITIONAL OPTIONS','WEITERE OPTIONEN'],
    'Importer les chats en tant qu’archives':['Import chats as archives','Chats als Archive importieren'],
    'Une page par chat, pour tous les chats de l’espace source. Pièces jointes selon l’option fichiers.':['One page per chat, for all chats in the source space. Attachments follow the files option.','Eine Seite pro Chat für alle Chats des Quellbereichs. Anhänge gemäß Dateioption.'],
    'Récupérer les fichiers':['Include files','Dateien übernehmen'],
    'Images, documents et pièces jointes':['Images, documents and attachments','Bilder, Dokumente und Anhänge'],
    'Importer également les éléments liés':['Also import linked items','Verknüpfte Elemente ebenfalls importieren'],
    'Peut étendre le nombre d’objets importés':['May increase the number of imported objects','Kann die Anzahl der importierten Objekte erhöhen'],
    '⌁  Tester':['⌁  Test','⌁  Testen'],
    'Tester':['Test','Testen'],
    'Importer':['Import','Importieren'],
    'Import réel : crée des objets et collections dans Anytwo ; aucun changement dans Anytype. Tester reste sans écriture.':['Real import creates objects and collections in Anytwo; Anytype is not modified. Test mode does not write data.','Beim echten Import werden Objekte und Sammlungen in Anytwo erstellt; Anytype bleibt unverändert. Der Testmodus schreibt keine Daten.'],
    'Traitement local · Anytype reste en lecture seule · L’import modifie Anytwo après confirmation':['Local processing · Anytype is read-only · Anytwo is modified only after confirmation','Lokale Verarbeitung · Anytype bleibt schreibgeschützt · Anytwo wird erst nach Bestätigung geändert'],
    'AVANT D’IMPORTER':['BEFORE IMPORTING','VOR DEM IMPORT'],
    'Limites connues de la migration':['Known migration limitations','Bekannte Einschränkungen beim Import'],
    'Certaines fonctionnalités d’Anytype ne peuvent pas être reprises à l’identique dans Anytwo. Cette liste':['Some Anytype features cannot be recreated identically in Anytwo. This list','Einige Anytype-Funktionen können in Anytwo nicht identisch wiederhergestellt werden. Diese Liste'],
    'n’est pas exhaustive':['is not exhaustive','ist nicht vollständig'],
    '. Les différences de fonctionnement entre les deux applications peuvent également empêcher l’import de fonctionnalités pourtant présentes dans les deux.':['. Differences between the applications may prevent importing features even when both support them.','. Unterschiede zwischen den Anwendungen können auch die Übernahme von Funktionen verhindern, die in beiden vorhanden sind.'],
    'Éléments signalés à ce stade':['Currently identified limitations','Derzeit bekannte Einschränkungen'],
    'Les vues intégrées ne peuvent pas rester dans des colonnes de blocs':['Inline views cannot stay inside block columns','Inline-Ansichten können nicht in Blockspalten bleiben'],
    'Une vue importée depuis Anytype ne peut être basée que sur une collection Anytwo':['A view imported from Anytype can only use an Anytwo collection as its source','Eine aus Anytype importierte Ansicht kann nur eine Anytwo-Sammlung als Quelle verwenden'],
    'Vues : certains regroupements et filtres avancés ne sont pas transposables':['Views: some groupings and advanced filters cannot be transferred','Ansichten: Einige Gruppierungen und erweiterte Filter lassen sich nicht übertragen'],
    'Propriétés : certains fuseaux horaires de plages de dates ne sont pas transposables':['Properties: some date range time zones cannot be transferred','Eigenschaften: Einige Zeitzonen von Datumsbereichen lassen sich nicht übertragen'],
    'Les propriétés système intégrées affichent la valeur Anytwo, par exemple le créateur de la page importée':['Inline system properties show the Anytwo value, such as the creator of the imported page','Eingebettete Systemeigenschaften zeigen den Anytwo-Wert, etwa wer die importierte Seite erstellt hat'],
    'Le soulignement dépend de la version Anytwo':['Underlining depends on the Anytwo version','Unterstreichungen hängen von der Anytwo-Version ab'],
    'Pages : aperçus web externes conservés comme liens ; boutons, fil d’Ariane et onglets non reproduits':['Pages: external web previews become links; buttons, breadcrumbs and tabs are omitted','Seiten: Externe Webvorschauen werden als Links übernommen; Schaltflächen, Brotkrümelnavigation und Tabs entfallen'],
    'Pages : sommaire statique avec liens vers les titres':['Pages: static table of contents with links to headings','Seiten: Statisches Inhaltsverzeichnis mit Links zu Überschriften'],
    'Pages : couleurs de texte et de fond non conservées ; soulignement selon la version Anytwo':['Pages: text and background colours are omitted; underlining depends on the Anytwo version','Seiten: Text- und Hintergrundfarben entfallen; Unterstreichungen hängen von der Anytwo-Version ab'],
    'Espace créé. Il est sélectionné pour le prochain import.':['Space created and selected for the next import.','Der erstellte Space ist für den nächsten Import ausgewählt.'],
    'L’espace sélectionné est introuvable. Choisissez une destination.':['The selected space could not be found. Choose a destination.','Der ausgewählte Space wurde nicht gefunden. Wähle ein Ziel.'],
    'Couleur de background':['Block background colors','Blockhintergrundfarben'],
    'Types':['Types','Typen'],
    'Incompatibilités regroupées':['Grouped incompatibilities','Zusammengefasste Inkompatibilitäten'],
    'Configurer les API':['Configure the APIs','APIs konfigurieren'],
    'Configurer les API Notion et Anytwo':['Configure the Notion and Anytwo APIs','Notion- und Anytwo-APIs konfigurieren'],
    'Créer les données sélectionnées dans Anytwo':['Create the selected data in Anytwo','Ausgewählte Daten in Anytwo erstellen'],
    'Aucune écriture en mode démo':['No writes in demo mode','Keine Schreibvorgänge im Demomodus'],
    'Tout l’espace':['Entire space','Gesamter Bereich'],
    'Chaque source de données devient une collection avec son supertag et ses propriétés. Les pages membres reçoivent ce supertag ; les pages ordinaires restent des pages.':['Each data source becomes a collection with its supertag and properties. Member pages receive this supertag; ordinary pages stay pages.','Jede Datenquelle wird zu einer Sammlung mit ihrem Supertag und ihren Eigenschaften. Mitgliedsseiten erhalten dieses Supertag; normale Seiten bleiben Seiten.'],
    'Vérifiez Anytwo pour choisir ou créer un espace.':['Check Anytwo to choose or create a space.','Prüfen Sie Anytwo, um einen Bereich zu wählen oder zu erstellen.'],
    'Configurez votre jeton Notion pour continuer.':['Configure your Notion token to continue.','Konfigurieren Sie Ihr Notion-Token, um fortzufahren.'],
    'Saisissez le jeton et autorisez le contenu dans Notion.':['Enter the token and authorize content in Notion.','Geben Sie das Token ein und geben Sie Inhalte in Notion frei.'],
    'Notion connecté · Anytwo à vérifier':['Notion connected · Anytwo to check','Notion verbunden · Anytwo zu prüfen'],
    'nom à renseigner':['name to fill in','Name erforderlich'],
    'Notion · Source':['Notion · Source','Notion · Quelle'],
    'Anytwo · Destination':['Anytwo · Destination','Anytwo · Ziel'],
    'Templates':['Templates','Vorlagen'],
    'Propriétés globales':['Global properties','Globale Eigenschaften'],
    'Propriétés locales':['Local properties','Lokale Eigenschaften'],
    'Table des matières':['Table of contents','Inhaltsverzeichnis'],
    'Bookmarks':['Bookmarks','Lesezeichen'],
    'Vues / Queries':['Views / Queries','Ansichten / Abfragen'],
    'Certaines vues de collection':['Some collection views','Bestimmte Sammlungsansichten'],
    'Filtres avancés':['Advanced filters','Erweiterte Filter'],
    'Collection et vues intégrées dans les pages':['Collections and views embedded in pages','In Seiten eingebettete Sammlungen und Ansichten'],
    'Propriétés intégrées à la page':['Properties embedded in pages','In Seiten eingebettete Eigenschaften'],
    'Discussions':['Discussions','Diskussionen'],
    'Le contenu de ces éléments pourra parfois être adapté ou conservé partiellement, mais pas nécessairement leur comportement ou leur présentation. La conversion réelle peut entraîner des adaptations ; consultez le bilan de chaque import.':['Some content may be adapted or partially preserved, but not its original behavior or presentation. Review each migration report.','Einige Inhalte können angepasst oder teilweise übernommen werden, jedoch nicht unbedingt ihre Funktionsweise oder Darstellung. Prüfen Sie jeden Importbericht.'],
    'Compris':['Understood','Verstanden'],
    'Connexion aux applications':['Connect to applications','Verbindung zu den Anwendungen'],
    'Vérification des accès locaux avant de charger vos espaces.':['Checking local access before loading your spaces.','Lokaler Zugriff wird geprüft, bevor die Bereiche geladen werden.'],
    'En attente de vérification':['Waiting for check','Prüfung ausstehend'],
    'Action nécessaire':['Action required','Aktion erforderlich'],
    'Lancez les applications concernées, puis vérifiez les paramètres ci-dessous.':['Open both applications and check the settings below.','Starten Sie beide Anwendungen und prüfen Sie die Einstellungen unten.'],
    'Client any.exe ouvert requis':['any.exe must be running','any.exe muss gestartet sein'],
    'Port HTTP':['HTTP port','HTTP-Port'],
    'Port habituel : 31310. La détection automatique essaye aussi les autres ports connus et celui du processus any.exe si possible.':['Usual port: 31310. Automatic detection also checks other known ports and, where possible, the any.exe process.','Üblicher Port: 31310. Die automatische Erkennung prüft auch andere bekannte Ports und nach Möglichkeit den Prozess any.exe.'],
    'Client ouvert + autorisation API requise':['Application running + API authorization required','Anwendung geöffnet + API-Autorisierung erforderlich'],
    'Autoriser dans Anytype':['Authorize in Anytype','In Anytype autorisieren'],
    'ou':['or','oder'],
    'Saisir une clé API':['Enter an API key','API-Schlüssel eingeben'],
    'Le code s’affiche dans Anytype, pas dans ce navigateur. Revenez ici (Alt+Tab sous Windows) et saisissez les quatre chiffres :':['The code appears in Anytype, not this browser. Return here (Alt+Tab on Windows) and enter the four digits:','Der Code erscheint in Anytype, nicht in diesem Browser. Kehren Sie hierher zurück (Alt+Tab unter Windows) und geben Sie die vier Ziffern ein:'],
    'Valider le code':['Confirm code','Code bestätigen'],
    'Une petite fenêtre de navigateur distincte vous aidera à saisir le code. L’autorisation sera mémorisée sur cet ordinateur.':['A separate browser window helps you enter the code. Authorization is saved on this computer.','Ein separates Browserfenster hilft bei der Codeeingabe. Die Autorisierung wird auf diesem Computer gespeichert.'],
    '↻  Enregistrer et vérifier':['↻  Save and check','↻  Speichern und prüfen'],
    'Continuer →':['Continue →','Weiter →'],
    'SIMULATION':['SIMULATION','SIMULATION'],
    'Vérification de l’import':['Import preview','Importvorschau'],
    'Analyse des éléments sélectionnés…':['Analyzing selected items…','Ausgewählte Elemente werden analysiert …'],
    'Exporter le bilan JSON':['Export JSON report','JSON-Bericht exportieren'],
    'Fermer':['Close','Schließen'],
    'CONNEXION SÉCURISÉE':['SECURE CONNECTION','SICHERE VERBINDUNG'],
    'Autoriser l’accès à Anytype':['Authorize access to Anytype','Zugriff auf Anytype autorisieren'],
    'L’application Anytype vous demande de choisir les espaces autorisés, puis affiche un code à quatre chiffres.':['Anytype asks you to select the permitted spaces and then displays a four-digit code.','Anytype fordert Sie auf, die freigegebenen Bereiche auszuwählen, und zeigt danach einen vierstelligen Code an.'],
    'Où saisir ce code ?':['Where do I enter the code?','Wo gebe ich den Code ein?'],
    'Ici, dans cette petite fenêtre. Si Anytype passe au premier plan, revenez à cette fenêtre avec':['Here, in this small window. If Anytype comes to the foreground, return to this window with','Hier in diesem kleinen Fenster. Wenn Anytype im Vordergrund erscheint, wechseln Sie zurück mit'],
    '(Windows). Vous pouvez laisser Anytype ouvert derrière.':['(Windows). You can leave Anytype open in the background.','(Windows). Anytype kann im Hintergrund geöffnet bleiben.'],
    'Code affiché dans Anytype':['Code displayed in Anytype','In Anytype angezeigter Code'],
    'Initialisation de la demande…':['Initializing request…','Anfrage wird initialisiert …'],
    'Autoriser l’accès':['Authorize access','Zugriff erlauben'],
    'Relancer la demande':['Retry request','Anfrage erneut senden'],
    'Le code ne peut pas être lu automatiquement par l’API : cette validation protège l’accès à vos données. Anytype peut afficher le nom du processus « Python » lorsque l’outil est lancé comme script.':['The API cannot read the code automatically. This confirmation protects your data. Anytype may display “Python” as the process name when the tool runs as a script.','Die API kann den Code nicht automatisch auslesen. Diese Bestätigung schützt Ihre Daten. Anytype zeigt möglicherweise „Python“ als Prozessnamen an, wenn das Tool als Skript ausgeführt wird.'],
    'Nom de l’espace':['Space name','Bereichsname'],
    'Nom de la collection':['Collection name','Name der Sammlung'],
    'Nom de la nouvelle collection':['New collection name','Name der neuen Sammlung'],
    'Rechercher un type ou un objet…':['Search for a type or object…','Typ oder Objekt suchen …'],
    'Coller la clé API Anytype':['Paste your Anytype API key','Anytype-API-Schlüssel einfügen'],
    'État des API':['API status','API-Status'],
    'Langue':['Language','Sprache'],
    'Langue de l’interface':['Interface language','Sprache der Benutzeroberfläche'],
    'Différence entre les modes':['Difference between import modes','Unterschied zwischen den Importmodi'],
    'Relire les espaces, collections et objets depuis les API':['Reload spaces, collections and objects from the APIs','Bereiche, Sammlungen und Objekte über die APIs neu laden'],
    'Espace source':['Source space','Quellbereich'],
    'Avertissement sur la compatibilité':['Compatibility warning','Kompatibilitätswarnung'],
    'Fermer les paramètres':['Close settings','Einstellungen schließen'],
    'Choisissez un espace':['Choose a space','Bereich auswählen'],
    'Aucun objet':['No objects','Keine Objekte'],
    'Aucun type correspondant':['No matching types','Keine passenden Typen'],
    'Aucune collection':['No collections','Keine Sammlungen'],
    'Aucun espace autorisé ou disponible.':['No authorized or available spaces.','Keine freigegebenen oder verfügbaren Bereiche.'],
    'Lecture des objets, des types et des collections de cet espace…':['Reading objects, types and collections in this space…','Objekte, Typen und Sammlungen dieses Bereichs werden gelesen …'],
    'Espace complet':['Entire space','Gesamter Bereich'],
    'Sélection d’objets individuels':['Individual object selection','Einzelne Objekte ausgewählt'],
    'Créer un nouvel espace…':['Create a new space…','Neuen Bereich erstellen …'],
    'Créer une nouvelle collection':['Create a new collection','Neue Sammlung erstellen'],
    'Sans collection (aucune propriété identifiée)':['No collection (no properties identified)','Ohne Sammlung (keine Eigenschaften erkannt)'],
    'Un espace Anytwo existant sera réutilisé.':['An existing Anytwo space will be reused.','Ein vorhandener Anytwo-Bereich wird wiederverwendet.'],
    'Le nouvel espace ne sera pas créé pendant le test.':['The new space will not be created during the test.','Der neue Bereich wird beim Test nicht erstellt.'],
    'Les objets sélectionnés ayant des propriétés (ou un statut indéterminé) doivent rejoindre une collection de leur type. Les autres objets restent hors collection.':['Selected objects with properties (or an unknown status) must be placed in a collection for their type. Other objects remain outside collections.','Ausgewählte Objekte mit Eigenschaften (oder unbekanntem Status) müssen einer Sammlung ihres Typs zugeordnet werden. Andere bleiben außerhalb von Sammlungen.'],
    'Une collection est obligatoire dès que des propriétés existent ou que leur absence ne peut être confirmée. Les types sans propriétés identifiées peuvent rester hors collection.':['A collection is required when properties exist or cannot be ruled out. Types without identified properties may stay outside collections.','Eine Sammlung ist erforderlich, wenn Eigenschaften vorhanden sind oder nicht ausgeschlossen werden können. Typen ohne erkannte Eigenschaften können außerhalb von Sammlungen bleiben.'],
    'Propriétés détectées : collection obligatoire.':['Properties detected: collection required.','Eigenschaften erkannt: Sammlung erforderlich.'],
    'Propriétés non vérifiables à ce stade : collection conseillée pour éviter toute perte.':['Properties cannot be checked yet: collection recommended to prevent data loss.','Eigenschaften noch nicht überprüfbar: Sammlung empfohlen, um Datenverlust zu vermeiden.'],
    'Import désactivé en mode démonstration.':['Import disabled in demo mode.','Import im Demomodus deaktiviert.'],
    'Synchronisation en cours de développement : utilisez Import simple.':['Synchronization is under development: use Simple import.','Synchronisierung in Entwicklung: Verwenden Sie den einfachen Import.'],
    'L’import crée des données dans Anytwo après confirmation. Tester ne modifie rien.':['Import creates data in Anytwo after confirmation. Testing does not modify anything.','Nach Bestätigung erstellt der Import Daten in Anytwo. Der Test ändert nichts.'],
    'API indisponibles : consultation uniquement.':['APIs unavailable: preview only.','APIs nicht verfügbar: nur Vorschau.'],
    'Vous pouvez parcourir l’interface et changer de langue, mais les données ne peuvent pas être chargées et les imports sont désactivés. Cliquez sur le statut API en haut à droite pour réessayer.':['You can explore the interface and change languages, but data cannot be loaded and imports are disabled. Click the API status at the top right to retry.','Sie können die Oberfläche ansehen und die Sprache wechseln, aber Daten können nicht geladen und Importe nicht ausgeführt werden. Klicken Sie oben rechts auf den API-Status, um es erneut zu versuchen.'],
    '⚠ API indisponibles':['⚠ APIs unavailable','⚠ APIs nicht verfügbar'],
    'API indisponibles : l’interface reste consultable, mais aucun test ou import n’est possible.':['APIs unavailable: you can preview the interface, but tests and imports are disabled.','APIs nicht verfügbar: Sie können die Oberfläche ansehen, aber Tests und Importe sind deaktiviert.'],
    'Attention : accès aux API indisponible. Ouvrir les paramètres':['Warning: API access unavailable. Open settings','Achtung: API-Zugriff nicht verfügbar. Einstellungen öffnen'],
    'Attention : API indisponibles — ouvrir les paramètres':['Warning: APIs unavailable — open settings','Achtung: APIs nicht verfügbar — Einstellungen öffnen'],
    'APIs connectées':['APIs connected','APIs verbunden'],
    'Connexion à configurer':['Connection needs configuration','Verbindung muss eingerichtet werden'],
    'Vérification en cours…':['Checking…','Prüfung läuft …'],
    'Vérification accès Anytwo…':['Checking Anytwo access…','Anytwo-Zugriff wird geprüft …'],
    'Vérification accès Anytype…':['Checking Anytype access…','Anytype-Zugriff wird geprüft …'],
    'action requise — ':['action required — ','Aktion erforderlich — '],
    'Espaces, collections et éléments actualisés.':['Spaces, collections and items refreshed.','Bereiche, Sammlungen und Elemente aktualisiert.'],
    'Paramètres de connexion':['Connection settings','Verbindungseinstellungen'],
    'Modifiez les ports ou l’autorisation, puis cliquez sur « Enregistrer et vérifier ».':['Change the ports or authorization, then click “Save and check”.','Ändern Sie Ports oder Autorisierung und klicken Sie auf „Speichern und prüfen“.'],
    'Configurez les deux accès pour continuer.':['Configure both connections to continue.','Konfigurieren Sie beide Verbindungen, um fortzufahren.'],
    'Demande envoyée. Choisissez les autorisations dans Anytype, puis saisissez le code ici.':['Request sent. Choose the permissions in Anytype, then enter the code here.','Anfrage gesendet. Wählen Sie die Berechtigungen in Anytype und geben Sie dann hier den Code ein.'],
    'Envoi de la demande à Anytype…':['Sending request to Anytype…','Anfrage wird an Anytype gesendet …'],
    'Anytype n’a pas retourné de challenge_id.':['Anytype did not return a challenge_id.','Anytype hat keine challenge_id zurückgegeben.'],
    'Le code doit contenir exactement quatre chiffres.':['The code must contain exactly four digits.','Der Code muss genau vier Ziffern enthalten.'],
    'Vérification du code…':['Checking code…','Code wird geprüft …'],
    'Accès autorisé et enregistré. Vous pouvez fermer cette fenêtre.':['Access authorized and saved. You can close this window.','Zugriff autorisiert und gespeichert. Sie können dieses Fenster schließen.'],
    'Importé':['Imported','Importiert'],
    'Import partiel':['Partially imported','Teilweise importiert'],
    'Échec':['Failed','Fehlgeschlagen'],
    'Incompatibilités regroupées':['Grouped incompatibilities','Zusammengefasste Inkompatibilitäten'],
    'IMPORT RÉEL':['REAL IMPORT','ECHTER IMPORT'],
    'Import Anytype → Anytwo':['Anytype → Anytwo import','Anytype → Anytwo Import'],
    'Import en cours : ne fermez pas cette fenêtre.':['Import in progress: do not close this window.','Import läuft: Schließen Sie dieses Fenster nicht.'],
    'Simulation terminée · aucun changement appliqué.':['Simulation complete · no changes made.','Simulation abgeschlossen · keine Änderungen vorgenommen.'],
    'Import terminé · bilan ci-dessous.':['Import complete · report below.','Import abgeschlossen · Bericht unten.'],
    'Simulation interrompue par une erreur.':['Simulation stopped due to an error.','Simulation wegen eines Fehlers abgebrochen.'],
    'Impossible de terminer la simulation.':['Could not complete the simulation.','Simulation konnte nicht abgeschlossen werden.'],
    'Import interrompu · modifications partielles possibles.':['Import interrupted · partial changes may exist.','Import unterbrochen · Teiländerungen möglich.'],
    'Erreur : ':['Error: ','Fehler: '],
    'Contenu non reproduit : ':['Content not reproduced: ','Inhalt nicht reproduziert: '],
    'ID Anytwo : ':['Anytwo ID: ','Anytwo-ID: '],
    'Attention : certains éléments Notion ne pourront pas être importés dans Anytwo.':['Warning: some Notion items cannot be imported into Anytwo.','Achtung: Einige Notion-Elemente können nicht nach Anytwo importiert werden.'],
    'Choisissez précisément ce que vous souhaitez transférer depuis Notion vers Anytwo.':['Choose exactly what to transfer from Notion to Anytwo.','Wählen Sie genau aus, was von Notion nach Anytwo übertragen werden soll.'],
    'Types':['Types','Typen'],
    'Templates':['Templates','Vorlagen'],
    'Bookmarks':['Bookmarks','Lesezeichen'],
    'Discussions':['Discussions','Diskussionen'],
    'Importer dans Anytwo ?\n\nDes espaces, collections, propriétés et objets vont être créés ou complétés. Aucun retour arrière automatique.\n\nIl est conseillé de commencer par un espace de test.':['Import into Anytwo?\n\nSpaces, collections, properties and objects will be created or updated. There is no automatic rollback.\n\nIt is best to start with a test space.','Nach Anytwo importieren?\n\nBereiche, Sammlungen, Eigenschaften und Objekte werden erstellt oder ergänzt. Kein automatisches Zurücksetzen.\n\nBeginnen Sie am besten mit einem Testbereich.'],
    'Source des données':['Data source','Datenquelle'],
    'ESPACE NOTION':['NOTION SPACE','NOTION-BEREICH'],
    'Choisir un espace…':['Choose a space…','Bereich wählen …'],
    'Ce jeton donne accès à un seul espace. Seul le contenu autorisé est proposé.':['This token grants access to a single space. Only authorized content is offered.','Dieses Token gewährt Zugriff auf einen Bereich. Es wird nur freigegebener Inhalt angeboten.'],
    'Tout sélectionner dans cet espace':['Select everything in this space','Alles in diesem Bereich auswählen'],
    'Toutes les racines accessibles et leurs descendants':['All accessible roots and their descendants','Alle verfügbaren Wurzeln und ihre Unterelemente'],
    'Validez la connexion pour charger les éléments accessibles.':['Validate the connection to load accessible items.','Bestätigen Sie die Verbindung, um verfügbare Elemente zu laden.'],
    'Sélection sur trois niveaux : racine → niveau 1 → niveau 2. Cocher un élément inclut tous ses descendants, même ceux qui ne sont pas affichés. Les niveaux plus profonds ne sont pas sélectionnables individuellement.':['Three-level selection: root → level 1 → level 2. Checking an item includes all its descendants, even those not displayed. Deeper levels cannot be selected individually.','Auswahl auf drei Ebenen: Wurzel → Ebene 1 → Ebene 2. Das Ankreuzen eines Elements schließt alle Unterelemente ein, auch nicht angezeigte. Tiefere Ebenen sind nicht einzeln auswählbar.'],
    'Ajouter un élément par son lien ou identifiant':['Add an item by link or ID','Element per Link oder ID hinzufügen'],
    'Ajouter':['Add','Hinzufügen'],
    'Sélectionnez un espace, une page ou une base à gauche pour configurer sa destination.':['Select a space, page or database on the left to configure its destination.','Wählen Sie links einen Bereich, eine Seite oder eine Datenbank aus, um das Ziel festzulegen.'],
    'Destination Anytwo à vérifier':['Anytwo destination to check','Zu prüfendes Anytwo-Ziel'],
    'COLLECTIONS ET PROPRIÉTÉS':['COLLECTIONS AND PROPERTIES','SAMMLUNGEN UND EIGENSCHAFTEN'],
    'Les bases intégrées seront affichées par une vue inline dans leur page, avec leurs filtres, tris et propriétés compatibles.':['Embedded databases are shown as an inline view in their page, with compatible filters, sorts and properties.','Eingebettete Datenbanken werden als Inline-Ansicht in ihrer Seite angezeigt, mit kompatiblen Filtern, Sortierungen und Eigenschaften.'],
    'Importer les éléments liés hors de l’arborescence':['Import linked items outside the tree','Verknüpfte Elemente außerhalb des Baums importieren'],
    'Les descendants des éléments choisis sont toujours inclus. Cette option étend le périmètre aux pages liées.':['Descendants of selected items are always included. This option extends the scope to linked pages.','Unterelemente ausgewählter Elemente sind immer enthalten. Diese Option erweitert den Umfang auf verknüpfte Seiten.'],
    'Vérifier la sélection et sa compatibilité sans écriture':['Check the selection and its compatibility without writing','Auswahl und Kompatibilität ohne Schreiben prüfen'],
    'Choisissez une sélection et une destination':['Choose a selection and a destination','Wählen Sie eine Auswahl und ein Ziel'],
    'Tester vérifie la sélection sans écriture. Importer crée une copie dans Anytwo ; Notion reste inchangé. Une interruption conserve les éléments déjà créés. Un nouvel import crée une copie supplémentaire.':['Test checks the selection without writing. Import creates a copy in Anytwo; Notion stays unchanged. An interruption keeps already created items. A new import creates another copy.','Testen prüft die Auswahl ohne Schreiben. Importieren erstellt eine Kopie in Anytwo; Notion bleibt unverändert. Eine Unterbrechung behält bereits erstellte Elemente. Ein neuer Import erstellt eine weitere Kopie.'],
    'Bilan de vérification Notion':['Notion check report','Notion-Prüfbericht'],
    'Préparation de l’analyse…':['Preparing analysis…','Analyse wird vorbereitet …'],
    'Lecture seule : aucune écriture dans Notion ou Anytwo.':['Read-only: no writes to Notion or Anytwo.','Nur Lesen: keine Schreibvorgänge in Notion oder Anytwo.'],
    'Annuler':['Cancel','Abbrechen'],
    'Traitement local · Notion reste en lecture seule · L’import modifie Anytwo':['Local processing · Notion stays read-only · Import changes Anytwo','Lokale Verarbeitung · Notion bleibt schreibgeschützt · Der Import ändert Anytwo'],
    'Fermer le chargement et continuer en arrière-plan':['Close loading and continue in the background','Laden schließen und im Hintergrund fortfahren'],
    'Chargement des données Notion':['Loading Notion data','Notion-Daten werden geladen'],
    'Récupération des éléments de premier niveau…':['Retrieving top-level items…','Elemente der obersten Ebene werden abgerufen …'],
    'Vous pouvez fermer cette fenêtre pour faire autre chose. La recherche continue en arrière-plan.':['You can close this window to do something else. The search continues in the background.','Sie können dieses Fenster schließen und etwas anderes tun. Die Suche läuft im Hintergrund weiter.'],
    'Continuer sans attendre':['Continue without waiting','Ohne Warten fortfahren'],
    'Connexion à Notion et Anytwo':['Notion and Anytwo connection','Verbindung zu Notion und Anytwo'],
    'Notion via Internet · Anytwo sur cet ordinateur':['Notion over the Internet · Anytwo on this computer','Notion über das Internet · Anytwo auf diesem Computer'],
    'Configurez les accès aux applications.':['Configure access to the applications.','Konfigurieren Sie den Zugang zu den Anwendungen.'],
    'Jeton de connexion interne Notion':['Notion internal connection token','Internes Verbindungs-Token von Notion'],
    'Saisir le jeton ici, jamais dans le chat':['Enter the token here, never in the chat','Token hier eingeben, niemals im Chat'],
    'Un jeton mémorisé est disponible sur cet ordinateur. Vous pouvez valider la connexion sans le saisir à nouveau.':['A remembered token is available on this computer. You can validate the connection without entering it again.','Auf diesem Computer ist ein gemerktes Token verfügbar. Sie können die Verbindung ohne erneute Eingabe bestätigen.'],
    'Mémoriser sur cet ordinateur (protection Windows)':['Remember on this computer (Windows protection)','Auf diesem Computer merken (Windows-Schutz)'],
    'Valider la connexion':['Validate connection','Verbindung bestätigen'],
    'Oublier le jeton':['Forget token','Token vergessen'],
    'Non connecté.':['Not connected.','Nicht verbunden.'],
    'Connexion à l’API Notion via Internet : l’application Notion peut rester fermée.':['Notion API connection over the Internet: the Notion app can stay closed.','Notion-API-Verbindung über das Internet: die Notion-App kann geschlossen bleiben.'],
    'Comment autoriser le contenu ?':['How to authorize content?','Wie wird Inhalt freigegeben?'],
    'Créez une connexion interne Any2Any dans le portail développeur Notion, avec la capacité de lecture du contenu. Dans « Content access », autorisez les pages et bases voulues. Aucun droit d’insertion ou de modification n’est nécessaire.':['Create an Any2Any internal connection in the Notion developer portal with the read content capability. In “Content access”, authorize the pages and databases you need. No insert or update permission is required.','Erstellen Sie im Notion-Entwicklerportal eine interne Any2Any-Verbindung mit der Berechtigung zum Lesen von Inhalten. Erlauben Sie unter „Content access“ die gewünschten Seiten und Datenbanken. Eine Schreibberechtigung ist nicht erforderlich.'],
    'Guide officiel Notion':['Official Notion guide','Offizieller Notion-Leitfaden'],
    'Sans mémorisation, le jeton reste uniquement dans la session du serveur local. Une connexion interne est propre à un espace Notion.':['Without remembering, the token stays only in the local server session. An internal connection belongs to a single Notion space.','Ohne Merken bleibt das Token nur in der Sitzung des lokalen Servers. Eine interne Verbindung gehört zu einem Notion-Bereich.'],
    'Ouvrez Anytwo et autorisez son API locale pour choisir la destination.':['Open Anytwo and authorize its local API to choose the destination.','Öffnen Sie Anytwo und erlauben Sie die lokale API, um das Ziel zu wählen.'],
    'Port de l’API Anytwo':['Anytwo API port','Anytwo-API-Port'],
    'Détection automatique':['Automatic detection','Automatische Erkennung'],
    'Enregistrer et vérifier Anytwo':['Save and check Anytwo','Anytwo speichern und prüfen'],
    'Accès Anytwo à vérifier.':['Anytwo access to check.','Anytwo-Zugriff zu prüfen.'],
    'Afficher le chargement':['Show loading','Laden anzeigen'],
    'Continuer':['Continue','Weiter'],
    'Arborescence Notion':['Notion tree','Notion-Baum'],
    'Import depuis Notion':['Notion import','Import aus Notion'],
    'Import interrompu : le bilan ci-dessous est partiel. Les créations déjà effectuées ne sont pas annulées.':['Import interrupted: the report below is partial. Items already created are not rolled back.','Import unterbrochen: Der Bericht unten ist unvollständig. Bereits erstellte Elemente werden nicht zurückgesetzt.'],
    'Import interrompu · bilan partiel ci-dessous.':['Import interrupted · partial report below.','Import unterbrochen · unvollständiger Bericht unten.'],
    'Import interrompu : modifications partielles possibles.':['Import interrupted: partial changes may exist.','Import unterbrochen: Teiländerungen möglich.'],
    'Import interrompu · modifications partielles possibles.':['Import interrupted · partial changes may exist.','Import unterbrochen · Teiländerungen möglich.'],
    'Lecture des données, simulation en cours…':['Reading data, simulation in progress…','Daten werden gelesen, Simulation läuft …'],
  };
  const params=[
    [/^Créer l’espace « (.*) »$/,(v,l)=>l==='en'?`Create space “${v}”`:`Bereich „${v}“ erstellen`],
    [/^Espace existant · (.*)$/,(v,l)=>l==='en'?`Existing space · ${v}`:`Vorhandener Bereich · ${v}`],
    [/^Collection existante · (.*)$/,(v,l)=>l==='en'?`Existing collection · ${v}`:`Vorhandene Sammlung · ${v}`],
    [/^Importer tous les objets de (.*)$/,(v,l)=>l==='en'?`Import all objects of ${v}`:`Alle Objekte von ${v} importieren`],
    [/^Voir les objets de (.*)$/,(v,l)=>l==='en'?`View objects of ${v}`:`Objekte von ${v} anzeigen`],
    [/^(\d+) objet\(s\)$/,(v,l)=>l==='en'?`${v} object(s)`:`${v} Objekt(e)`],
    [/^(\d+) type\(s\) sélectionné\(s\)$/,(v,l)=>l==='en'?`${v} type(s) selected`:`${v} Typ(en) ausgewählt`],
    [/^(\d+) objets · (\d+) collections · (\d+) types\. Les types incluent aussi les objets présents dans des collections\.$/,(a,b,c,l)=>l==='en'?`${a} objects · ${b} collections · ${c} types. Types also include objects belonging to collections.`:`${a} Objekte · ${b} Sammlungen · ${c} Typen. Typen umfassen auch Objekte in Sammlungen.`],
    [/^(\d+) événement\(s\)$/,(v,l)=>l==='en'?`${v} events`:`${v} Ereignisse`],
    [/^(\d+) événement$/,(v,l)=>l==='en'?`${v} event`:`${v} Ereignis`],
    [/^Bilan : (\d+) objet\(s\), (\d+) complet\(s\), (\d+) partiel\(s\), (\d+) erreur\(s\)$/,(a,b,c,d,l)=>l==='en'?`Report: ${a} objects, ${b} complete, ${c} partial, ${d} errors`:`Bericht: ${a} Objekte, ${b} vollständig, ${c} teilweise, ${d} Fehler`],
    [/^(.+) — (importé|partiel|échec) · (\d+) adaptation\(s\), (\d+) erreur\(s\)$/,(n,s,a,e,l)=>{const st=l==='en'?({['importé']:'imported',['partiel']:'partial',['échec']:'failed'})[s]:({['importé']:'importiert',['partiel']:'teilweise',['échec']:'fehlgeschlagen'})[s];return l==='en'?`${n} — ${st} · ${a} adaptation(s), ${e} error(s)`:`${n} — ${st} · ${a} Anpassung(en), ${e} Fehler`;}],
    [/^Espace Anytwo : (.+) \((créé|existant)\)\.$/,(n,s,l)=>{const st=l==='en'?(s==='créé'?'created':'existing'):(s==='créé'?'erstellt':'vorhanden');return l==='en'?`Anytwo space: ${n} (${st}).`:`Anytwo-Bereich: ${n} (${st}).`;}],
    [/^Lecture de (\d+) objets source · (\d+) avertissement\(s\)\.$/,(a,b,l)=>l==='en'?`Reading ${a} source objects · ${b} warning(s).`:`${a} Quellobjekte werden gelesen · ${b} Warnung(en).`],
    [/^Créé : (.+)$/,(n,l)=>l==='en'?`Created: ${n}`:`Erstellt: ${n}`],
    [/^! Création impossible « (.+) » : ([\s\S]+)$/,(n,e,l)=>l==='en'?`! Could not create “${n}”: ${e}`:`! Erstellen von „${n}“ nicht möglich: ${e}`],
    [/^Collection « (.+) » → (.+)$/,(n,id,l)=>l==='en'?`Collection “${n}” → ${id}`:`Sammlung „${n}“ → ${id}`],
    [/^(\d+) chat\(s\) à importer en archives\.$/,(n,l)=>l==='en'?`${n} chat(s) to import as archives.`:`${n} Chat(s) als Archive zu importieren.`],
    [/^Overview Anytwo : (\d+) widget\(s\) ajouté\(s\), (\d+) déjà présent\(s\)\.$/,(a,b,l)=>l==='en'?`Anytwo Overview: ${a} widget(s) added, ${b} already present.`:`Anytwo-Overview: ${a} Widget(s) hinzugefügt, ${b} bereits vorhanden.`],
    [/^Propriétés techniques Anytype retirées : (.+)\.$/,(n,l)=>l==='en'?`Anytype bookkeeping properties removed: ${n}.`:`Anytype-Hilfseigenschaften entfernt: ${n}.`],
    [/^! ([\s\S]+)$/,(m,l)=>l==='en'?`! ${m}`:`! ${m}`],
    [/^Erreur générale : ([\s\S]+)$/,(m,l)=>l==='en'?`General error: ${m}`:`Allgemeiner Fehler: ${m}`],
    [/^Contenu non reproduit : ([\s\S]+)$/,(m,l)=>l==='en'?`Content not reproduced: ${m}`:`Inhalt nicht reproduziert: ${m}`],
    [/^Erreur : ([\s\S]+)$/,(m,l)=>l==='en'?`Error: ${m}`:`Fehler: ${m}`],
    [/^ID Anytype : (.+)$/,(m,l)=>l==='en'?`Anytype ID: ${m}`:`Anytype-ID: ${m}`],
    [/^Sélectionné via l’espace « (.+) »$/,(n,l)=>l==='en'?`Selected through the space “${n}”`:`Über den Bereich „${n}“ ausgewählt`],
    [/^Sélectionné via la collection « (.+) »$/,(n,l)=>l==='en'?`Selected through the collection “${n}”`:`Über die Sammlung „${n}“ ausgewählt`],
    [/^Sélectionné via le type « (.+) »$/,(n,l)=>l==='en'?`Selected through the type “${n}”`:`Über den Typ „${n}“ ausgewählt`],
    [/^Sélectionné individuellement$/,(l)=>l==='en'?'Selected individually':'Einzeln ausgewählt'],
    [/^Lié à « (.+) »$/,(n,l)=>l==='en'?`Linked to “${n}”`:`Verknüpft mit „${n}“`],
    [/^Document de la vue intégrée de « (.+) »$/,(n,l)=>l==='en'?`Document of the inline view of “${n}”`:`Dokument der Inline-Ansicht von „${n}“`],
    [/^Lié indirectement à la sélection$/,(l)=>l==='en'?'Indirectly linked to the selection':'Indirekt mit der Auswahl verknüpft'],
    [/^Option archive des chats de l’espace source$/,(l)=>l==='en'?'Source space chat archive option':'Archivoption für Chats des Quellbereichs'],
    [/^Propriété « (.+) » conservée en texte \(format non transposable\)$/,(n,l)=>l==='en'?`Property “${n}” kept as text (format cannot be mapped)`:`Eigenschaft „${n}“ als Text beibehalten (Format nicht übertragbar)`],
    [/^Référence externe dans la propriété « (.+) » conservée en texte$/,(n,l)=>l==='en'?`External reference in property “${n}” kept as text`:`Externe Referenz in Eigenschaft „${n}“ als Text beibehalten`],
    [/^Restriction de types de « (.+) » archivée : certains types cibles ne sont pas importés$/,(n,l)=>l==='en'?`Type restriction of “${n}” archived: some target types are not imported`:`Typeinschränkung von „${n}“ archiviert: Einige Zieltypen werden nicht importiert`],
    [/^Propriété « (.+) » : même nom mais format différent dans la collection cible$/,(n,l)=>l==='en'?`Property “${n}”: same name but a different format in the target collection`:`Eigenschaft „${n}“: gleicher Name, aber anderes Format in der Zielsammlung`],
    [/^Couleur des cellules du tableau non reproduite$/,(l)=>l==='en'?'Table cell color not reproduced':'Zellfarbe der Tabelle nicht reproduziert'],
    [/^Couleur d’arrière-plan de bloc$/,(l)=>l==='en'?'Block background color':'Hintergrundfarbe des Blocks'],
    [/^Couverture ajoutée dans la page \(présentation d’origine non reproduite\)$/,(l)=>l==='en'?'Cover added inside the page (original presentation not reproduced)':'Titelbild in die Seite eingefügt (ursprüngliche Darstellung nicht reproduziert)'],
    [/^Propriété intégrée à la page non reproduite$/,(l)=>l==='en'?'Property embedded in the page not reproduced':'In die Seite eingebettete Eigenschaft nicht reproduziert'],
    [/^Collection \/ vue intégrée non reproduite$/,(l)=>l==='en'?'Embedded collection / view not reproduced':'Eingebettete Sammlung / Ansicht nicht reproduziert'],
    [/^Disposition en colonnes simplifiée$/,(l)=>l==='en'?'Column layout simplified':'Spaltenlayout vereinfacht'],
    [/^Disposition en colonnes non reconstruite : contenu conservé en séquence$/,(l)=>l==='en'?'Column layout not rebuilt: content kept in sequence':'Spaltenlayout nicht rekonstruiert: Inhalt in Reihenfolge beibehalten'],
    [/^Colonnes préservées en HTML \(rendu à vérifier dans Anytwo\)$/,(l)=>l==='en'?'Columns preserved as HTML (rendering to check in Anytwo)':'Spalten als HTML beibehalten (Darstellung in Anytwo prüfen)'],
    [/^Vue limitée au périmètre importé : (\d+) membre\(s\) source non importé\(s\)$/,(n,l)=>l==='en'?`View limited to the imported scope: ${n} source member(s) not imported`:`Ansicht auf den importierten Umfang begrenzt: ${n} Quellmitglied(er) nicht importiert`],
    [/^Vue non convertie : ([\s\S]+)$/,(m,l)=>l==='en'?`View not converted: ${m}`:`Ansicht nicht konvertiert: ${m}`],
    [/^Largeur relative d’image approximée sur une largeur de bloc de référence de (\d+) px$/,(n,l)=>l==='en'?`Relative image width approximated on a ${n} px reference block`:`Relative Bildbreite auf einen Referenzblock von ${n} px angenähert`],
    [/^Soulignement\/exposant\/indice non pris en charge par l’import Markdown Anytwo : texte conservé sans balises$/,(l)=>l==='en'?'Underline/superscript/subscript not supported by the Anytwo Markdown import: text kept without tags':'Unterstreichung/Hoch-/Tiefstellung vom Anytwo-Markdown-Import nicht unterstützt: Text ohne Tags beibehalten'],
    [/^Fichiers non importés \(option désactivée\)$/,(l)=>l==='en'?'Files not imported (option disabled)':'Dateien nicht importiert (Option deaktiviert)'],
    [/^Valeur vide ignorée pour la propriété « (.+) »$/,(n,l)=>l==='en'?`Empty value ignored for property “${n}”`:`Leerer Wert für Eigenschaft „${n}“ ignoriert`],
    [/^Valeur non absolue pour « (.+) » conservée en texte$/,(n,l)=>l==='en'?`Non-absolute value for “${n}” kept as text`:`Nicht absoluter Wert für „${n}“ als Text beibehalten`],
    [/^Mention vers un objet non importé$/,(l)=>l==='en'?'Mention of an object that was not imported':'Erwähnung eines nicht importierten Objekts'],
    [/^Lien vers un objet non importé$/,(l)=>l==='en'?'Link to an object that was not imported':'Link zu einem nicht importierten Objekt'],
    [/^API connectée, accès autorisé\.$/,(l)=>l==='en'?'API connected, access authorized.':'API verbunden, Zugriff autorisiert.'],
    [/^API connectée sur le port (\d+) · (\d+) espace\(s\) visible\(s\)\.$/,(port,n,l)=>l==='en'?`API connected on port ${port} · ${n} visible space(s).`:`API verbunden auf Port ${port} · ${n} sichtbare(r) Bereich(e).`],
    // Prefixes are separate nodes; the renderer trims their trailing space.
    [/^Erreur :$/, (l)=>l==='en'?'Error: ':'Fehler: '],
    [/^Erreur générale :$/, (l)=>l==='en'?'General error: ':'Allgemeiner Fehler: '],
    [/^Contenu non reproduit :$/, (l)=>l==='en'?'Content not reproduced: ':'Inhalt nicht reproduziert: '],
    [/^ID Anytwo :$/, (l)=>l==='en'?'Anytwo ID: ':'Anytwo-ID: '],
    [/^ID Anytype :$/, (l)=>l==='en'?'Anytype ID: ':'Anytype-ID: '],
    [/^Propriété « (.+) » : ([\s\S]+)$/,(n,m,l)=>l==='en'?`Property “${n}”: ${m}`:`Eigenschaft „${n}“: ${m}`],
    [/^Fichier de propriété « (.+) » : ([\s\S]+)$/,(n,m,l)=>l==='en'?`Property file “${n}”: ${m}`:`Eigenschaftsdatei „${n}“: ${m}`],
    [/^(\d+) branches sélectionnées$/,(n,l)=>l==='en'?`${n} branches selected`:`${n} Zweige ausgewählt`],
    [/^(\d+) branche\(s\) sélectionnée\(s\), (\d+) exclusion\(s\)\. Les pages seront comptées lors de l’analyse\.$/,(a,b,l)=>l==='en'?`${a} branch(es) selected, ${b} exclusion(s). Pages are counted during analysis.`:`${a} Zweig(e) ausgewählt, ${b} Ausnahme(n). Seiten werden bei der Analyse gezählt.`],
    [/^(\d+) page\(s\) dans la sélection analysée\.$/,(n,l)=>l==='en'?`${n} page(s) in the analyzed selection.`:`${n} Seite(n) in der analysierten Auswahl.`],
    [/^Espace à créer : (.+)$/,(n,l)=>l==='en'?`Space to create: ${n}`:`Zu erstellender Bereich: ${n}`],
    [/^Espace existant : (.+)$/,(n,l)=>l==='en'?`Existing space: ${n}`:`Vorhandener Bereich: ${n}`],
    [/^· (\d+) occurrence\(s\)$/,(n,l)=>l==='en'?` · ${n} occurrence(s)`:` · ${n} Vorkommen`],
    [/^OPTIONS : fichiers (inclus|ignorés), liens (suivis|non suivis)\.$/,(f,li,l)=>l==='en'?`Options: files ${f==='inclus'?'included':'ignored'}, links ${li==='suivis'?'followed':'not followed'}.`:`Optionen: Dateien ${f==='inclus'?'eingeschlossen':'ignoriert'}, Links ${li==='suivis'?'verfolgt':'nicht verfolgt'}.`],
    [/^Bilan de vérification$/,(l)=>l==='en'?'Check report':'Prüfbericht'],
    [/^(.*) · (\d+) occurrence\(s\)$/,(a,b,l)=>l==='en'?`${a} · ${b} occurrence(s)`:`${a} · ${b} Vorkommen`],
  ];
  function detect(){let explicit='';try{explicit=localStorage.getItem(STORAGE_KEY)||'';}catch(e){}
    if(!explicit){try{explicit=localStorage.getItem(LEGACY_STORAGE_KEY)||'';}catch(e){}}
    if(['fr','en','de'].includes(explicit))return explicit;
    const raw=(navigator.language||'fr').slice(0,2).toLowerCase();return ['fr','en','de'].includes(raw)?raw:'fr';
  }
  let lang=detect();const originals=new WeakMap();const attrs=new WeakMap();
  // Messages produced by the migration engine. '{}' marks a runtime value so
  // object names and identifiers are reinserted verbatim.
  const templates={"Aperçu web externe conservé comme lien": ["External web preview kept as a link", "Externe Webvorschau als Link beibehalten"], "Bloc système ou widget non reproduit": ["System block or widget not reproduced", "Systemblock oder Widget nicht reproduziert"], "Bookmark converti en lien titré": ["Bookmark converted to a titled link", "Lesezeichen in einen betitelten Link umgewandelt"], "Chat / discussion ignoré (non importable)": ["Chat / discussion skipped (not importable)", "Chat / Diskussion ignoriert (nicht importierbar)"], "Cible de relation inaccessible ou ambiguë : références conservées en texte, sans relation non restreinte": ["Relation target inaccessible or ambiguous: references kept as text, without an unrestricted relation", "Relationsziel nicht erreichbar oder mehrdeutig: Referenzen als Text beibehalten, ohne uneingeschränkte Relation"], "Collection / vue intégrée non reproduite": ["Embedded collection / view not reproduced", "Eingebettete Sammlung / Ansicht nicht reproduziert"], "Collection intégrée adaptée en vue en ligne : {}": ["Embedded collection adapted to an inline view: {}", "Eingebettete Sammlung als Inline-Ansicht angepasst: {}"], "Colonne affichée non transposable : {}": ["Displayed column cannot be mapped: {}", "Angezeigte Spalte nicht übertragbar: {}"], "Colonne de vue supprimée ou inaccessible ignorée : {}": ["Removed or inaccessible view column ignored: {}", "Entfernte oder nicht erreichbare Ansichtsspalte ignoriert: {}"], "Colonnes préservées en HTML (rendu à vérifier dans Anytwo)": ["Columns preserved as HTML (rendering to check in Anytwo)", "Spalten als HTML beibehalten (Darstellung in Anytwo prüfen)"], "Configuration avancée de la collection source non vérifiable": ["Advanced source collection configuration cannot be verified", "Erweiterte Konfiguration der Quellsammlung nicht prüfbar"], "Contrôle de filtre vide sans propriété compatible : {}": ["Empty filter control without a compatible property: {}", "Leeres Filtersteuerelement ohne passende Eigenschaft: {}"], "Couleur différente pour « {} » dans la propriété existante « {} » : conservée": ["Different color for “{}” in the existing property “{}”: kept", "Abweichende Farbe für „{}“ in der vorhandenen Eigenschaft „{}“: beibehalten"], "Couleur d’arrière-plan de bloc": ["Block background color", "Hintergrundfarbe des Blocks"], "Couverture ajoutée dans la page (présentation d’origine non reproduite)": ["Cover added inside the page (original presentation not reproduced)", "Titelbild in die Seite eingefügt (ursprüngliche Darstellung nicht reproduziert)"], "Couverture conservée comme image en tête de page": ["Cover kept as an image at the top of the page", "Titelbild als Bild am Seitenanfang beibehalten"], "Couverture image non importée (option fichiers désactivée)": ["Cover image not imported (files option disabled)", "Titelbild nicht importiert (Dateioption deaktiviert)"], "Couverture image non importée : {}": ["Cover image not imported: {}", "Titelbild nicht importiert: {}"], "Date de plage non reconnue : valeur conservée dans le rapport": ["Unrecognized range date: value kept in the report", "Zeitraumdatum nicht erkannt: Wert im Bericht beibehalten"], "Disposition de vue en ligne adaptée en liste : {}": ["Inline view layout adapted to a list: {}", "Inline-Ansichtslayout als Liste angepasst: {}"], "Disposition en colonnes non reconstructible : contenu conservé en séquence": ["Column layout not rebuilt: content kept in sequence", "Spaltenlayout nicht rekonstruiert: Inhalt in Reihenfolge beibehalten"], "Disposition en colonnes simplifiée": ["Column layout simplified", "Spaltenlayout vereinfacht"], "Documents de vue intégrée non résolus : {}": ["Inline view documents not resolved: {}", "Inline-Ansichtsdokumente nicht aufgelöst: {}"], "Embed fournisseur non pris en charge : conservé comme lien": ["Unsupported provider embed: kept as a link", "Nicht unterstützte Anbieter-Einbettung: als Link beibehalten"], "Fichier imbriqué non importé (indisponible ou option désactivée)": ["Nested file not imported (unavailable or option disabled)", "Verschachtelte Datei nicht importiert (nicht verfügbar oder Option deaktiviert)"], "Fichier imbriqué non importé : {}": ["Nested file not imported: {}", "Verschachtelte Datei nicht importiert: {}"], "Fichier source non importé (option désactivée)": ["Source file not imported (option disabled)", "Quelldatei nicht importiert (Option deaktiviert)"], "Fichier source non importé : {}": ["Source file not imported: {}", "Quelldatei nicht importiert: {}"], "Fichiers non importés": ["Files not imported", "Dateien nicht importiert"], "Fichiers non importés (option désactivée)": ["Files not imported (option disabled)", "Dateien nicht importiert (Option deaktiviert)"], "Filtre sur formule conservé sur les résultats figés importés": ["Formula filter kept on the imported frozen results", "Formelfilter auf den importierten eingefrorenen Ergebnissen beibehalten"], "Filtres / tris hors définition de vue conservés dans le rapport": ["Filters / sorts outside the view definition kept in the report", "Filter / Sortierungen außerhalb der Ansichtsdefinition im Bericht beibehalten"], "Format numérique source inconnu archivé ; valeur conservée sans format d’affichage": ["Unknown source number format archived; value kept without display format", "Unbekanntes Quellzahlenformat archiviert; Wert ohne Anzeigeformat beibehalten"], "Formule : résultat figé ; expression archivée dans le descripteur": ["Formula: frozen result; expression archived in the descriptor", "Formel: eingefrorenes Ergebnis; Ausdruck im Deskriptor archiviert"], "Fuseau de plage indisponible : valeur conservée dans le rapport": ["Range time zone unavailable: value kept in the report", "Zeitzone des Zeitraums nicht verfügbar: Wert im Bericht beibehalten"], "Groupes du workflow Notion archivés ; choix simple importé": ["Notion workflow groups archived; simple choice imported", "Notion-Workflow-Gruppen archiviert; einfache Auswahl importiert"], "Icône image non appliquée": ["Image icon not applied", "Bildsymbol nicht angewendet"], "Intervalle/fuseau de date archivé dans le rapport ; seule la date de début est native": ["Date range/time zone archived in the report; only the start date is native", "Datumsbereich/Zeitzone im Bericht archiviert; nur das Startdatum ist nativ"], "Intégration externe « {} » remplacée par un lien": ["External “{}” embed replaced by a link", "Externe „{}“-Einbettung durch einen Link ersetzt"], "Intégration non reconnue : lien externe de remplacement": ["Unrecognized embed: external replacement link", "Einbettung nicht erkannt: externer Ersatzlink"], "Intégration « {} » non reproduite": ["“{}” embed not reproduced", "„{}“-Einbettung nicht reproduziert"], "Largeurs de colonnes archivées : réglage local du client Anytwo": ["Column widths archived: local setting of the Anytwo client", "Spaltenbreiten archiviert: lokale Einstellung des Anytwo-Clients"], "Lien Notion hors périmètre conservé comme lien vers la source": ["Out-of-scope Notion link kept as a link to the source", "Notion-Link außerhalb des Umfangs als Link zur Quelle beibehalten"], "Lien vers un chat / une discussion non importé": ["Link to a chat / discussion not imported", "Link zu einem Chat / einer Diskussion nicht importiert"], "Lien vers un objet non importé": ["Link to an object that was not imported", "Link zu einem nicht importierten Objekt"], "Mention vers un objet non importé": ["Mention of an object that was not imported", "Erwähnung eines nicht importierten Objekts"], "Mise en forme de chat non prise en charge : texte conservé sans balises": ["Chat formatting not supported: text kept without tags", "Chat-Formatierung nicht unterstützt: Text ohne Tags beibehalten"], "Mise en forme de propriété texte adaptée en texte brut": ["Rich property text adapted to plain text", "Formatierter Eigenschaftstext als Klartext angepasst"], "Objet lié à un chat non importé": ["Object linked to a chat not imported", "Mit einem Chat verknüpftes Objekt nicht importiert"], "Page enfant non importée": ["Child page not imported", "Unterseite nicht importiert"], "Paramètre {} de « {} » conservé en métadonnées, non appliqué": ["Setting {} of “{}” kept in metadata, not applied", "Einstellung {} von „{}“ in Metadaten beibehalten, nicht angewendet"], "Paramètres de la propriété existante « {} » différents : conservés sans modification": ["Settings of the existing property “{}” differ: kept unchanged", "Einstellungen der vorhandenen Eigenschaft „{}“ weichen ab: unverändert beibehalten"], "Personnes/auteurs conservés comme texte, sans comptes ni droits": ["People/authors kept as text, without accounts or permissions", "Personen/Autoren als Text beibehalten, ohne Konten oder Rechte"], "Pièce jointe de chat indisponible : {}": ["Chat attachment unavailable: {}", "Chat-Anhang nicht verfügbar: {}"], "Pièce jointe indisponible : {}": ["Attachment unavailable: {}", "Anhang nicht verfügbar: {}"], "Portée des propriétés Anytype non reproduite (valeurs reprises en colonnes)": ["Anytype property scope not reproduced (values moved to columns)", "Anytype-Eigenschaftsbereich nicht reproduziert (Werte in Spalten übernommen)"], "Propriété adaptée en texte : {}": ["Property adapted to text: {}", "Eigenschaft als Text angepasst: {}"], "Propriété fichiers adaptée en liens vers les pièces jointes importées": ["File property adapted to links to the imported attachments", "Dateieigenschaft als Links zu den importierten Anhängen angepasst"], "Propriété intégrée à la page non reproduite": ["Property embedded in the page not reproduced", "In die Seite eingebettete Eigenschaft nicht reproduziert"], "Propriété sans schéma de collection : {}": ["Property without a collection schema: {}", "Eigenschaft ohne Sammlungsschema: {}"], "Propriété système intégrée « {} » : valeur calculée par Anytwo sur la page importée": ["Embedded system property “{}”: value computed by Anytwo on the imported page", "Eingebettete Systemeigenschaft „{}“: Wert von Anytwo auf der importierten Seite berechnet"], "Propriété « {} » conservée en texte (format non transposable)": ["Property “{}” kept as text (format cannot be mapped)", "Eigenschaft „{}“ als Text beibehalten (Format nicht übertragbar)"], "Propriété « {} » : même nom mais format différent dans la collection cible": ["Property “{}”: same name but a different format in the target collection", "Eigenschaft „{}“: gleicher Name, aber anderes Format in der Zielsammlung"], "Propriété « {} » sans collection de destination": ["Property “{}” without a destination collection", "Eigenschaft „{}“ ohne Zielsammlung"], "Propriétés de collection non reproduites : {}": ["Collection properties not reproduced: {}", "Sammlungseigenschaften nicht reproduziert: {}"], "Relation : {} cible(s) hors périmètre non importée(s)": ["Relation: {} out-of-scope target(s) not imported", "Relation: {} Ziel(e) außerhalb des Umfangs nicht importiert"], "Rendu intégré « {} » remplacé par son code source": ["Embedded “{}” rendering replaced by its source code", "Eingebettete „{}“-Darstellung durch ihren Quellcode ersetzt"], "Rollup natif configuré ; définition et résultat source conservés dans le bilan": ["Native rollup configured; source definition and result kept in the report", "Nativer Rollup konfiguriert; Quelldefinition und -ergebnis im Bericht beibehalten"], "Rollup non transposable : résultat figé ; définition archivée": ["Rollup cannot be mapped: frozen result; definition archived", "Rollup nicht übertragbar: eingefrorenes Ergebnis; Definition archiviert"], "Référence externe dans la propriété « {} » conservée en texte": ["External reference in property “{}” kept as text", "Externe Referenz in Eigenschaft „{}“ als Text beibehalten"], "Référence de filtre non importée : {}": ["Filter reference not imported: {}", "Filterreferenz nicht importiert: {}"], "Référence vers une collection / un objet non migrable : {}": ["Reference to a collection / non-migratable object: {}", "Referenz auf eine Sammlung / ein nicht migrierbares Objekt: {}"], "Réglages de vues indisponibles : vue de collection sans filtre source": ["View settings unavailable: collection view without a source filter", "Ansichtseinstellungen nicht verfügbar: Sammlungsansicht ohne Quellfilter"], "Réglages visuels et ordre manuel des vues archivés, non appliqués au client Anytwo": ["Visual settings and manual view order archived, not applied to the Anytwo client", "Visuelle Einstellungen und manuelle Ansichtsreihenfolge archiviert, nicht auf den Anytwo-Client angewendet"], "Sommaire non finalisé : {}": ["Table of contents not finalized: {}", "Inhaltsverzeichnis nicht abgeschlossen: {}"], "Sommaire importé en liens de blocs ; mise à jour automatique non conservée": ["Table of contents imported as block links; automatic update not kept", "Inhaltsverzeichnis als Blocklinks importiert; automatische Aktualisierung nicht beibehalten"], "Soulignement non pris en charge par le pont Markdown Anytwo ; texte conservé sans balises": ["Underline not supported by the Anytwo Markdown bridge; text kept without tags", "Unterstreichung vom Anytwo-Markdown-Bridge nicht unterstützt; Text ohne Tags beibehalten"], "Soulignement/exposant/indice non pris en charge par l’import Markdown Anytwo : texte conservé sans balises": ["Underline/superscript/subscript not supported by the Anytwo Markdown import: text kept without tags", "Unterstreichung/Hoch-/Tiefstellung vom Anytwo-Markdown-Import nicht unterstützt: Text ohne Tags beibehalten"], "Table des matières non reproduite": ["Table of contents not reproduced", "Inhaltsverzeichnis nicht reproduziert"], "Template importé comme une page ordinaire": ["Template imported as an ordinary page", "Vorlage als normale Seite importiert"], "Vue en ligne : première vue affichée ; autres vues conservées comme vues enregistrées": ["Inline view: first view displayed; other views kept as saved views", "Inline-Ansicht: erste Ansicht angezeigt; weitere als gespeicherte Ansichten beibehalten"], "Vue groupée adaptée en liste sans regroupement ; filtres et tris conservés": ["Grouped view adapted to a list without grouping; filters and sorts kept", "Gruppierte Ansicht als Liste ohne Gruppierung angepasst; Filter und Sortierungen beibehalten"], "Vue limitée au périmètre importé : {} membre(s) source non importé(s)": ["View limited to the imported scope: {} source member(s) not imported", "Ansicht auf den importierten Umfang begrenzt: {} Quellmitglied(er) nicht importiert"], "Vues / requêtes dynamiques non reproduites": ["Dynamic views / queries not reproduced", "Dynamische Ansichten / Abfragen nicht reproduziert"], "Vues enregistrées rattachées à la page ; emplacement et rendu intégrés à vérifier dans Anytwo": ["Saved views attached to the page; embedded placement and rendering to check in Anytwo", "Gespeicherte Ansichten an die Seite angehängt; eingebettete Platzierung und Darstellung in Anytwo prüfen"], "Widgets Overview non confirmés : {}": ["Overview widgets not confirmed: {}", "Overview-Widgets nicht bestätigt: {}"], "Format d’icône source non transposable automatiquement": ["Source icon format cannot be mapped automatically", "Quellsymbolformat nicht automatisch übertragbar"], "Filtre dynamique dépendant du contexte Anytype": ["Dynamic filter depending on the Anytype context", "Dynamischer Filter abhängig vom Anytype-Kontext"], "Fichier de propriété « {} » : {}": ["Property file “{}”: {}", "Eigenschaftsdatei „{}“: {}"], "! Métadonnées des propriétés indisponibles : {} (conversion prudente)": ["! Property metadata unavailable: {} (cautious conversion)", "! Eigenschaftsmetadaten nicht verfügbar: {} (vorsichtige Konvertierung)"], "! Schéma du type « {} » incomplet : les colonnes sans valeur peuvent manquer.": ["! Incomplete schema for type “{}”: columns without a value may be missing.", "! Unvollständiges Schema für Typ „{}“: Spalten ohne Wert können fehlen."], "! Schéma du type « {} » inaccessible : {}": ["! Schema of type “{}” inaccessible: {}", "! Schema des Typs „{}“ nicht erreichbar: {}"], "! Widgets Anytype non lus : {}": ["! Anytype widgets not read: {}", "! Anytype-Widgets nicht gelesen: {}"], "! Certains contenus de l’espace source n’ont pas pu être lus.": ["! Some source space content could not be read.", "! Einige Inhalte des Quellbereichs konnten nicht gelesen werden."], "Lecture des objets, des types et des collections de cet espace…": ["Reading objects, types and collections in this space…", "Objekte, Typen und Sammlungen dieses Bereichs werden gelesen …"], "Collection « {} » :": ["Collection “{}”:", "Collection „{}“:"], "COLLECTION : {} — {} éléments.": ["Collection: {} — {} item(s).", "Sammlung: {} — {} Element(e)."], "SÉLECTION : {} objets distincts (déduplication entre types).": ["Selection: {} distinct objects (deduplicated across types).", "Auswahl: {} eindeutige Objekte (über Typen dedupliziert)."], "OBJETS : {} élément(s) sélectionné(s) individuellement.": ["Objects: {} item(s) selected individually.", "Objekte: {} Element(e) einzeln ausgewählt."], "→ Création simulée de la collection « {} » pour le type « {} ».": ["→ Simulated creation of collection “{}” for type “{}”.", "→ Simulierte Erstellung der Sammlung „{}“ für Typ „{}“."], "→ Utilisation de la collection « {} » pour le type « {} ».": ["→ Using collection “{}” for type “{}”.", "→ Verwendung der Sammlung „{}“ für Typ „{}“."], "→ Utilisation de l’espace Anytwo « {} ».": ["→ Using Anytwo space “{}”.", "→ Verwendung des Anytwo-Bereichs „{}“."], "→ Création simulée de l’espace Anytwo « {} ».": ["→ Simulated creation of Anytwo space “{}”.", "→ Simulierte Erstellung des Anytwo-Bereichs „{}“."], "→ Création simulée de la collection « {} » (collection ou type structuré).": ["→ Simulated creation of collection “{}” (collection or structured type).", "→ Simulierte Erstellung der Sammlung „{}“ (Sammlung oder strukturierter Typ)."], "→ Création simulée de la collection « {} ».": ["→ Simulated creation of collection “{}”.", "→ Simulierte Erstellung der Sammlung „{}“."], "→ Utilisation de la collection « {} ».": ["→ Using collection “{}”.", "→ Verwendung der Sammlung „{}“."], "→ Les types sans propriétés confirmées peuvent rester hors collection ; en cas de doute, une collection est prévue pour préserver les propriétés.": ["→ Types without confirmed properties may stay outside collections; when in doubt, a collection is planned to preserve properties.", "→ Typen ohne bestätigte Eigenschaften können außerhalb von Sammlungen bleiben; im Zweifel ist eine Sammlung zum Erhalt der Eigenschaften vorgesehen."], "FICHIERS : transfert prévu, pièces jointes non inspectées dans ce prototype.": ["FILES: transfer planned, attachments not inspected in this prototype.", "DATEIEN: Übertragung geplant, Anhänge in diesem Prototyp nicht geprüft."], "OBJET : {} — serait importé.": ["OBJECT: {} — would be imported.", "OBJEKT: {} — würde importiert."], "! Documents de vue intégrée non résolus : {}": ["! Inline view documents not resolved: {}", "! Inline-Ansichtsdokumente nicht aufgelöst: {}"], "↳ Document de vue intégrée « {} » : objet ajouté au périmètre.": ["↳ Inline view document “{}”: object added to the scope.", "↳ Inline-Ansichtsdokument „{}“: Objekt zum Umfang hinzugefügt."], "↳ Lien vers « {} » : objet ajouté au périmètre.": ["↳ Link to “{}”: object added to the scope.", "↳ Link zu „{}“: Objekt zum Umfang hinzugefügt."], "↳ Lien vers « {} » : non suivi (option désactivée).": ["↳ Link to “{}”: not followed (option disabled).", "↳ Link zu „{}“: nicht verfolgt (Option deaktiviert)."], "! Impossible d’inspecter les liens : {}": ["! Cannot inspect links: {}", "! Links können nicht geprüft werden: {}"], "! Limite de sécurité de 5 000 objets atteinte : analyse arrêtée.": ["! Safety limit of 5,000 objects reached: analysis stopped.", "! Sicherheitsgrenze von 5.000 Objekten erreicht: Analyse gestoppt."], "BILAN : {} objet(s) prévu(s), {} ajouté(s) par les liens, {} erreur(s) de lecture.": ["REPORT: {} object(s) planned, {} added through links, {} read error(s).", "BERICHT: {} Objekt(e) geplant, {} über Links hinzugefügt, {} Lesefehler."], "ARCHIVE CHAT : {} — {} message(s), une page prévue.": ["CHAT ARCHIVE: {} — {} message(s), one page planned.", "CHAT-ARCHIV: {} — {} Nachricht(en), eine Seite geplant."], "CHATS : {} archive(s) supplémentaire(s), tous les chats de l’espace source.": ["CHATS: {} additional archive(s), every chat in the source space.", "CHATS: {} zusätzliche(s) Archiv(e), alle Chats des Quellbereichs."], "CHATS : exclus (option archives désactivée).": ["CHATS: excluded (archives option disabled).", "CHATS: ausgeschlossen (Archivoption deaktiviert)."], "TERMINÉ : simulation uniquement. Aucun objet n’a été créé, modifié ou téléchargé.": ["DONE: simulation only. No object was created, modified or downloaded.", "FERTIG: nur Simulation. Kein Objekt wurde erstellt, geändert oder heruntergeladen."], "ESPACE : {} — {} objets, {} collections et {} types.": ["SPACE: {} — {} objects, {} collections and {} types.", "BEREICH: {} — {} Objekte, {} Sammlungen und {} Typen."], "TYPE : {} — {} objets ; destination : sans collection.": ["TYPE: {} — {} objects; destination: no collection.", "TYP: {} — {} Objekte; Ziel: ohne Sammlung."], "TYPE : {} — {} objets ; destination : collection existante « {} ».": ["TYPE: {} — {} objects; destination: existing collection “{}”.", "TYP: {} — {} Objekte; Ziel: vorhandene Sammlung „{}“."], "TYPE : {} — {} objets ; destination : nouvelle collection « {} ».": ["TYPE: {} — {} objects; destination: new collection “{}”.", "TYP: {} — {} Objekte; Ziel: neue Sammlung „{}“."], "Sélectionnez un espace, une collection, un ou plusieurs types ou objets.": ["Select a space, a collection, one or more types or objects.", "Wählen Sie einen Bereich, eine Sammlung, einen oder mehrere Typen oder Objekte."], "Définissez un espace de destination.": ["Define a destination space.", "Legen Sie einen Zielbereich fest."], "Types sélectionnés introuvables : rechargez l’espace.": ["Selected types not found: reload the space.", "Ausgewählte Typen nicht gefunden: Bereich neu laden."], "Correspondance manquante pour le type « {} ».": ["Missing mapping for type “{}”.", "Fehlende Zuordnung für Typ „{}“."], "Destination incorrecte pour le type « {} ».": ["Incorrect destination for type “{}”.", "Ungültiges Ziel für Typ „{}“."], "Le type « {} » doit être importé dans une collection pour conserver ses propriétés.": ["Type “{}” must be imported into a collection to keep its properties.", "Typ „{}“ muss zum Erhalt seiner Eigenschaften in eine Sammlung importiert werden."], "Donnez un nom à la collection du type « {} ».": ["Name the collection for type “{}”.", "Benennen Sie die Sammlung für Typ „{}“."], "Nom de collection manquant pour le type « {} ».": ["Missing collection name for type “{}”.", "Fehlender Sammlungsname für Typ „{}“."], "Collection de destination obligatoire pour le type « {} » (propriétés à préserver).": ["A destination collection is required for type “{}” (properties to preserve).", "Für Typ „{}“ ist eine Zielsammlung erforderlich (beizubehaltende Eigenschaften)."], "La sélection a changé : rechargez la liste des objets.": ["The selection changed: reload the object list.", "Die Auswahl hat sich geändert: Objektliste neu laden."], "Collection source inconnue (rechargez l’espace).": ["Unknown source collection (reload the space).", "Unbekannte Quellsammlung (Bereich neu laden)."], "Sélection source manquante.": ["Missing source selection.", "Fehlende Quellauswahl."], "ID de l’espace cible manquant.": ["Missing target space ID.", "Fehlende Zielbereichs-ID."], "Limite de sécurité : plus de {} objets dans le périmètre. Aucune écriture effectuée.": ["Safety limit: more than {} objects in scope. No write performed.", "Sicherheitsgrenze: mehr als {} Objekte im Umfang. Keine Schreibvorgänge."], "Réponse objet non JSON.": ["Object response is not JSON.", "Objektantwort ist kein JSON."], "Objet de vues créé sans identifiant": ["View object created without an identifier", "Ansichtsobjekt ohne Kennung erstellt"], "Aucun document source lisible. Aucune écriture effectuée.": ["No readable source document. No write performed.", "Kein lesbares Quelldokument. Keine Schreibvorgänge."], "Un autre import est déjà en cours.": ["Another import is already running.", "Ein weiterer Import läuft bereits."], "Recharger l’inventaire Anytype avant l’import.": ["Reload the Anytype inventory before importing.", "Laden Sie das Anytype-Inventar vor dem Import neu."], "Import Notion non encore activé ; utilisez son analyse sans écriture.": ["Notion import is not enabled yet; use its read-only analysis.", "Notion-Import noch nicht aktiviert; nutzen Sie die Analyse ohne Schreiben."]};
  const templateRules=Object.entries(templates).map(([fr,pair])=>({
    rx:new RegExp('^'+fr.split('{}').map(part=>part.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('([\\s\\S]*?)')+'$'),
    en:pair[0],de:pair[1]}));
  function template(source,into){
    for(const rule of templateRules){
      const found=source.match(rule.rx);
      if(!found)continue;
      let index=0;
      return (into==='en'?rule.en:rule.de).replace(/\{\}/g,()=>found[++index]??'');
    }
    return null;
  }
  function translate(source, into=lang){
    if(into==='fr'||typeof source!=='string')return source;
    if(Object.prototype.hasOwnProperty.call(messages,source))return messages[source][into==='en'?0:1];
    // Markup often carries a non-breaking space; dictionaries use a plain one.
    if(source.includes('\u00a0')){
      const flat=source.replace(/\u00a0/g,' ');
      if(Object.prototype.hasOwnProperty.call(messages,flat))return messages[flat][into==='en'?0:1];
    }
    const fromTemplate=template(source,into);
    if(fromTemplate!==null)return fromTemplate;
    for(const [rx,formatter] of params){const found=source.match(rx);if(found)return formatter(...found.slice(1),into);}
    return source;
  }
  function ignored(el){
    // Source data (object names, server diagnostics) must never be rewritten.
    return !!el.closest('#source-space, #selected-name, #custom-space, #custom-collection, .item-name, .source-text, .type-map-head strong, .item-count, .log-arrow');
  }
  function transformText(node){
    const parent=node.parentElement;if(!parent || ignored(parent)||['SCRIPT','STYLE','TEXTAREA'].includes(parent.tagName))return;
    const current=node.nodeValue; if(!current||!current.trim())return;
    const old=originals.get(node);
    const source=old&&(current===old.last || current===old.source)?old.source:current;
    const m=source.match(/^(\s*)([\s\S]*?)(\s*)$/),translated=translate(m[2]);
    const result=m[1]+translated+m[3];originals.set(node,{source,last:result});
    if(result!==current)node.nodeValue=result;
  }
  function ignoredAttr(el){
    // Labels stay translatable on containers whose text is source data.
    return !!el.closest('.source-text');
  }
  function transformAttr(el,attribute){
    if(ignoredAttr(el))return;
    const current=el.getAttribute(attribute);if(!current)return;
    let map=attrs.get(el);if(!map){map={};attrs.set(el,map);}
    const old=map[attribute],source=old && (current===old.last||current===old.source)?old.source:current;
    const target=translate(source);map[attribute]={source,last:target};
    if(target!==current)el.setAttribute(attribute,target);
  }
  function process(root){
    if(!root)return;
    if(root.nodeType===3){transformText(root);return;}
    if(root.nodeType!==1 && root.nodeType!==9)return;
    if(root.nodeType===1){for(const attr of ['title','placeholder','aria-label'])if(root.hasAttribute(attr))transformAttr(root,attr);}
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_ELEMENT|NodeFilter.SHOW_TEXT);
    while(walker.nextNode()){
      const child=walker.currentNode;
      if(child.nodeType===3)transformText(child);
      else if(child.nodeType===1)for(const attr of ['title','placeholder','aria-label'])if(child.hasAttribute(attr))transformAttr(child,attr);
    }
  }
  function setLanguage(next){
    if(!['fr','en','de'].includes(next))return;
    lang=next;try{localStorage.setItem(STORAGE_KEY,next);}catch(e){}
    document.documentElement.lang=next;
    for(const box of document.querySelectorAll('[data-language-choice]'))box.value=next;
    process(document);
    document.dispatchEvent(new CustomEvent('any2any:language',{detail:{language:next}}));
  }
  function init(){
    for(const box of document.querySelectorAll('[data-language-choice]')){
      box.value=lang;box.addEventListener('change',()=>setLanguage(box.value));
    }
    setLanguage(lang);
    const observer=new MutationObserver(records=>{
      for(const r of records){
        if(r.type==='characterData')transformText(r.target);
        else if(r.type==='attributes')transformAttr(r.target,r.attributeName);
        else for(const n of r.addedNodes)process(n);
      }
    });
    observer.observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['title','placeholder','aria-label']});
  }
  global.Any2AnyI18n={t:translate,setLanguage,getLanguage:()=>lang,init,messages};
  if(typeof document!=='undefined'){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();}
})(typeof window!=='undefined'?window:globalThis);
