from categories.serializers import CategorySerializer


class CategoryTreeSerializer(CategorySerializer):
    """
    Serializer class for 'Category' model to represent data in tree structure
    """
    pagination_class = None

    def to_representation(self, instance):
        """
        Defining the representation of serialized data
        :param instance: Object of the 'Category' model
        :return: Serialized representation of the object
        """

        representation = super().to_representation(instance)

        if not instance.is_leaf_node():
            representation['subcategories'] = []
            for child in instance.get_children():
                representation['subcategories'].append(
                    CategoryTreeSerializer(child).data
                )

        return representation
