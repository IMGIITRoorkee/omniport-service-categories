from django.db import models
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    """
    Describes the tree format of categorization level in apps and services
    """

    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)
    name = models.CharField(
        max_length=127,
    )
    slug = models.SlugField(
        db_index=True,
        unique=True,
    )
    parent = TreeForeignKey(
        to='self',
        related_name='children',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    meta = models.JSONField(
        verbose_name='Meta Information',
        help_text='Additional information stored as per requirements',
        blank=True,
        null=True,
    )

    class Meta:
        """
        Meta class for 'Category' model.
        """

        verbose_name_plural = 'categories'

    class MPTTMeta:
        """
        Custom Meta class of `django-mptt` based model.
        """

        order_insertion_by = ['name']

    def __str__(self):
        """
        Return the string representation of the model
        :return: the string representation of the model
        """

        slug = self.slug
        name = self.name

        return f'{name}: {slug}'

    @property
    def app(self):
        """
        Get node of the application/service this category belongs to
        :return: A root instance of category mptt model
        """
        if self.is_root_node():
            return self

        return self.get_root()

    @property
    def app_config(self):
        """
        :return:
        """
        return settings.DISCOVERY.get_app_configuration(self.app.slug)

    @classmethod
    def generate_tree(cls, parent):
        """
        Use to create the category tree in the database
        :param parent: categorisation object read from the config file
        :return: success True/False
        """

        root, _ = cls.objects.get_or_create(
            slug=parent.slug,
            defaults={'name': parent.name},
        )
        result = root.create_recursively(parent.subcategories, root.slug)
        return result

    def create_recursively(self, categories, app_slug):
        """
        Recursive function to generate category nodes
        :param app_slug: slug of the app/service
        :param categories: List of category objects
        :return: Success True/False
        """

        res = True

        for category in categories:
            name = category.name
            category_slug = category.slug

            parent, _ = Category.objects.update_or_create(
                name=name,
                slug=f'{app_slug}__{category_slug}',
                parent=self
            )

            res &= parent.create_recursively(
                categories=category.categories or [],
                app_slug=app_slug
            )

        return res
