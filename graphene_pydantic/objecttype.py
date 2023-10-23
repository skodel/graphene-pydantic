import typing as T

import graphene
import pydantic
from graphene.types.objecttype import ObjectTypeOptions
from graphene.types.utils import yank_fields_from_attrs
from graphql import GraphQLResolveInfo

from .converters import convert_pydantic_field
from .inputobjecttype import PydanticInputObjectType
from .registry import Placeholder, Registry, get_global_registry


class PydanticObjectTypeOptions(ObjectTypeOptions):
    # TODO:
    # It's not clear what purpose this serves within Graphene, or whether
    # it'd be meaningful to construct this from the pydantic.Config associated
    # with a given model, so skipping it for now.
    pass


def construct_fields(
        obj_type: T.Type["PydanticObjectType"],
        model: T.Type[pydantic.BaseModel],
        registry: Registry,
        only_fields: T.Tuple[str, ...],
        exclude_fields: T.Tuple[str, ...],
) -> T.Dict[str, graphene.Field]:
    """
    Construct all the fields for a PydanticObjectType.

    NOTE: Currently simply fetches all the attributes from the Pydantic model
    `__fields__`. In the future we hope to implement field-level overrides that
    we'll have to merge in.
    """
    excluded: T.Tuple[str, ...] = ()
    if exclude_fields:
        excluded = exclude_fields
    elif only_fields:
        excluded = tuple(k for k in model.__fields__ if k not in only_fields)

    fields_to_convert = (
        (k, v) for k, v in model.__fields__.items() if k not in excluded
    )

    fields = {}
    for name, field in fields_to_convert:
        converted = convert_pydantic_field(
            field, registry, parent_type=obj_type, model=model
        )
        registry.register_object_field(obj_type, name, field)
        fields[name] = converted
    return fields


# TODO: implement an OverrideField of some kind


class PydanticObjectType(graphene.ObjectType):
    """Graphene ObjectType that knows how to map itself to a Pydantic model defined in its nested `Meta` class."""

    @classmethod
    def __init_subclass_with_meta__(
            cls,
            model: type = None,
            registry: Registry = None,
            skip_registry: bool = False,
            only_fields: T.Tuple[str, ...] = (),
            exclude_fields: T.Tuple[str, ...] = (),
            interfaces=(),
            id=None,
            _meta=None,
            **options,
    ):
        assert model and issubclass(
            model, pydantic.BaseModel
        ), f'You need to pass a valid Pydantic model in {cls.__name__}.Meta, received "{model}"'

        assert isinstance(
            registry, (Registry, None.__class__)
        ), f'The attribute registry in {cls.__name__} needs to be an instance of Registry, received "{registry}".'

        if only_fields and exclude_fields:
            raise ValueError(
                "The options 'only_fields' and 'exclude_fields' cannot be both set on the same type."
            )

        if not registry:
            registry = get_global_registry(PydanticObjectType)

        if not cls.__doc__:
            cls.__doc__ = model.__doc__

        pydantic_fields = yank_fields_from_attrs(
            construct_fields(
                obj_type=cls,
                model=model,
                registry=registry,
                only_fields=only_fields,
                exclude_fields=exclude_fields,
            ),
            _as=graphene.Field,
            sort=False,
        )

        if not _meta:
            _meta = PydanticObjectTypeOptions(cls)

        _meta.model = model
        _meta.registry = registry

        if _meta.fields:
            _meta.fields.update(pydantic_fields)
        else:
            _meta.fields = pydantic_fields

        _meta.id = id or "id"

        # TODO: We don't currently do anything with interfaces, and it would
        # be great to handle them as well. Some options include:
        # - throwing an error if they're present, because we _can't_ handle them
        # - finding a model class with that name and generating an interface
        #   from it
        # - using the nearest common ancestor of multiple types in a Union

        super().__init_subclass_with_meta__(
            _meta=_meta, interfaces=interfaces, **options
        )

        if not skip_registry:
            registry.register(cls)

    @classmethod
    def resolve_placeholders(cls):
        """
        If this class has any placeholders in the registry (e.g. classes that
        weren't resolvable when the class was created, perhaps due to the
        PydanticObjectType wrapper not existing yet), resolve them as far as
        possible.
        """
        meta = cls._meta
        fields_to_update = {}
        for name, field in meta.fields.items():
            target_type = field._type
            if hasattr(target_type, "_of_type"):
                target_type = target_type._of_type
            if isinstance(target_type, Placeholder):
                pydantic_field = meta.model.__fields__[name]
                graphene_field = convert_pydantic_field(
                    pydantic_field,
                    meta.registry,
                    parent_type=cls,
                    model=target_type.model,
                )
                fields_to_update[name] = graphene_field
                meta.registry.register_object_field(cls, name, pydantic_field)
        # update the graphene side of things
        meta.fields.update(fields_to_update)

    @classmethod
    def is_type_of(cls, root, _: GraphQLResolveInfo) -> bool:
        if isinstance(root, PydanticInputObjectType):
            return type(root._meta.model) is type(cls._meta.model)
        return isinstance(root, cls._meta.model)
