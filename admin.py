from mptt.admin import MPTTModelAdmin

from kernel.admin.site import omnipotence
from categories.models import Category

omnipotence.register(Category, MPTTModelAdmin)
