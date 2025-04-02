from convert_case import kebab_case, pascal_case
from tortoise import Tortoise

from .consts import PAGE_SIZE
from .logic.actions import to_internal_value, to_representation
from .logic.getters import get_model, get_model_instance
from .settings import settings


def get_menu_items() -> list:
    items: list[dict] = []
    for name, meta in Tortoise.apps.get('models').items():
        if name in settings.ADMIN_EXCLUDE_MODELS:
            continue
        items.append({
            'code': kebab_case(string=name),
            'label': getattr(meta.Meta, 'verbose_name_plural', name),
            'fields': [],
        })
    return items


async def get_paginator(model) -> dict:
    return {'count': await model.all().count()}


async def get_list_meta_fields(model) -> list:
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
            # ForeignKey pk "{field}_id"
            field_meta['type'] = 'related_id'
        if getattr(f_meta, 'related_model', None):
            # ForeignKey
            field_meta['type'] = 'related'
        fields.append(field_meta)
    return fields


async def menu_item_list(code: str, page: int, search: str = None) -> dict:
    model = get_model(code=code)
    offset = (page - 1) * PAGE_SIZE
    queryset = await model.all().order_by('-id').limit(PAGE_SIZE).offset(offset)
    fields_meta = await get_list_meta_fields(model=model)
    items = await to_representation(fields=fields_meta, queryset=queryset)
    paginator = await get_paginator(model)
    return {
        'data': items,
        'meta': {
            'fields': fields_meta,
            'paginator': paginator,
        },
    }


async def get_object_meta_fields(model) -> list:
    """Meta for POST/PUT"""
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


async def menu_item_meta(code: str) -> dict:
    model = get_model(code=code)
    fields = await get_object_meta_fields(model=model)
    return {'fields': fields}


async def menu_item_post(code: str, data: dict) -> dict:
    model = get_model(code=code)
    data = await to_internal_value(model=model, data=data)
    instance = await model.create(**data)
    return {'pk': instance.pk}


async def menu_item_instance_retrieve(code: str, pk: int) -> dict:
    instance = await get_model_instance(code=code, pk=pk)
    return dict(instance)


async def menu_item_instance_put(code: str, pk: int, data: dict) -> dict:
    model = get_model(code=code)
    data = await to_internal_value(model=model, data=data)
    instance = await get_model_instance(code=code, pk=pk)
    for key, value in data.items():
        setattr(instance, key, value)
    await instance.save()
    return dict(instance)


async def menu_item_instance_delete(code: str, pk: int) -> None:
    instance = await get_model_instance(code=code, pk=pk)
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
