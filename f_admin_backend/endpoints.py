import os
from datetime import datetime

from convert_case import kebab_case, pascal_case
from starlette import status
from starlette.exceptions import HTTPException
from tortoise import Tortoise

from .consts import DATE_FORMAT, DATETIME_FORMAT

ADMIN_EXCLUDE_MODELS: list = os.environ.get('F_ADMIN_EXCLUDE_MODELS', [])


def _get_model(code: str):
    model = Tortoise.apps['models'].get(pascal_case(code))
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return model


async def _get_model_instance(code: str, pk: int):
    model = _get_model(code)
    instance = await model.filter(pk=pk).first()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return instance


def get_menu_items():
    data: list[dict] = []
    for name, meta in Tortoise.apps.get('models').items():
        if name in ADMIN_EXCLUDE_MODELS:
            continue
        data.append({
            'code': kebab_case(string=name),
            'label': getattr(meta.Meta, 'verbose_name_plural', name),
            'fields': [],
        })
    return data


async def get_paginator(model):
    return {'count': await model.all().count()}


async def to_representation(fields: list, queryset) -> list:
    """object -> json"""
    items = []
    for obj in queryset:
        item = {}
        for field in fields:
            f_type = field['type']
            if f_type == 'related':
                value = await getattr(obj, field['name'])
                value = str(value) if value else None
            else:
                value = getattr(obj, field['name'])
            if value and f_type == 'datetime':
                value = value.strftime(DATETIME_FORMAT)
            if value and f_type == 'date':
                value = value.strftime(DATE_FORMAT)
            item[field['name']] = value
        items.append(item)
    return items


async def to_internal_value(model, data: dict):
    """json -> object"""
    _data = {}
    for key, value in data.items():
        # TODO(разобраться с наличием value и default полей)
        f_meta = model._meta.fields_map[key]
        f_type = f_meta.field_type.__name__
        if f_type == 'datetime' and value:
            value = datetime.strptime(value, DATETIME_FORMAT)
        if f_type == 'date' and value:
            value = datetime.strptime(value, DATE_FORMAT).date()
        if f_type == 'bool' and value is None:
            value = f_meta.default
        if f_type == 'int':
            value = f_meta.default if not value else int(value)
        if getattr(f_meta, 'related_model', None):
            key = f'{key}_id'
        _data[key] = value
    return _data


async def get_list_meta_fields(model):
    fields = []
    for f_name, f_meta in model._meta.fields_map.items():
        if not f_meta.field_type:
            # backward relation
            continue
        field_meta = {
            'name': f_name,
            'label': f_meta.description or f_name,
            'type': f_meta.field_type.__name__,
        }
        if f_meta.allows_generated and f_meta.source_field:
            # fk field_id
            field_meta['type'] = 'related_id'
        if getattr(f_meta, 'related_model', None):
            field_meta['type'] = 'related'
        fields.append(field_meta)
    return fields


async def menu_item_list(code: str, page: int, search: str = None):
    model = _get_model(code)
    limit = 10
    offset = (page - 1) * limit
    queryset = await model.all().order_by('-created_at').limit(limit).offset(offset)
    fields_meta = await get_list_meta_fields(model)
    items = await to_representation(fields=fields_meta, queryset=queryset)
    paginator = await get_paginator(model)
    return {'data': items, 'meta': {'fields': fields_meta, 'paginator': paginator}}


async def get_object_meta_fields(model):
    fields = []
    for f_name, f_meta in model._meta.fields_map.items():
        if not f_meta.field_type:
            # backward relation
            continue
        if f_meta.allows_generated and f_meta.source_field:
            # fk field_id
            continue
        read_only = any([
            f_meta.generated,
            getattr(f_meta, 'auto_now_add', False),
            getattr(f_meta, 'auto_now', False),
        ])
        if read_only:
            continue
        field_meta = {
            'name': f_name,
            'label': f_meta.description or f_name,
            'required': f_meta.required,
            'allow_null': f_meta.null,
            'type': f_meta.field_type.__name__,
        }
        if getattr(f_meta, 'related_model', None):
            related_queryset = await f_meta.related_model.all()
            field_meta['type'] = 'related'
            field_meta['choices'] = [(x.id, str(x)) for x in related_queryset]
        fields.append(field_meta)
    return fields


async def menu_item_meta(code: str):
    model = _get_model(code)
    fields = await get_object_meta_fields(model)
    return {'fields': fields}


async def menu_item_post(code: str, data: dict):
    model = _get_model(code)
    data = await to_internal_value(model=model, data=data)
    instance = await model.create(**data)
    return {'pk': instance.pk}


async def menu_item_instance_retrieve(code: str, pk: int):
    instance = await _get_model_instance(code, pk)
    return dict(instance)


async def menu_item_instance_put(code: str, pk: int, data: dict):
    model = _get_model(code)
    data = await to_internal_value(model=model, data=data)
    instance = await _get_model_instance(code, pk)
    for key, value in data.items():
        setattr(instance, key, value)
    await instance.save()
    return dict(instance)


async def menu_item_instance_delete(code: str, pk: int):
    instance = await _get_model_instance(code, pk)
    await instance.delete()


__all__ = (
    'get_menu_items',
    'menu_item_list',
    'menu_item_meta',
    'menu_item_post',
    'menu_item_instance_retrieve',
    'menu_item_instance_put',
    'menu_item_instance_delete',
)
