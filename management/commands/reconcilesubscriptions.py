from django.core.management.base import BaseCommand
from django_redis import get_redis_connection

from categories.models import Category, UserSubscription

client = get_redis_connection('communication')

BATCH_SIZE = 5000


class Command(BaseCommand):
    """
    This class describes the command to be executed
    """

    help = """Rebuild the Redis subscription sets from the database, which is
    the source of truth the settings interface reads.
    Usage: django-admin reconcilesubscriptions [--dry-run] [--action ACTION]
    """

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--action', nargs='*', type=str)

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        subscribers = {}
        actions = set()
        for person_id, category_id, action in UserSubscription.objects.values_list(
                'person_id', 'category_id', 'action'
        ):
            subscribers.setdefault((action, category_id), set()).add(person_id)
            actions.add(action)

        if options['action']:
            actions &= set(options['action'])

        categories = list(Category.objects.all())
        added = removed = 0

        for action in sorted(actions):
            pipe = client.pipeline(transaction=False)
            queued = 0
            action_added = action_removed = 0

            for category in categories:
                # A leaf inherits its ancestors' subscribers because
                # Subscription.save fans a subscription out over leaf
                # descendants; anything else is subscribed to directly
                if category.is_leaf_node():
                    sources = category.get_ancestors(include_self=True)
                else:
                    sources = [category]

                expected = set()
                for source in sources:
                    expected |= subscribers.get((action, source.id), set())

                key = f'categories:subscription:{action}:{category.slug}'
                current = {int(member) for member in client.smembers(key)}

                for person_id in expected - current:
                    action_added += 1
                    if not dry_run:
                        pipe.sadd(key, person_id)
                        queued += 1

                for person_id in current - expected:
                    action_removed += 1
                    if not dry_run:
                        pipe.srem(key, person_id)
                        queued += 1

                if queued >= BATCH_SIZE:
                    pipe.execute()
                    pipe = client.pipeline(transaction=False)
                    queued = 0

            pipe.execute()
            added += action_added
            removed += action_removed
            self.stdout.write(
                f'{action}: {action_added} added, {action_removed} removed'
            )

        verb = 'would change' if dry_run else 'changed'
        self.stdout.write(
            self.style.SUCCESS(f'{verb} {added} additions, {removed} removals')
        )
