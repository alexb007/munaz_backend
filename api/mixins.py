from django.db.models import QuerySet
from django.db import models

from rest_framework.serializers import BaseSerializer, ListSerializer, Serializer

class ReadWriteSerializerMixin:
    """
    Mixin to use different serializers for read vs. write operations.
    """
    read_serializer_class = None
    write_serializer_class = None

    def get_serializer_class(self):
        # Use the write serializer for create, update, and partial_update
        if self.action in ["create", "update", "partial_update"]:
            if self.write_serializer_class:
                return self.write_serializer_class
        
        # Fallback to read serializer (for list, retrieve, or others)
        if self.read_serializer_class:
            return self.read_serializer_class
            
        return super().get_serializer_class()
    


def _get_serializer_fields(serializer_class) -> dict:
    """
    Instantiate the serializer without arguments and return its fields dict.
    Guards against serializers that require constructor arguments.
    """
    try:
        return serializer_class().fields
    except Exception:
        return {}


def _get_model_field(meta, field_name: str):
    """Return the model field object for field_name, or None if not found."""
    try:
        return meta.get_field(field_name)
    except Exception:
        return None


def _is_single_valued_relation(field) -> bool:
    return isinstance(
        field,
        (models.ForeignKey, models.OneToOneField, models.OneToOneRel),
    )


def _is_multi_valued(field) -> bool:
    return isinstance(
        field,
        (
            models.ManyToManyField,
            models.ManyToManyRel,
            models.ManyToOneRel,  # reverse FK
        ),
    )


def _resolve_nested_model(
    parent_meta, field_name: str, serializer_instance
) -> "type[models.Model] | None":
    """
    Try to figure out which Django model a nested serializer targets.

    Strategy (in order):
    1. serializer.Meta.model
    2. Related model resolved via parent model's field
    """
    meta = getattr(type(serializer_instance), "Meta", None)
    if meta is not None:
        model = getattr(meta, "model", None)
        if model is not None:
            return model

    try:
        rel_field = parent_meta.get_field(field_name)
        if hasattr(rel_field, "related_model") and rel_field.related_model:
            return rel_field.related_model
        if hasattr(rel_field, "field") and hasattr(rel_field.field, "model"):
            return rel_field.field.model
    except Exception:
        pass

    return None


def _collect_relations(
    serializer_class,
    model: "type[models.Model]",
    prefix: str = "",
    visited: set | None = None,
) -> tuple[list[str], list[str]]:
    """
    Recursively walk a serializer class + its model to collect field paths
    that should be passed to select_related / prefetch_related.

    Returns
    -------
    select_related_paths : list[str]
        ForeignKey / OneToOneField paths  (single-valued -> JOIN is cheap).
    prefetch_related_paths : list[str]
        ManyToManyField / reverse-FK paths  (multi-valued -> separate query).
    """
    if visited is None:
        visited = set()

    cycle_key = (id(serializer_class), id(model), prefix)
    if cycle_key in visited:
        return [], []
    visited.add(cycle_key)

    select_paths: list[str] = []
    prefetch_paths: list[str] = []

    try:
        model_meta = model._meta
    except AttributeError:
        return [], []

    fields = _get_serializer_fields(serializer_class)

    for field_name, field_obj in fields.items():
        actual_field = field_obj
        if isinstance(field_obj, ListSerializer):
            actual_field = field_obj.child

        orm_path = f"{prefix}__{field_name}" if prefix else field_name

        if isinstance(actual_field, Serializer):
            nested_serializer_class = type(actual_field)
            nested_model = _resolve_nested_model(model_meta, field_name, actual_field)

            if nested_model is not None:
                rel_field = _get_model_field(model_meta, field_name)
                if rel_field is not None and _is_multi_valued(rel_field):
                    prefetch_paths.append(orm_path)
                    sub_select, sub_prefetch = _collect_relations(
                        nested_serializer_class, nested_model,
                        prefix=orm_path, visited=visited,
                    )
                    # nested selects under a prefetch become prefetches too
                    prefetch_paths.extend(sub_select)
                    prefetch_paths.extend(sub_prefetch)
                else:
                    select_paths.append(orm_path)
                    sub_select, sub_prefetch = _collect_relations(
                        nested_serializer_class, nested_model,
                        prefix=orm_path, visited=visited,
                    )
                    select_paths.extend(sub_select)
                    prefetch_paths.extend(sub_prefetch)
            else:
                prefetch_paths.append(orm_path)
        else:
            rel_field = _get_model_field(model_meta, field_name)
            if rel_field is None:
                continue
            if _is_multi_valued(rel_field):
                prefetch_paths.append(orm_path)
            elif _is_single_valued_relation(rel_field):
                select_paths.append(orm_path)

    return select_paths, prefetch_paths


