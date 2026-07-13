from django_redis import get_redis_connection
from django.core.management.base import BaseCommand

from categories.models import UserSubscription
from categories.redisdb import Subscription


class Command(BaseCommand):
    """
    Rebuild the Redis subscription sets so they exactly match the
    UserSubscription table (the source of truth).

    Existing drift - e.g. a person removed from a Redis set but whose DB row
    survived, or the reverse - is corrected by flushing every
    'categories:subscription:<action>:*' key and replaying save() over the DB
    rows. save() expands a parent subscription back into all of its leaf sets,
    so the reconstruction matches what fetch_people() reads.

    Usage:
        django-admin reconcilesubscriptions               # all actions
        django-admin reconcilesubscriptions --action emails
        django-admin reconcilesubscriptions --dry-run
    """

    help = 'Rebuild Redis subscription sets from the UserSubscription table.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            default=None,
            help='Only reconcile this action (e.g. emails). Default: all.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report what would change without touching Redis.',
        )

    def handle(self, *args, **options):
        client = get_redis_connection('communication')
        dry_run = options['dry_run']

        # Actions to reconcile: the requested one, or every action that shows
        # up in the DB or in existing Redis keys (so stale keys for a
        # fully-unsubscribed action get cleared too).
        if options['action']:
            actions = {options['action']}
        else:
            actions = set(
                UserSubscription.objects.values_list('action', flat=True).distinct()
            )
            for key in client.scan_iter('categories:subscription:*'):
                parts = key.decode('utf-8').split(':')
                if len(parts) >= 3:
                    actions.add(parts[2])

        if not actions:
            self.stdout.write('Nothing to reconcile.')
            return

        for action in sorted(actions):
            keys = list(client.scan_iter(f'categories:subscription:{action}:*'))
            rows = UserSubscription.objects.filter(action=action)

            if dry_run:
                self.stdout.write(
                    f'[dry-run] {action}: would clear {len(keys)} Redis keys '
                    f'and replay {rows.count()} DB rows'
                )
                continue

            if keys:
                client.delete(*keys)

            replayed = 0
            for subscription in rows.select_related('category'):
                Subscription(
                    category_slug=subscription.category.slug,
                    person_id=subscription.person_id,
                    action=action,
                ).save()
                replayed += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'{action}: cleared {len(keys)} keys, replayed {replayed} rows'
                )
            )

        if dry_run:
            self.stdout.write('Dry run complete - no changes made.')
