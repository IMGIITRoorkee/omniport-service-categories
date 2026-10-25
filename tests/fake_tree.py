"""
A stand-in for the Category tree, for tests that run without Django
"""


class Node:
    """
    Stands in for a Category with the tree methods the service reads
    """

    def __init__(self, slug, children=(), meta=None):
        self.slug = slug
        self.children = list(children)
        self.meta = meta
        self.parent = None
        self.lft = self.rght = None
        for child in self.children:
            child.parent = self

    def is_leaf_node(self):
        return not self.children

    def is_root_node(self):
        return self.parent is None

    def get_children(self):
        return self.children

    def get_ancestors(self, include_self=False):
        ancestors = [self] if include_self else []
        node = self.parent
        while node is not None:
            ancestors.append(node)
            node = node.parent
        return ancestors

    def get_descendants(self):
        return [node for node in self.walk() if node is not self]

    def get_leafnodes(self):
        return [node for node in self.get_descendants() if node.is_leaf_node()]

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


def tree(root):
    """
    Number the nodes the way django-mptt does, so that a node's lft and rght
    enclose those of everything below it
    :param root: the root Node
    :return: the same root
    """

    counter = 0

    def number(node):
        nonlocal counter
        counter += 1
        node.lft = counter
        for child in node.children:
            number(child)
        counter += 1
        node.rght = counter

    number(root)
    return root


SEASONS = ('pla', 'int', 'ear')


def placement_tree():
    """
    The placement tree from section 2 of the plan, with its meta
    """

    group_meta = {'fcmTopic': False, 'keepChildren': True}

    def group(slug):
        return Node(
            f'placement_and_internship__{slug}',
            [
                Node(f'placement_and_internship__{slug}__{season}', meta={'fcmTopic': True})
                for season in SEASONS
            ],
            meta=group_meta,
        )

    return tree(Node(
        'placement_and_internship',
        [
            group('profile_announcement'),
            group('profile_update'),
            group('results'),
            Node('placement_and_internship__app_status_update', meta={'fcmTopic': False}),
            Node('placement_and_internship__credits_audit', meta={'fcmTopic': False}),
        ],
        meta={'keepChildren': True},
    ))
