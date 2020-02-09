from django.urls import path, include
from rest_framework import routers

from categories.views import (
    SubscriptionTreeViewSet
)

app_name = 'categories'

router = routers.SimpleRouter()
router.register(
    prefix='subscription_tree',
    viewset=SubscriptionTreeViewSet,
    basename='subscription_tree'
)

urlpatterns = [
    path('', include(router.urls))
]
