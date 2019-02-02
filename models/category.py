from django.db import models
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
        primary_key=True
    )
    parent = TreeForeignKey(
        to='self',
        related_name='children',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
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

    def get_application(self):
        """
        Get node of the application/service this category belongs to
        :return: A root instance of category mptt model
        """
        return self.get_root()

    def generate_tree(self, categories):
        """
        Use to create the category tree in the database
        :param categories: List of category objects
        :return: success True/False
        """

        if not self.is_root_node():
            raise AttributeError('Method valid for only app root node')

        result = self._create_recursively(categories, self.slug)
        return result

    def _create_recursively(self, categories, app_slug):
        """
        Recursive function to generate category nodes
        :param categories: List of category objects
        :return: Success True/False
        """

        res = True

        for category in categories:
            print(type(category))
            name = category.name
            category_slug = category.slug

            parent = Category.objects.create(
                name=name,
                slug=f'{app_slug}__{category_slug}',
                parent=self
            )

            res &= parent._create_recursively(
                categories=category.subcategories or [],
                app_slug=app_slug
            )

        return res
