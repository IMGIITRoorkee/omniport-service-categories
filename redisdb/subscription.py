from django.db.models import F
from django_redis import get_redis_connection
from categories.models import Category


client = get_redis_connection('communication')


class Subscription:
    """
    This class maps subscription to app categories
    """

    def __init__(self, category_slug, person_id, action):
        """
        Constructor to create a subscription mapping between
        a category and a person
        :param category_slug: Used to identify a category
        :param person_id: Person Db id to identify the person
        :param action: Action to which the subscription corresponds to
        """

        self.category_slug = category_slug
        self.person_id = person_id
        self.action = action

    def save(self):
        """
        To save person for an action for all the subcategories of the
        category with slug to self.category_slug
        :return: success True/False
        """

        try:
            root = Category.objects.get(
                slug=self.category_slug
            )
        except Category.DoesNotExist:
            raise ValueError(
                f'No category node exists for the slug \'{self.category_slug}\''
            )

        # Get all leaf nodes of this root category
        sub_categories = root.get_descendants().filter(rght=F('lft') + 1)

        pipe = client.pipeline(transaction=True)

        pipe.sadd(
            f'categories:subscription:{self.action}:{root.slug}',
            self.person_id
        )

        for category in sub_categories:
            # Use SET for `subscribed users`
            pipe.sadd(
                f'categories:subscription:{self.action}:{category.slug}',
                self.person_id
            )

        res = pipe.execute()  # Non-strict query
        return all(res)

    def delete(self):
        """
        To delete person for an action from all the subcategories of the
        category with slug to self.category_slug
        :return: success True/False
        """

        try:
            root = Category.objects.get(
                slug=self.category_slug
            )
        except Category.DoesNotExist:
            raise ValueError(
                f'No category node exists for the slug \'{self.category_slug}\''
            )

        # Get all leaf nodes of this root category
        sub_categories = root.get_descendants().filter(rght=F('lft') + 1)

        pipe = client.pipeline(transaction=True)

        pipe.srem(
            f'categories:subscription:{self.action}:{root.slug}',
            self.person_id
        )

        for category in sub_categories:
            pipe.srem(
                f'categories:subscription:{self.action}:{category.slug}',
                self.person_id
            )
        res = pipe.execute()  # Non-strict query
        return all(res)

    @staticmethod
    def fetch_people(category_slug, action):
        """
        Static method to fetch subscribed users corresponding
         to a category for a particular action.
        :param category_slug: Category slug of the root category
        :param action: subscription action
        :return: list of ids of subscribed users
        """

        try:
            root = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            raise ValueError(
                f'No category node exists for the slug \'{category_slug}\''
            )

        # Get all leaf nodes of this root category
        sub_categories = root.get_descendants(include_self=True).filter(rght=F('lft') + 1)
        categories = list(sub_categories)
        categories.append(root)

        if sub_categories:
            result = client.sunion([
                f'categories:subscription:{action}:{category.slug}'
                for category in sub_categories
            ])
        else:
            result = client.smembers(
                f'categories:subscription:{action}:{root.slug}'
            )

        # return result
        return [s.decode('utf-8') for s in result]
