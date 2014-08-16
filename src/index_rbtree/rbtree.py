#!/usr/bin/env python
#coding:utf-8
# Author:  mozman (python version)
# Purpose: red-black tree module (Julienne Walker's none recursive algorithm)
# source: http://eternallyconfuzzled.com/tuts/datastructures/jsw_tut_rbtree.aspx
# Created: 01.05.2010
# Copyright (c) 2010-2013 by Manfred Moitzi
# License: MIT License

# Conclusion of Julian Walker

# Red black trees are interesting beasts. They're believed to be simpler than
# AVL trees (their direct competitor), and at first glance this seems to be the
# case because insertion is a breeze. However, when one begins to play with the
# deletion algorithm, red black trees become very tricky. However, the
# counterweight to this added complexity is that both insertion and deletion
# can be implemented using a single pass, top-down algorithm. Such is not the
# case with AVL trees, where only the insertion algorithm can be written top-down.
# Deletion from an AVL tree requires a bottom-up algorithm.

# So when do you use a red black tree? That's really your decision, but I've
# found that red black trees are best suited to largely random data that has
# occasional degenerate runs, and searches have no locality of reference. This
# takes full advantage of the minimal work that red black trees perform to
# maintain balance compared to AVL trees and still allows for speedy searches.

# Red black trees are popular, as most data structures with a whimsical name.
# For example, in Java and C++, the library map structures are typically
# implemented with a red black tree. Red black trees are also comparable in
# speed to AVL trees. While the balance is not quite as good, the work it takes
# to maintain balance is usually better in a red black tree. There are a few
# misconceptions floating around, but for the most part the hype about red black
# trees is accurate.

from __future__ import absolute_import

from .abctree import ABCTree

__all__ = ['RBTree']

class Node(object):
    """Internal object, represents a tree node."""

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.red = True
        self._parent = None
        self._left = None
        self._right = None
        self.number_left = 0
        self.number_right = 0

    def free(self):
        self._parent = None
        self._left = None
        self._right = None
        self.key = None
        self.value = None
        self.number_left = None
        self.number_right = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, node):
        # First sever our parent's connection to us...
        if self._parent:
            if self._parent.left == self:
                self._parent._left = None
                self._parent.number_left = 0
            elif self._parent.right == self:
                self._parent._right = None
                self._parent.number_right = 0
            else:
                assert False

        self._parent = node

    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, node):
        if self._left:
            self._left.parent = None
        self._left = None

        if node is None:
            self.number_left = 0
            self._fix_parent()
            return

        if node.parent is not None:
            if node.parent.left is node:
                node.parent.number_left = 0
            elif node.parent.right is node:
                node.parent.number_right = 0
            else:
                assert False

        self.number_left = node.count_subtree()
     #  if node.left is not None or node.right is not None:
     #      assert self._left is not self._right

        self._left = node
        node.parent = self
        self._fix_parent()

    @property
    def right(self):
        return self._right

    @right.setter
    def right(self, node):
        if self._right:
            self._right.parent = None
        self._right = None

        if node is None:
            self.number_right = 0
            self._fix_parent()
            return

        if node.parent is not None:
            if node.parent.left is node:
                node.parent.left = None
            elif node.parent.right is node:
                node.parent.right = None
            else:
                assert False

        self.number_right = node.count_subtree()
        self._right = node
        node.parent = self
        # Recurses up if there's a problem.
        self._fix_parent()

    def _fix_parent(self):
        cursor = self
        continue_fixing = True
        while continue_fixing:
            continue_fixing = False

            if cursor.parent:
                subtree = cursor.count_subtree()
                if cursor.parent._left is cursor:
                    if cursor.parent.number_left != subtree:
                        cursor.parent.number_left = subtree
                        continue_fixing = True
                else:
                    if cursor.parent.number_right != subtree:
                        cursor.parent.number_right = subtree
                        continue_fixing = True
            cursor = cursor._parent

    def count_subtree(self):
        return 1 + self.number_left + self.number_right

    @staticmethod
    def is_red(node):
        return node is not None and node.red

    @staticmethod
    def rotate_single(node, direction):
        other_side = 1 - direction
        save = node[other_side]
        node[other_side] = save[direction]
        save[direction] = node
        node.red = True
        save.red = False
        return save

    @staticmethod
    def rotate_double(node, direction):
        other_side = 1 - direction
        node[other_side] = Node.rotate_single(node[other_side], other_side)
        return Node.rotate_single(node, direction)

    def to_str(self):
        return "{0}: {1} | <{2}, {3}> [{4}, {5}]".format(
                self.key, self.value, self.number_left, self.number_right,
                self.left.key if self.left else '',
                self.right.key if self.right else '')

    def __getitem__(self, key):
        """N.__getitem__(key) <==> x[key], where key is 0 (left) or 1 (right)."""
        return self.left if key == 0 else self.right

    def __setitem__(self, direction, node):
        """N.__setitem__(direction, node) <==> x[direction]=node,
        where direction is 0 (left) or 1 (right)."""
        if direction == 0:
            self.left = node
        else:
            self.right = node


