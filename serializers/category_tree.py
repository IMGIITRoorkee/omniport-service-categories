from kernel.serializers.root import ModelSerializer

from categories.models import Category


class CategoryTreeSerializer(ModelSerializer):
    """
    Serializer class for 'Category' model to represent data in tree structure
    """
    pagination_class = None

    class Meta:
        """
        Meta class for 'CategoryTreeSerializer'
        """
        model = Category
        fields = (
            'name',
            'slug'
        )

    def to_representation(self, instance):
        """
        Defining the representation of serialized data
        :param instance: Object of the 'Category' model
        :return: Serialized representation of the object
        """

        representation = super().to_representation(instance)
        print(type(representation), representation)
        if not instance.is_leaf_node():
            representation['children'] = []
            for child in instance.get_children():
                representation['children'].append(
                    CategoryTreeSerializer(child).data
                )

        return representation
