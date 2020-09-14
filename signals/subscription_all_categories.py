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

@receiver(post_save, sender = swapper.get_model_name('kernel', 'Person'))
def subscription_all_categories(sender, instance, **kwargs):
    
    """ Database signal receiver for subscription to all Categories
    whenever a new Person is created.
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    
    category_list = Category.objects.all()
    category_list = list(category_list)
    
    for category in category_list:
        
        _ = UserSubscription(
            person = instance,
            category = category,
            action = 'email',
            ).subscribe()
        
        _ = UserSubscription(
            person = instance,
            category = category,
            action = 'notifications'
        ).subscribe()
                
    return Response(
        data={
                'success': True,
            },
            status=status.HTTP_201_CREATED
        )
