"""Explicit conversion policy, separate from either source reader or writer."""
BLOCKS={
    **{kind:('native','Blocs de texte/listes Anytwo, via conversion des annotations et liens.') for kind in
       ('paragraph','heading_1','heading_2','heading_3','bulleted_list_item','numbered_list_item','to_do','quote','code','divider')},
    'toggle':('native','Toggle natif avec enfants ; adapter aussi les titres repliables.'),
    'column_list':('adaptation','Colonnes natives ; convertir la hiérarchie et les proportions exposées.'),
    'column':('adaptation','Colonne du groupe parent, sans duplication de contenu.'),
    'table':('adaptation','Tableau de blocs, distinct d’une base ; conversion de ses cellules.'),
    'table_row':('adaptation','Cellules en texte enrichi à convertir dans leur tableau.'),
    'callout':('native','Callout natif avec cadre, icône et enfants ; couleurs de texte/fond non reproduites.'),
    **{kind:('adaptation','Télécharger le fichier et le joindre dans Anytwo ; ne pas conserver une URL temporaire comme pièce jointe définitive.') for kind in ('image','file','pdf','audio','video')},
    'embed':('adaptation','Embed natif si fournisseur reconnu, sinon lien avec signalement.'),
    'bookmark':('adaptation','Conserver le lien ; aperçu enrichi à vérifier.'),
    'link_preview':('adaptation','Conserver le lien ; aperçu externe non garanti.'),
    'child_page':('adaptation','Lien vers la page enfant importée ; préserver la navigation.'),
    'child_database':('adaptation','Créer la collection, son supertag et ses propriétés, puis insérer une vue inline à cet emplacement de la page ; plusieurs sources distinctes donnent plusieurs collections.'),
    'link_to_page':('adaptation','Lien remappé si la cible est importée, sinon référence explicitement signalée.'),
    'synced_block':('adaptation','Originaux et références deviennent des blocs synchronisés Anytwo. La synchronisation est interne à Anytwo, sans lien vivant avec Notion ; original hors sélection matérialisé dans la première occurrence importée.'),
    'equation':('adaptation','Expression mathématique conservée ; rendu cible à vérifier.'),
    'table_of_contents':('adaptation','Sommaire statique avec liens vers les identifiants réels des blocs de titre ; pas de mise à jour automatique.'),
    'unsupported':('unavailable','L’API ne fournit pas le contenu de ce bloc : perte à signaler, pas à inventer.'),
}
PROPERTIES={
    'title':('native','Titre natif de page.'),
    'rich_text':('adaptation','Texte/Markdown ; annotations compatibles et liens à convertir.'),
    'number':('native','Valeur numérique conservée ; format monétaire, devise, pourcentage et séparateurs repris.'),
    'checkbox':('native','Case à cocher, état préservé.'),
    'date':('adaptation','Date ou date/heure ; intervalle, fuseau et rappels à examiner séparément.'),
    'select':('native','Choix simple, options et couleurs traduites vers la palette cible.'),
    'multi_select':('native','Choix multiples avec vocabulaire et couleurs.'),
    'status':('adaptation','Choix simple ; groupes du workflow Notion conservés dans les métadonnées.'),
    **{kind:('native','Texte typé correspondant.') for kind in ('url','email','phone_number')},
    'relation':('adaptation','Relation native Anytwo (liens any://), limitée au handle du supertag cible. Schéma cible lu sans importer ses pages si elles sont hors sélection ; cible inaccessible/ambiguë conservée en texte avec avertissement.'),
    'files':('adaptation','Fichiers locaux cibles ; téléchargement sans transmettre le jeton Notion à leur hébergeur.'),
    'formula':('snapshot','Résultat figé et expression archivée ; formule non recréée comme calcul actif.'),
    'rollup':('adaptation','Rollup natif configurable via xFormat.anyui.rollup : remapper la relation et la propriété cible, puis vérifier l’agrégation. Somme et valeurs originales observées dans le client ; autres calculs à vérifier, avec archivage du résultat si incompatibles.'),
    'people':('snapshot','Noms/identifiants lisibles ; ne pas recréer de comptes ou droits Anytwo.'),
    'created_by':('snapshot','Auteur source décrit dans une propriété ; auteur natif cible distinct.'),
    'last_edited_by':('snapshot','Dernier éditeur source conservé sans usurper son identité.'),
    'created_time':('native','Date source dans une propriété distincte de la date d’import.'),
    'last_edited_time':('native','Date de modification source conservée séparément.'),
    'unique_id':('snapshot','Identifiant préfixé conservé ; pas de séquence automatique supposée.'),
    'button':('unavailable','Action Notion non rejouée dans Anytwo.'),
}

VIEWS={
    **{kind:('adaptation','Vue inline de la collection ; remapper filtres, tris, ordre et visibilité des propriétés. Toute condition non traduisible doit être signalée sans élargir silencieusement les résultats.') for kind in ('table','list','board','gallery')},
    **{kind:('unavailable','Rendu de vue non reproduit ; conserver les données dans la collection et archiver les réglages source.') for kind in ('chart','map','timeline','form','dashboard')},
    'calendar':('review','Rendu calendrier à vérifier dans Anytwo ; conserver les dates et les paramètres source.'),
}

def assess(blocks,properties,views=None):
    result=[]
    for category,counts,policy in (('bloc',blocks,BLOCKS),('propriété',properties,PROPERTIES)):
        for kind,count in sorted(counts.items()):
            status,note=policy.get(kind,('review','Type inconnu : conserver sa définition et vérifier avant conversion.'))
            result.append({'category':category,'type':kind,'count':count,'conversion':status,'note':note})
    from collections import Counter
    for kind,count in sorted(Counter(x.get('type','unknown') for x in (views or [])).items()):
        status,note=VIEWS.get(kind,('review','Disposition inconnue : conserver sa définition pour examen.'))
        result.append({'category':'vue','type':kind,'count':count,'conversion':status,'note':note})
    return {'stage':'planned','items':result,'notes':[
        'Cette classification décrit la conversion prévue, pas un import déjà validé.',
        'Le soulignement et les couleurs de texte/fond Notion ne sont pas garantis par le pont Markdown Anytwo actuel.',
        'Les vues compatibles seront remappées avec filtres/tris/visibilité ; une condition non traduisible fera refuser la vue entière.',
        'Permissions, commentaires, historique, modèles actifs et automatisations ne sont pas recréés.',
    ]}
