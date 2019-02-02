from kernel.serializers.root import ModelSerializer

from categories.models import Category


class CategorySerializer(ModelSerializer):
    """
    Serializer class for 'Category' model
    """

    class Meta:
        """
        Meta class for 'CategorySerializer'
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
        if instance.level < 2:
            return representation

        app = instance.get_application()
        if app is not None:
            representation['app'] = CategorySerializer(app).data

        return representation
