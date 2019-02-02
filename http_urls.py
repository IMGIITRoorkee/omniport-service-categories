from django.urls import path, include
from rest_framework import routers

from categories.views import (
    CategoryTreeViewSet
)

app_name = 'categories'

router = routers.SimpleRouter()
router.register(
    prefix='category_tree',
    viewset=CategoryTreeViewSet,
    base_name='category_tree'
)

urlpatterns = [
    path('', include(router.urls))
]
