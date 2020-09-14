import swapper

from django.dispatch import receiver

from rest_framework import status
from rest_framework.response import Response

from django.db.models.signals import (
    post_save
)

from categories.models import (
    UserSubscription,
    Category
)

@receiver(post_save, sender = Category)
def subscription_all_persons(sender, instance, **kwargs):
    
    """ Database signal receiver for the subscription of all Persons
    to every new Category created.
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    
    persons_list = swapper.load_model('kernel', 'Person').objects.all()
    persons_list = list(persons_list)
    
    for person in persons_list:
        _ = UserSubscription(
            person = person,
            category = instance,
            action = 'email'
        ).subscribe()
        
        _ = UserSubscription(
            person = person,
            category = instance,
            action = 'notifications'
        ).subscribe()
        
    return Response(
        data={
            'success': True,
        },
        status=status.HTTP_201_CREATED
    )