def quiet(node):
    if not node:
        return

    error = False
    error_msg = []

    def recurser(node):
        if not node:
            return
        if node._left:
            if node.number_left != node._left.count_subtree():
                error = True
                error_msg.append("Number left... {0} != {1}".format(
                        node.number_left, node._left.count_subtree()))
        if node._right:
            if node.number_right != node._right.count_subtree():
                error = True
                error_msg.append("Number right... {0} != {1}".format(
                        node.number_right, node._right.count_subtree()))
        if node.parent:
            if node is node.parent._left:
                if node.count_subtree() != node.parent.number_left:
                    error = True
                    error_msg.append("Parent left... {0} != {1}".format(
                            node.count_subtree(), node.parent.number_left))
            elif node is node.parent._right:
                if node.count_subtree() != node.parent.number_right:
                    error = True
                    error_msg.append("Parent right... {0} != {1}".format(
                            node.count_subtree(), node.parent.number_right))
            else:
                error = True
                error_msg.append("Node is not child of its parent.")
        recurser(node._left)
        recurser(node._right)

    root = node
    while root.parent:
        if root.parent._left is not root and root.parent._right is not root:
            error = True
            error_msg.append("Node is not child of its parent.")
            break
        root = root.parent
    recurser(root)


class RBTree(ABCTree):
    """
    RBTree implements a balanced binary tree with a dict-like interface.

    see: http://en.wikipedia.org/wiki/Red_black_tree

    A red-black tree is a type of self-balancing binary search tree, a data
    structure used in computing science, typically used to implement associative
    arrays. The original structure was invented in 1972 by Rudolf Bayer, who
    called them "symmetric binary B-trees", but acquired its modern name in a
    paper in 1978 by Leonidas J. Guibas and Robert Sedgewick. It is complex,
    but has good worst-case running time for its operations and is efficient in
    practice: it can search, insert, and delete in O(log n) time, where n is
    total number of elements in the tree. Put very simply, a red-black tree is a
    binary search tree which inserts and removes intelligently, to ensure the
    tree is reasonably balanced.

    RBTree() -> new empty tree.
    RBTree(mapping) -> new tree initialized from a mapping
    RBTree(seq) -> new tree initialized from seq [(k1, v1), (k2, v2), ... (kn, vn)]

    see also abctree.ABCTree() class.
    """
    def _new_node(self, key, value):
        """Create a new tree node."""
        self._count += 1
        return Node(key, value)

    def index(self, key):
        node = self._root
        count = 0
        while node is not None:
            if key == node.key:
                return count + (node.number_left if node else 0)
            elif key < node.key:
                node = node.left
            else:
                count += 1 + (node.number_left if node else 0)
                node = node.right
        raise KeyError(str(key))

    def insert(self, key, value):
        """T.insert(key, value) <==> T[key] = value, insert key, value into tree."""
        if self._root is None:  # Empty tree case
            self._root = self._new_node(key, value)
            self._root.red = False  # make root black
            return

        head = Node()  # False tree root
        grand_parent = None
        grand_grand_parent = head
        parent = None  # parent
        direction = 0
        last = 0

        # Set up helpers
        grand_grand_parent.right = self._root
        node = grand_grand_parent.right
        # Search down the tree
        while True:
            if node is None:  # Insert new node at the bottom
                node = self._new_node(key, value)
                parent[direction] = node
            elif Node.is_red(node.left) and Node.is_red(node.right):  # Color flip
                node.red = True
                node.left.red = False
                node.right.red = False

            # Fix red violation
            if Node.is_red(node) and Node.is_red(parent):
                direction2 = 1 if grand_grand_parent.right is grand_parent else 0
                if node is parent[last]:
                    grand_grand_parent[direction2] = \
                            Node.rotate_single(grand_parent, 1 - last)
                else:
                    grand_grand_parent[direction2] = \
                            Node.rotate_double(grand_parent, 1 - last)

            # Stop if found
            if key == node.key:
                node.value = value  # set new value for key
                break

            last = direction
            direction = 0 if key < node.key else 1
            # Update helpers
            if grand_parent is not None:
                grand_grand_parent = grand_parent
            grand_parent = parent
            parent = node
            node = node[direction]

        self._root = head.right  # Update root
        self._root.red = False  # make root black

    def remove(self, key):
        """T.remove(key) <==> del T[key], remove item <key> from tree."""
        if self._root is None:
            raise KeyError(str(key))
        head = Node()  # False tree root
        node = head
        node.right = self._root
        parent = None
        grand_parent = None
        found = None  # Found item
        direction = 1

        # Search and push a red down
        while node[direction] is not None:
            last = direction

            # Update helpers
            grand_parent = parent
            parent = node
            node = node[direction]

            direction = 1 if key > node.key else 0

            # Save found node
            if key == node.key:
                found = node

            # Push the red node down
            if not Node.is_red(node) and not Node.is_red(node[direction]):
                if Node.is_red(node[1 - direction]):
                    parent[last] = Node.rotate_single(node, direction)
                    parent = parent[last]
                elif not Node.is_red(node[1 - direction]):
                    sibling = parent[1 - last]
                    if sibling is not None:
                        if (not Node.is_red(sibling[1 - last]) and
                            not Node.is_red(sibling[last])):
                            # Color flip
                            parent.red = False
                            sibling.red = True
                            node.red = True
                        else:
                            direction2 = 1 if grand_parent.right is parent else 0
                            if Node.is_red(sibling[last]):
                                grand_parent[direction2] = \
                                    Node.rotate_double(parent, last)
                            elif Node.is_red(sibling[1-last]):
                                grand_parent[direction2] = \
                                        Node.rotate_single(parent, last)
                            # Ensure correct coloring
                            grand_parent[direction2].red = True
                            node.red = True
                            grand_parent[direction2].left.red = False
                            grand_parent[direction2].right.red = False

        # Replace and remove if found
        if found is not None:
            found.key = node.key
            found.value = node.value
            parent[int(parent.right is node)] = node[int(node.left is None)]
            node.free()
            self._count -= 1

        # Update root and make it black
        self._root = head.right
        if self._root is not None:
            self._root.red = False
        if not found:
            raise KeyError(str(key))

