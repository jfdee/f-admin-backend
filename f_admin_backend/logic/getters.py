from convert_case import kebab_case, pascal_case
from starlette import status
from starlette.exceptions import HTTPException
from tortoise import Tortoise


def get_model(code: str, raise_exception: bool = True):
    model = Tortoise.apps['models'].get(pascal_case(code))
    if not model and raise_exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return model


async def get_model_instance(code: str, pk: int, raise_exception: bool = True):
    model = get_model(code=code, raise_exception=raise_exception)
    instance = await model.filter(pk=pk).first()
    if not instance and raise_exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return instance


__all__ = (
    'get_model',
    'get_model_instance',
)
