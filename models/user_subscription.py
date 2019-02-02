from django.db import models

from core.kernel.models.root import Model
from categories.redisdb import Subscription


class UserSubscription(Model):
    """
    Store subscription of a person to an app's subcategory
    """

    person = models.ForeignKey(
        to='kernel.Person',
        db_index=True,
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        to='categories.Category',
        on_delete=models.CASCADE,
    )
    action = models.CharField(
        max_length=127,
    )

    class Meta:
        """
        Meta class for 'UserSubscription' model
        """

        unique_together = ('person', 'category', 'action')

    def __str__(self):
        return f'{self.action}' \
            f': {self.person.id}[{self.person.full_name}] ' \
            f'- {self.category.slug}'

    def subscribe(self):
        """
        Custom database save method to sync postgres and redis entries
        :return: success True/False
        """

        # Update redis db entries
        try:
            redis_subscription = Subscription(
                category_slug=self.category.slug,
                person_id=self.person.id,
                action=self.action,
            )
        except ValueError:
            # TODO Log
            return False

        redis_result = redis_subscription.save()
        if not redis_result:
            return False

        UserSubscription.objects.create(
            person=self.person,
            category=self.category,
            action=self.action,
        )

        return True

    def unsubscribe(self):
        """
        Custom database delete method to sync postgres and redis entries
        :return: success True/False
        """

        # Update redis db entries
        try:
            redis_subscription = Subscription(
                person_id=self.person.id,
                category_slug=self.category.slug,
                action=self.action,
            )
        except ValueError:
            # TODO Log
            return False

        redis_result = redis_subscription.unsubscribe()
        if not redis_result:
            return False

        try:
            self.delete()
        except UserSubscription.DoesNotExist:
            _ = Subscription(
                person_id=self.person.id,
                category_slug=self.category.slug,
                action=self.action,
            ).unsubscribe()
            return False

        return True
