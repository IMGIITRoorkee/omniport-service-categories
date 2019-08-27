from categories.models import Category
from categories.serializers import CategorySerializer
from categories.models import UserSubscription


class SubscriptionTreeSerializer(CategorySerializer):
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
        representation['subscribed'] = UserSubscription.objects.filter(
            person=self.context.get('person'),
            category=instance,
            action=self.context.get('action'),
        ).exists()

        if not instance.is_leaf_node():
            representation['subcategories'] = []
            for child in instance.get_children():
                representation['subcategories'].append(
                    SubscriptionTreeSerializer(
                        child,
                        context=self.context
                    ).data
                )

        return representation
