from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

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
        return Category.objects.root_nodes()
