from configuration.serializers.app.assets import AssetsSerializer
from formula_one.serializers.base import ModelSerializer

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
            'slug',
        )

    def to_representation(self, instance):
        """
        Defining the representation of serialized data
        :param instance: Object of the 'Category' model
        :return: Serialized representation of the object
        """
        representation = super().to_representation(instance)

        app = instance.app
        representation['isApp'] = app == instance
        representation['app'] = CategorySerializer(app)


        return representation
