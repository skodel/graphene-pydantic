# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_schema 1"
] = '''input GraphFoo {
  name: String!
  size: Int!
  color: [[Int]]!
}

type FooBarOutput {
  count: Int!
  name: String!
}

input FooBarInput {
  count: Int!
  name: String = "FooName"
}

type Query {
  listArticles: [Article]

  """the model schema"""
  aNode: NodeModelSchema!
}

type Article {
  id: UUID!
  author: Author!
  body: String!
}

"""
Leverages the internal Python implementation of UUID (uuid.UUID) to provide native UUID objects
in fields, resolvers and input.
"""
scalar UUID

type Author {
  id: UUID!
  email: String!

  """The nickname"""
  nickname: String
}

type NodeModelSchema {
  id: Int!
  name: String!
  nodes: NodeModelSchema
}'''
