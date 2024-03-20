import typing as T

import pytest
from pydantic import BaseModel

from graphene_pydantic.objecttype import PydanticObjectType
from pydantic.types import StringConstraints


def test_object_type_onlyfields():
    class Foo(BaseModel):
        name: str
        size: int
        color: T.Tuple[int, int, int, int]

    class GraphFoo(PydanticObjectType):
        class Meta:
            model = Foo
            only_fields = ("name",)

    assert list(GraphFoo._meta.fields.keys()) == ["name"]


def test_object_type_excludefields():
    class Foo(BaseModel):
        name: str
        size: int
        color: T.Tuple[int, int, int, int]

    class GraphFoo(PydanticObjectType):
        class Meta:
            model = Foo
            exclude_fields = ("size",)

    assert list(GraphFoo._meta.fields.keys()) == ["name", "color"]


def test_object_type_onlyandexclude():
    class Foo(BaseModel):
        name: str
        size: int
        color: T.Tuple[int, int, int, int]

    with pytest.raises(ValueError):

        class GraphFoo(PydanticObjectType):
            class Meta:
                model = Foo
                only_fields = ("name",)
                exclude_fields = ("size",)


def test_object_type_annotated(snapshot):
    import pydantic

    class Child(BaseModel):
        name: str
        age: int

    class GraphChild(PydanticObjectType):
        class Meta:
            model = Child

    class AnnotatedName(BaseModel):
        name: T.Annotated[str, StringConstraints(min_length=2, max_length=256)]
        name_optional: T.Annotated[
            str, StringConstraints(min_length=2, max_length=256)
        ] | None = None

        scaled_values: T.Annotated[T.List[int], pydantic.Field(min_length=2)]
        scaled_values_optional: T.Annotated[
            T.List[int], pydantic.Field(min_length=2)
        ] | None = None

        objs: T.Annotated[T.List[Child], pydantic.Field(min_length=2)]
        optional_objs: T.Annotated[
            T.List[Child], pydantic.Field(min_length=2)
        ] | None = None

    class GraphAnnotatedName(PydanticObjectType):
        class Meta:
            model = AnnotatedName

    import graphene

    class Query(graphene.ObjectType):
        list_articles = graphene.List(GraphAnnotatedName)

        def resolve_list_articles(self, info):
            return []

    schema = graphene.Schema(query=Query, types=[GraphAnnotatedName])
    snapshot.assert_match(str(schema))
