from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    """
    This model describes the tree format of categorization level in apps and services
    """

    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)

    name = models.CharField(
        max_length=127,
    )
    slug = models.SlugField()

    parent = TreeForeignKey(
        to='self',
        related_name='children',
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        blank=True,
    )

    class Meta:
        """

        """

        unique_together = ('parent', 'slug',)
        verbose_name_plural = 'categories'

    class MPTTMeta:
        """

        """

        order_insertion_by = ['name']

    def __str__(self):
        """
        Return the string representation of the model
        :return: the string representation of the model
        """

        slug = self.slug
        name = self.name

        return f'{slug}: {name}'

    @classmethod
    def register_app(cls, name, slug):
        """
        Use to register app as a category(child) of ROOT.
        :param name: Name of the app
        :param slug: Slug string
        :return: TODO
        """

        root = Category.objects.get(name='ROOT')
        return cls.objects.create(
            name=name,
            parent=root,
            slug=slug
        )

    @classmethod
    def create_category_tree(cls, category_dict, rebuild=False):
        """
        Use to create the category tree from a dictionary
        :param app: App name
        :param category_dict: Category tree in dictionary form.
        :return:
        """

        try:
            app = Category.objects.get(name=category_dict['app_name'])
        except Category.DoesNotExist:
            app = cls.register_app(
                name=category_dict.app_name,
                slug=category_dict.app_slug
            )
        except Category.MultipleObjectsReturned:
            # TODO logging
            return False
