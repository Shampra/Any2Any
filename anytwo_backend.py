"""Shared Anytwo destination API for source adapters.

Keep a single implementation in api_clients during the incremental extraction.
These re-exports intentionally preserve the existing public API and tests. Both
source adapters must use this boundary rather than copy target write logic.
Source-specific discovery/conversion remains outside this module.
"""
from api_clients import (
    APIError, Anytwo, target_write, create_space, create_collection,
    create_object, add_membership, list_columns, add_column, set_column_value,
    set_markdown, append_markdown, attach_file, get_file_info, create_editor_block,
    local_get, local_binary, unwrap_list, _segment,
)

__all__=[
    'APIError','Anytwo','target_write','create_space','create_collection',
    'create_object','add_membership','list_columns','add_column','set_column_value',
    'set_markdown','append_markdown','attach_file','get_file_info','create_editor_block',
    'local_get','local_binary','unwrap_list','_segment','set_space_icon',
]


def set_space_icon(api,sid,name,content,mime):
    """Use the same index-object file URI as the native space icon picker."""
    space=local_get(api.port,f'/v1/spaces/{_segment(sid)}')
    oid=space.get('spaceIndexObjectId')
    if not oid:raise APIError('Objet index de l’espace indisponible pour son icône.')
    fid=attach_file(api,sid,oid,name,content,mime)
    target_write(api,f'/spaces/{_segment(sid)}',{'iconCid':f'any://f/{sid}/{fid}'},method='PATCH')
    return fid
