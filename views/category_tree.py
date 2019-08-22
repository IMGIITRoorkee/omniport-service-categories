from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from discovery.available import available_apps
from categories.models import Category
from categories.serializers import CategoryTreeSerializer


class CategoryTreeViewSet(ModelViewSet):
    """
    The view for read operations of category tree
    """

    serializer_class = CategoryTreeSerializer
    permission_classes = [IsAuthenticated, ]
    http_method_names = ['get', ]

    def get_queryset(self):
        """
        This function displays all applications category tree
        :return:
        """

        available = available_apps(
            request=self.request,
        )
        apps = [
            app
            for (app, app_configuration)
            in available
        ]

        app_filter = Q()
        for app in apps:
            app_filter |= Q(app_subcategory__slug__startswith=app)

        return Category.objects.root_nodes()
