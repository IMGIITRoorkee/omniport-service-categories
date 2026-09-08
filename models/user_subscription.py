import logging

import swapper
from django.db import models, transaction

from formula_one.models.base import Model
from categories.redisdb import Subscription

logger = logging.getLogger('categories')


class UserSubscription(Model):
    """
    Store subscription of a person to an app's subcategory
    """

    person = models.ForeignKey(
        to=swapper.get_model_name('kernel', 'Person'),
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
            f': {self.person.full_name} ' \
            f'- {self.category.slug}'

    def subscribe(self):
        """
        Custom create method to sync database and communication-store
        entries
        :return: success True/False
        """

        # The row is written first so that a failing Redis write rolls it back,
        # rather than leaving the two stores disagreeing
        try:
            with transaction.atomic():
                UserSubscription.objects.get_or_create(
                    person=self.person,
                    category=self.category,
                    action=self.action,
                )
                Subscription(
                    category_slug=self.category.slug,
                    person_id=self.person.id,
                    action=self.action,
                ).save()
        except Exception:
            logger.exception(
                'Could not subscribe person %s to %s for %s',
                self.person_id, self.category.slug, self.action,
            )
            return False

        return True

    def unsubscribe(self):
        """
        Custom delete method to sync sync database and communication-store
        entries
        :return: success True/False
        """

        try:
            with transaction.atomic():
                self.__class__.objects.filter(
                    person=self.person,
                    category=self.category,
                    action=self.action,
                ).delete()
                Subscription(
                    person_id=self.person.id,
                    category_slug=self.category.slug,
                    action=self.action,
                ).delete()
        except Exception:
            logger.exception(
                'Could not unsubscribe person %s from %s for %s',
                self.person_id, self.category.slug, self.action,
            )
            return False

        return True
