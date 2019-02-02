from mptt.admin import MPTTModelAdmin

from omniport.admin.site import omnipotence
from categories.models import Category, UserSubscription

omnipotence.register(Category, MPTTModelAdmin)
omnipotence.register(UserSubscription)
