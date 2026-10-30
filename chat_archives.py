"""Read-only chat history export and page archive rendering."""
from urllib.parse import quote
from datetime import datetime
from api_clients import APIError, paginated, item_id, item_name
from rich_content import image_markdown, file_html, remove_unsupported_inline


def histories(source, sid):
    rows=paginated(source.port,f'/v2/spaces/{quote(sid,safe="")}/chats',source.key)
    result=[];seen_chats=set()
    for row in rows:
        cid=item_id(row)
        if not cid or cid in seen_chats:continue
        seen_chats.add(cid);pages=[];seen_cursors=set();seen={};cursor=None;expected=None;warnings=[]
        for _ in range(500):
            path=f'/spaces/{quote(sid,safe="")}/chats/{quote(cid,safe="")}/messages?limit=200'
            if cursor is not None:path+='&before='+quote(cursor,safe='')
            payload=source.request(path)
            if not isinstance(payload,dict) or not isinstance(payload.get('messages'),list):
                raise APIError('Historique de chat non reconnu : '+item_name(row))
            if expected is None:expected=payload.get('message_count')
            warnings.extend(str(v) for v in payload.get('warnings',[]))
            batch=[]
            for message in payload['messages']:
                if not isinstance(message,dict) or not message.get('id'):
                    raise APIError('Message de chat sans identifiant : '+item_name(row))
                mid=message['id']
                if mid in seen:
                    if seen[mid]!=message:raise APIError('Historique modifié pendant la lecture : '+item_name(row))
                    continue
                seen[mid]=message;batch.append(message)
            pages.append(batch)
            if not payload.get('has_more',bool(payload.get('next_before'))):break
            cursor=payload.get('next_before')
            if not isinstance(cursor,str) or not cursor or cursor in seen_cursors:
                raise APIError('Pagination du chat incomplète : '+item_name(row))
            seen_cursors.add(cursor)
        else:raise APIError('Historique trop volumineux : '+item_name(row))
        messages=[m for batch in reversed(pages) for m in batch]
        if isinstance(expected,int) and expected!=len(messages):
            raise APIError('Nombre de messages incohérent : '+item_name(row)+' ; relancez la lecture.')
        result.append({'id':cid,'name':item_name(row),'messages':messages,'warnings':warnings})
    return result


def stamp(value):
    try:return datetime.fromisoformat(str(value).replace('Z','+00:00')).strftime('%d/%m/%Y %H:%M:%S %z')
    except ValueError:return str(value or 'Date inconnue')


def label(value):
    return str(value).replace('\\','\\\\').replace('*','\\*').replace('[','\\[').replace(']','\\]').replace('\n',' ')


def markdown(history, files, load_file, issues, rewrite=lambda text:text, object_link=lambda oid:None):
    messages=history['messages'];byid={m['id']:m for m in messages}
    lines=['Archive du chat **'+label(history['name'])+'** — '+str(len(messages))+' message(s).',
           'Les auteurs et dates ci-dessous proviennent d’Anytype. Cette page est une archive, pas une conversation active.']
    day=None
    for message in messages:
        current=str(message.get('at') or '')[:10]
        if current!=day:
            lines.append('## '+(current or 'Date inconnue'));day=current
        head='**'+label(message.get('author') or message.get('author_id') or 'Auteur inconnu')+'** · '+stamp(message.get('at'))
        if message.get('edited_at'):head+=' · modifié le '+stamp(message['edited_at'])
        body=[head]
        reply=message.get('reply_to') or message.get('reply_to_message_id')
        if reply:
            if isinstance(reply,dict):reply=reply.get('id')
            original=byid.get(reply)
            body.append('↪ En réponse à '+(label(original.get('author') or 'Auteur inconnu')+' : '+label(original.get('text','')[:160]) if original else 'un message absent de cet historique ('+label(reply)+')'))
        text=str(message.get('text') or '')
        cleaned=remove_unsupported_inline(text)
        if cleaned!=text:issues.add('Mise en forme de chat non prise en charge : texte conservé sans balises')
        if cleaned:body.append(rewrite(cleaned))
        for attachment in message.get('attachments') or []:
            fid=attachment.get('id');kind=attachment.get('type');name=attachment.get('name') or 'Pièce jointe'
            if not fid:
                issues.add('Pièce jointe de chat sans identifiant');body.append('Pièce jointe indisponible.');continue
            if kind=='link':
                link=object_link(fid)
                if link:body.append(link)
                else:
                    issues.add('Objet lié à un chat non importé')
                    body.append('Objet lié non importé : '+label(name)+' ('+label(fid)+')')
                continue
            if not files:
                issues.add('Pièces jointes de chat non importées (option fichiers désactivée)');body.append('Pièce jointe non importée : '+label(name));continue
            try:
                uri=load_file(fid,name,None);name=getattr(uri,'name',name)
                body.append(image_markdown(uri,name) if kind=='image' else file_html(uri,name))
            except (APIError,ValueError) as exc:
                issues.add('Pièce jointe de chat indisponible : '+str(exc));body.append('Pièce jointe indisponible : '+label(name))
        if message.get('reactions'):
            body.append('Réactions : '+ ' · '.join(label(k)+' '+str(v if isinstance(v,int) else len(v)) for k,v in message['reactions'].items()))
        quoted='\n>\n'.join('\n'.join('> '+line for line in part.split('\n')) for part in body)
        lines.extend([quoted,'---'])
    if not messages:lines.append('Ce chat ne contient aucun message.')
    return '\n\n'.join(lines)
