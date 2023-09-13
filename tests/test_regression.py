import sys
import typing as T
import uuid

import graphene
import pydantic

from graphene_pydantic import PydanticObjectType

import pytest

from graphene_pydantic.inputobjecttype import PydanticInputObjectType


class AuthorModel(pydantic.BaseModel):
    id: pydantic.UUID4
    email: pydantic.constr(strip_whitespace=True, to_lower=True, max_length=50)  # type: ignore
    nickname: T.Optional[str] = pydantic.Field("Nicky", description="The nickname")


class ArticleModel(pydantic.BaseModel):
    id: pydantic.UUID4
    author: AuthorModel
    body: str


class Author(PydanticObjectType):
    class Meta:
        model = AuthorModel


class Article(PydanticObjectType):
    class Meta:
        model = ArticleModel


class NodeModel(pydantic.BaseModel):
    id: int
    name: str
    # nodes: Union['NodeModel', None]
    nodes: T.Optional["NodeModel"]


NodeModel.model_rebuild()


class NodeModelSchema(PydanticObjectType):
    class Meta:  # noqa: too-few-public-methods
        model = NodeModel


NodeModelSchema.resolve_placeholders()


class Foo(pydantic.BaseModel):
    name: str
    size: int
    color: T.Tuple[int, int, int, int]


class GraphFoo(PydanticInputObjectType):
    class Meta:
        model = Foo


class Foo2(pydantic.BaseModel):
    name: str = "FooName"


class Bar2(pydantic.BaseModel):
    count: int


class FooBar2(Foo2, Bar2):
    pass


class FooBarOutput(PydanticObjectType):
    class Meta:
        model = FooBar2


class FooBarInput(PydanticInputObjectType):
    class Meta:
        model = FooBar2


class Query(graphene.ObjectType):
    list_articles = graphene.List(Article)
    a_node = graphene.NonNull(NodeModelSchema, description="the model schema")

    def resolve_list_articles(self, info):
        return []

    def resolve_a_node(self, info):
        return NodeModelSchema(id=1)


def test_schema(snapshot):
    schema = graphene.Schema(query=Query, types=[GraphFoo, FooBarOutput, FooBarInput])
    snapshot.assert_match(str(schema))
