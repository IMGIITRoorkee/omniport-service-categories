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
            category__in=instance.get_ancestors(include_self = True),
            action=self.context.get('action'),
        ).exists()

        if not instance.is_leaf_node():
            # A keepChildren node never gets a row of its own, so it counts as subscribed when every
            # leaf below it is
            if (instance.meta or {}).get('keepChildren') \
                    and not representation['subscribed']:
                representation['subscribed'] = self.covers_every_leaf(instance)

            representation['subcategories'] = []
            for child in instance.get_children():
                representation['subcategories'].append(
                    SubscriptionTreeSerializer(
                        child,
                        context=self.context
                    ).data
                )

        return representation

    def covers_every_leaf(self, instance):
        """
        Check whether every leaf below the node is subscribed, through a row
        on the leaf or on a node between it and this one
        :param instance: Object of the 'Category' model, with no subscribed
        ancestor
        :return: True if every leaf is covered, False otherwise
        """

        # A row on a node covers exactly the leaves its lft and rght enclose
        covering = list(UserSubscription.objects.filter(
            person=self.context.get('person'),
            category__in=instance.get_descendants(),
            action=self.context.get('action'),
        ).values_list('category__lft', 'category__rght'))

        return all(
            any(lft <= leaf.lft and leaf.rght <= rght for lft, rght in covering)
            for leaf in instance.get_leafnodes()
        )
