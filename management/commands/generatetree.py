from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from categories.models import Category


DISCOVERY = settings.DISCOVERY


class Command(BaseCommand):
    """
    This class describes the command to be executed
    """

    help = """Generate a django-mptt tree of application/service categories.
    Usage: django-admin generatetree [APP_NAME]...
    """

    def add_arguments(self, parser):
        parser.add_argument('apps', nargs='+', type=str)

    def handle(self, *args, **options):
        for app in options['apps']:
            app_conf = DISCOVERY.get_app_configuration(app)
            # if not app_conf:
            #     raise CommandError('Invalid application/service name')

            try:
                print(app_conf)
                app_node, _ = Category.objects.get_or_create(
                    slug=app_conf.nomenclature.name,
                    defaults={'name': app_conf.nomenclature.verbose_name}
                )
                app_node.generate_tree(app_conf.categories)
            except AttributeError as e:
                print(str(e))
                raise CommandError('Invalid application/service name')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated category trees for {options["apps"]}'
            )
        )
