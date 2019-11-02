from django.conf import settings

from formula_one.serializers.base import ModelSerializer
from configuration.serializers.app.app import NomenclatureSerializer

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
            'meta',
        )

    def to_representation(self, instance):
        """
        Defining the representation of serialized data
        :param instance: Object of the 'Category' model
        :return: Serialized representation of the object
        """

        app = instance.app
        representation = super().to_representation(instance)

        representation['isApp'] = app == instance
        app_config = settings.DISCOVERY.get_app_configuration(app.slug)
        if not representation['isApp'] and app_config:
            representation['appInfo'] = NomenclatureSerializer(
                app_config.nomenclature
            ).data

        return representation
