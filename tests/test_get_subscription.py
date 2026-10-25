"""
Tests for the choice of which category rows to store for a subscription

The module under test only needs the two model classes, so they are stubbed
and the module is loaded straight from its file rather than through the
package, whose __init__ needs a configured Django project. Run from the
service folder with
    python -m unittest discover --start-directory tests
"""

import importlib.util
import pathlib
import sys
import types
import unittest
from unittest import mock

from fake_tree import Node, placement_tree

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / 'utils' / 'get_subscription.py'
)

_models = types.ModuleType('categories.models')
_models.Category = mock.MagicMock()
_models.UserSubscription = mock.MagicMock()

with mock.patch.dict(sys.modules, {
    'categories': types.ModuleType('categories'),
    'categories.models': _models,
}):
    _spec = importlib.util.spec_from_file_location('get_subscription', MODULE_PATH)
    get_subscription = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(get_subscription)


def stored_rows(root, save, already=()):
    """
    Run GetSubscription over the tree and return the slugs it would
    subscribe and unsubscribe
    """

    nodes = {node.slug: node for node in root.walk()}
    drop = [slug for slug in nodes if slug not in save]
    existing = [
        types.SimpleNamespace(category=nodes[slug])
        for slug in already
    ]

    with mock.patch.object(get_subscription, 'Category') as category, \
            mock.patch.object(get_subscription, 'UserSubscription') as user_subscription:
        category.objects.get.side_effect = lambda slug: nodes[slug]
        user_subscription.objects.filter.return_value = existing
        subscribe, unsubscribe = get_subscription.GetSubscription(
            list(save), drop, person=object(), action='emails',
        ).get_should_subscribe()

    return (
        sorted(node.slug for node in subscribe),
        sorted(node.slug for node in unsubscribe),
    )


class KeepChildrenTestCase(unittest.TestCase):
    """
    A node with meta.keepChildren keeps its children's rows when all of
    them are ticked
    """

    def test_ticking_every_child_keeps_the_child_rows(self):
        root = placement_tree()
        leaves = [node.slug for node in root.walk() if node.is_leaf_node()]

        subscribe, unsubscribe = stored_rows(root, save=leaves)

        self.assertEqual(subscribe, sorted(leaves))
        self.assertEqual(unsubscribe, [])

    def test_ticking_all_seasons_of_one_group_keeps_the_season_rows(self):
        root = placement_tree()
        seasons = [
            f'placement_and_internship__profile_announcement__{season}'
            for season in ('pla', 'int', 'ear')
        ]

        subscribe, _ = stored_rows(root, save=seasons)

        self.assertEqual(subscribe, sorted(seasons))

    def test_an_old_group_row_is_swapped_for_the_child_rows(self):
        root = placement_tree()
        group = 'placement_and_internship__results'
        seasons = [f'{group}__{season}' for season in ('pla', 'int', 'ear')]

        subscribe, unsubscribe = stored_rows(root, save=seasons, already=[group])

        self.assertEqual(subscribe, sorted(seasons))
        self.assertEqual(unsubscribe, [group])

    def test_an_old_root_row_is_swapped_for_the_child_rows(self):
        root = placement_tree()
        leaves = [node.slug for node in root.walk() if node.is_leaf_node()]

        subscribe, unsubscribe = stored_rows(
            root, save=leaves, already=['placement_and_internship'],
        )

        self.assertEqual(subscribe, sorted(leaves))
        self.assertEqual(unsubscribe, ['placement_and_internship'])


class CollapseTestCase(unittest.TestCase):
    """
    Nodes without keepChildren still collapse, as before
    """

    def test_ticking_every_child_stores_the_parent_instead(self):
        root = Node('app', [
            Node('app__group', [Node('app__group__a'), Node('app__group__b')]),
            Node('app__other'),
        ])

        subscribe, _ = stored_rows(root, save=['app__group__a', 'app__group__b'])

        self.assertEqual(subscribe, ['app__group'])

    def test_ticking_everything_stores_only_the_root(self):
        root = Node('app', [
            Node('app__group', [Node('app__group__a'), Node('app__group__b')]),
            Node('app__other'),
        ])
        everything = [node.slug for node in root.walk()]

        subscribe, _ = stored_rows(root, save=everything)

        self.assertEqual(subscribe, ['app'])

    def test_a_kept_group_stops_the_collapse_above_it(self):
        root = Node('app', [
            Node(
                'app__group',
                [Node('app__group__a'), Node('app__group__b')],
                meta={'keepChildren': True},
            ),
            Node('app__other'),
        ])
        everything = [node.slug for node in root.walk()]

        subscribe, _ = stored_rows(root, save=everything)

        self.assertEqual(subscribe, ['app__group__a', 'app__group__b', 'app__other'])

    def test_a_group_under_a_kept_root_still_collapses(self):
        root = Node(
            'app',
            [
                Node('app__group', [Node('app__group__a'), Node('app__group__b')]),
                Node('app__other'),
            ],
            meta={'keepChildren': True},
        )
        everything = [node.slug for node in root.walk()]

        subscribe, _ = stored_rows(root, save=everything)

        self.assertEqual(subscribe, ['app__group', 'app__other'])


if __name__ == '__main__':
    unittest.main()
