"""
Tests for the subscribed flag the settings page reads for each category

The serializer only needs the models and the base serializer, so they are
stubbed and the module is loaded straight from its file rather than through
the package, whose __init__ needs a configured Django project. Run from the
service folder with
    python -m unittest discover --start-directory tests
"""

import importlib.util
import pathlib
import sys
import types
import unittest
from unittest import mock

from fake_tree import Node, SEASONS, placement_tree, tree

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / 'serializers' / 'subscription_tree.py'
)


class CategorySerializer:
    """
    Stands in for the base serializer, which adds fields this test ignores
    """

    def __init__(self, instance=None, context=None):
        self.instance = instance
        self.context = context or {}

    @property
    def data(self):
        return self.to_representation(self.instance)

    def to_representation(self, instance):
        return {'slug': instance.slug}


_models = types.ModuleType('categories.models')
_models.Category = mock.MagicMock()
_models.UserSubscription = mock.MagicMock()
_serializers = types.ModuleType('categories.serializers')
_serializers.CategorySerializer = CategorySerializer

with mock.patch.dict(sys.modules, {
    'categories': types.ModuleType('categories'),
    'categories.models': _models,
    'categories.serializers': _serializers,
}):
    _spec = importlib.util.spec_from_file_location('subscription_tree', MODULE_PATH)
    subscription_tree = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(subscription_tree)


class Rows:
    """
    Stands in for a UserSubscription queryset over a set of stored rows
    """

    def __init__(self, categories):
        self.categories = categories

    def exists(self):
        return bool(self.categories)

    def values_list(self, *fields):
        assert fields == ('category__lft', 'category__rght')
        return [(category.lft, category.rght) for category in self.categories]


def serialized(root, stored):
    """
    Serialize the tree for a person with rows on the given slugs, and return
    the subscribed flag of every node by slug
    """

    nodes = {node.slug: node for node in root.walk()}
    rows = [nodes[slug] for slug in stored]

    def filter_rows(person, category__in, action):
        return Rows([row for row in rows if row in list(category__in)])

    with mock.patch.object(subscription_tree, 'UserSubscription') as user_subscription:
        user_subscription.objects.filter.side_effect = filter_rows
        data = subscription_tree.SubscriptionTreeSerializer(
            root, context={'person': object(), 'action': 'emails'},
        ).data

    flags = {}

    def collect(representation):
        flags[representation['slug']] = representation['subscribed']
        for child in representation.get('subcategories', []):
            collect(child)

    collect(data)
    return flags


ROOT = 'placement_and_internship'
GROUP = 'placement_and_internship__profile_announcement'
GROUP_SEASONS = [f'{GROUP}__{season}' for season in SEASONS]


def every_leaf(root):
    return [node.slug for node in root.walk() if node.is_leaf_node()]


class KeepChildrenTestCase(unittest.TestCase):
    """
    A keepChildren node reports subscribed when every leaf below it is
    """

    def test_a_group_with_every_season_ticked_is_subscribed(self):
        flags = serialized(placement_tree(), stored=GROUP_SEASONS)

        self.assertTrue(flags[GROUP])

    def test_a_group_with_some_seasons_ticked_is_not_subscribed(self):
        flags = serialized(placement_tree(), stored=GROUP_SEASONS[:2])

        self.assertFalse(flags[GROUP])

    def test_a_group_with_no_season_ticked_is_not_subscribed(self):
        flags = serialized(placement_tree(), stored=[])

        self.assertFalse(flags[GROUP])
        self.assertFalse(flags[ROOT])

    def test_the_root_is_subscribed_when_every_row_is_ticked(self):
        root = placement_tree()

        flags = serialized(root, stored=every_leaf(root))

        self.assertTrue(flags[ROOT])
        self.assertTrue(all(flags.values()))

    def test_the_root_is_not_subscribed_when_one_row_is_missing(self):
        root = placement_tree()
        stored = [slug for slug in every_leaf(root) if slug != GROUP_SEASONS[0]]

        flags = serialized(root, stored=stored)

        self.assertFalse(flags[ROOT])
        self.assertFalse(flags[GROUP])
        self.assertTrue(flags['placement_and_internship__results'])

    def test_an_old_group_row_still_counts(self):
        flags = serialized(placement_tree(), stored=[GROUP])

        self.assertTrue(flags[GROUP])
        self.assertTrue(all(flags[slug] for slug in GROUP_SEASONS))
        self.assertFalse(flags[ROOT])

    def test_an_old_root_row_still_counts(self):
        flags = serialized(placement_tree(), stored=[ROOT])

        self.assertTrue(all(flags.values()))

    def test_a_row_on_a_node_between_counts_for_its_leaves(self):
        root = tree(Node(
            'app',
            [
                Node('app__group', [Node('app__group__a'), Node('app__group__b')]),
                Node('app__other'),
            ],
            meta={'keepChildren': True},
        ))

        flags = serialized(root, stored=['app__group', 'app__other'])

        self.assertTrue(flags['app'])


class OtherNodesTestCase(unittest.TestCase):
    """
    Nodes without keepChildren report only their own and their ancestors'
    rows, as before
    """

    def test_a_plain_group_with_every_child_ticked_is_not_subscribed(self):
        root = tree(Node('app', [
            Node('app__group', [Node('app__group__a'), Node('app__group__b')]),
        ]))

        flags = serialized(root, stored=['app__group__a', 'app__group__b'])

        self.assertFalse(flags['app__group'])
        self.assertFalse(flags['app'])

    def test_a_plain_group_with_its_own_row_is_subscribed(self):
        root = tree(Node('app', [
            Node('app__group', [Node('app__group__a'), Node('app__group__b')]),
        ]))

        flags = serialized(root, stored=['app__group'])

        self.assertTrue(flags['app__group'])
        self.assertTrue(flags['app__group__a'])
        self.assertFalse(flags['app'])


if __name__ == '__main__':
    unittest.main()
