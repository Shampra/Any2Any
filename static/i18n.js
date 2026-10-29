'use strict';
/* UI-only translations. Source data (names, property values, content) is never translated.
   French strings are source keys to preserve compatibility with the existing UI. */
(function(global){
  const STORAGE_KEY='any2any.language';
  const LEGACY_STORAGE_KEY='type2two.language';
  const messages={
    'Any2Any · Importer':['Any2Any · Import','Any2Any · Importieren'],
    'Any2Any · Autorisation Anytype':['Any2Any · Anytype authorization','Any2Any · Anytype-Autorisierung'],
    'Anytype → Anytwo · Outil de migration · Bêta 0.9.1':['Anytype → Anytwo · Migration tool · Beta 0.9.1','Anytype → Anytwo · Migrationstool · Beta 0.9.1'],
    'Autorisation Anytype · Importateur':['Anytype authorization · Importer','Anytype-Autorisierung · Importer'],
    'Outil de migration · Bêta 0.9.1':['Migration tool · Experimental beta 0.9.1','Migrationstool · Experimentelle Beta 0.9.1'],
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
    'Couleur de background':['Block background colors','Blockhintergrundfarben'],
    'Types':['Types','Typen'],
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
    [/^(.*) · (\d+) occurrence\(s\)$/,(a,b,l)=>l==='en'?`${a} · ${b} occurrence(s)`:`${a} · ${b} Vorkommen`],
  ];
  function detect(){let explicit='';try{explicit=localStorage.getItem(STORAGE_KEY)||'';}catch(e){}
    if(!explicit){try{explicit=localStorage.getItem(LEGACY_STORAGE_KEY)||'';}catch(e){}}
    if(['fr','en','de'].includes(explicit))return explicit;
    const raw=(navigator.language||'fr').slice(0,2).toLowerCase();return ['fr','en','de'].includes(raw)?raw:'fr';
  }
  let lang=detect();const originals=new WeakMap();const attrs=new WeakMap();
  function translate(source, into=lang){
    if(into==='fr'||typeof source!=='string')return source;
    if(Object.prototype.hasOwnProperty.call(messages,source))return messages[source][into==='en'?0:1];
    for(const [rx,formatter] of params){const found=source.match(rx);if(found)return formatter(...found.slice(1),into);}
    return source;
  }
  function ignored(el){
    return !!el.closest('#source-space, #selected-name, #custom-space, #custom-collection, .item-name, .report-item summary, .report-issue, .report-error, .log-lines, .type-map-head strong, .item-count');
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
  function transformAttr(el,attribute){
    if(ignored(el))return;
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
