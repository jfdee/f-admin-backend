from datetime import datetime

from f_admin_backend.consts import DATE_FORMAT, DATETIME_FORMAT


async def to_representation(fields: list, queryset) -> list:
    """pyobject -> json"""
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


async def to_internal_value(model, data: dict) -> dict:
    """json -> pyobject"""
    object_data = {}
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
        object_data[key] = value
    return object_data


__all__ = (
    'to_representation'
    'to_internal_value'
)
