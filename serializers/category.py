from django.conf import settings
from rest_framework import serializers

from formula_one.serializers.base import ModelSerializer
from configuration.serializers.app.app import AppSerializer
from categories.models import Category

# Category.meta also holds the token that gates emails/send/, so only the keys
# the interface reads are serialized
PUBLIC_META_KEYS = ('icon',)


class CategorySerializer(ModelSerializer):
    """
    Serializer class for 'Category' model
    """

    meta = serializers.SerializerMethodField()

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

    def get_meta(self, instance):
        """
        Restrict the serialized meta to the keys the interface reads
        :param instance: Object of the 'Category' model
        :return: The public subset of the object's meta information
        """

        meta = instance.meta or {}

        return {
            key: meta[key]
            for key in PUBLIC_META_KEYS
            if key in meta
        }

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
        if app_config:
            representation['appInfo'] = AppSerializer(
                app_config,
            ).data

        return representation
