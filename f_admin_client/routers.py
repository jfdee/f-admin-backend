from fastapi import APIRouter
from starlette import status

from . import endpoints

menu_item_instance_router = APIRouter(prefix='/{pk}', tags=['menu-item-instance'])
menu_item_instance_router.add_api_route(
    methods=['GET'],
    path='/',
    endpoint=endpoints.menu_item_instance_retrieve,
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
menu_item_instance_router.add_api_route(
    methods=['PUT'],
    path='/',
    endpoint=endpoints.menu_item_instance_put,
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
menu_item_instance_router.add_api_route(
    methods=['DELETE'],
    path='/',
    endpoint=endpoints.menu_item_instance_delete,
    response_model=None,
    status_code=status.HTTP_200_OK,
)

menu_item_router = APIRouter(prefix='/{code}', tags=['menu-item'])
menu_item_router.add_api_route(
    methods=['GET'],
    path='/',
    endpoint=endpoints.menu_item_list,
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
menu_item_router.add_api_route(
    methods=['GET'],
    path='/meta',
    endpoint=endpoints.menu_item_meta,
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
menu_item_router.add_api_route(
    methods=['POST'],
    path='/',
    endpoint=endpoints.menu_item_post,
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
menu_item_router.include_router(router=menu_item_instance_router)

menu_router = APIRouter(prefix='/menu', tags=['menu'])
menu_router.add_api_route(
    methods=['GET'],
    path='/',
    endpoint=endpoints.get_menu_items,
    response_model=list,
    status_code=status.HTTP_200_OK,
)
menu_router.include_router(router=menu_item_router)

router = APIRouter(prefix='/admin', tags=['admin'])
router.include_router(router=menu_router)

__all__ = ('router',)