class AutoRelatedMixin:
    """
    A ModelViewSet mixin that automatically applies select_related and
    prefetch_related to the viewset's queryset based on the fields
    declared on the serializer.

    How it works
    ------------
    On every get_queryset() call the mixin inspects the serializer class
    returned by get_serializer_class() and the model declared on the
    viewset's queryset.  It recursively walks nested serializer fields and
    maps them to Django model relations, then applies the appropriate ORM
    optimisation:

    * ForeignKey / OneToOneField  -> select_related  (single JOIN)
    * ManyToManyField / reverse-FK -> prefetch_related (separate query)
    * Nested serializer under M2M/reverse-FK -> prefetch_related
      (deeper nesting also becomes a prefetch to avoid cartesian products)

    Class-level overrides
    ---------------------
    extra_select_related : list[str]
        Additional paths appended to the auto-detected select_related list.
        Useful for relations not represented in the serializer but accessed
        in list/retrieve logic.

    extra_prefetch_related : list[str]
        Same, for prefetch_related.

    exclude_related : set[str]
        ORM path strings removed from both auto-detected lists
        (e.g. if a field causes issues or you handle it manually).

    disable_auto_related : bool
        Set to True to skip automatic detection entirely and rely only on
        the extra_* lists (or your own get_queryset override).

    Examples
    --------
    # Fully automatic:
    class OrderViewSet(AutoRelatedMixin, ModelViewSet):
        queryset = Order.objects.all()
        serializer_class = OrderSerializer

    # Automatic + manual additions:
    class InvoiceViewSet(AutoRelatedMixin, ModelViewSet):
        queryset = Invoice.objects.all()
        serializer_class = InvoiceSerializer
        extra_select_related = ["created_by"]
        extra_prefetch_related = ["attachments"]

    # Exclude a path the auto-detector picks up but you handle elsewhere:
    class ProductViewSet(AutoRelatedMixin, ModelViewSet):
        queryset = Product.objects.all()
        serializer_class = ProductSerializer
        exclude_related = {"category__parent"}

    # Combine with ShopFilterMixin:
    class SaleViewSet(ShopFilterMixin, AutoRelatedMixin, ModelViewSet):
        queryset = Sale.objects.all()
        serializer_class = SaleSerializer
        shop_field = "shop"
    """

    extra_select_related: list[str] = []
    extra_prefetch_related: list[str] = []
    exclude_related: set[str] = set()
    disable_auto_related: bool = False

    def _get_queryset_model(self, qs: QuerySet) -> "type[models.Model] | None":
        try:
            return qs.model
        except AttributeError:
            return None

    def _build_related_paths(
        self, serializer_class, model: "type[models.Model]"
    ) -> tuple[list[str], list[str]]:
        """
        Combine auto-detected paths with manual extras and apply exclusions.
        Returns (select_related_paths, prefetch_related_paths).
        """
        if self.disable_auto_related:
            auto_select, auto_prefetch = [], []
        else:
            auto_select, auto_prefetch = _collect_relations(serializer_class, model)

        # Merge, preserving order, removing duplicates
        select_paths = list(dict.fromkeys(auto_select + list(self.extra_select_related)))
        prefetch_paths = list(dict.fromkeys(auto_prefetch + list(self.extra_prefetch_related)))

        if self.exclude_related:
            select_paths = [p for p in select_paths if p not in self.exclude_related]
            prefetch_paths = [p for p in prefetch_paths if p not in self.exclude_related]

        return select_paths, prefetch_paths

    def get_queryset(self) -> QuerySet:
        qs: QuerySet = super().get_queryset()
        model = self._get_queryset_model(qs)
        if model is None:
            return qs

        try:
            serializer_class = self.get_serializer_class()
        except Exception:
            return qs

        select_paths, prefetch_paths = self._build_related_paths(serializer_class, model)

        if select_paths:
            qs = qs.select_related(*select_paths)
        if prefetch_paths:
            qs = qs.prefetch_related(*prefetch_paths)
        return qs