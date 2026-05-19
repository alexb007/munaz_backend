# filters.py
# Django-filter / DRF FilterSet that consumes the exact URL params
# produced by buildQueryParams() on the frontend.
#
# Install: pip install django-filter
# Wire up:  REST_FRAMEWORK = { 'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'] }
#
# ── Single-group (flat) format ─────────────────────────────────────────────────
#   GET /api/posts/?title__icontains=foo&status__in=draft,published&view_count__gte=100
#
# ── Multi-group format ─────────────────────────────────────────────────────────
#   GET /api/posts/?filter_logic=OR
#     &g0_logic=AND&g0__title__icontains=foo&g0__status__in=draft
#     &g1_logic=AND&g1__view_count__gte=100
#
# ── Negation sentinel ──────────────────────────────────────────────────────────
#   title__icontains=foo&title__icontains__exclude=1  →  .exclude(title__icontains="foo")

import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from api.models import ConstructionObject


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _parse_in_value(raw: str) -> list:
    """Split comma-separated __in value: "draft,published" → ["draft", "published"]"""
    return [v.strip() for v in raw.split(",") if v.strip()]


def _get_lookup_pairs(data: dict, prefix: str = "") -> list[tuple[str, str]]:
    """
    Extract (lookup_expr, value) tuples from a query-dict, stripping `prefix`.
    Excludes meta keys (filter_logic, g{n}_logic, page, ordering …) and
    __exclude sentinels.
    """
    META = {"filter_logic", "page", "limit", "sort", "dir", "ordering", "search"}
    pairs = []
    for key, value in data.items():
        if key in META:
            continue
        if key.endswith("__exclude"):
            continue
        if prefix and not key.startswith(prefix):
            continue
        stripped = key[len(prefix):]
        pairs.append((stripped, value))
    return pairs


def _build_q(lookup_expr: str, value: str, exclude: bool) -> Q:
    """Build a single Q object, handling __in, __isnull, and plain lookups."""
    if lookup_expr.endswith("__in"):
        q = Q(**{lookup_expr: _parse_in_value(value)})
    elif lookup_expr.endswith("__isnull"):
        q = Q(**{lookup_expr: value == "True"})
    else:
        q = Q(**{lookup_expr: value})
    return ~q if exclude else q


# ─── Universal group-aware filter backend ─────────────────────────────────────

class UniversalDRFFilterBackend(DjangoFilterBackend):
    """
    Drop-in replacement for DjangoFilterBackend that handles:
      - flat single-group params (standard FilterSet passthrough)
      - multi-group g{n}__ prefixed params with AND/OR logic
      - __exclude=1 negation sentinels
    """

    def filter_queryset(self, request, queryset, view):
        data = request.query_params

        # ── Multi-group mode ──────────────────────────────────────────────────
        if "filter_logic" in data:
            top_logic = data.get("filter_logic", "AND").upper()
            group_qs = []

            gi = 0
            while f"g{gi}_logic" in data:
                group_logic = data.get(f"g{gi}_logic", "AND").upper()
                prefix = f"g{gi}__"
                pairs = _get_lookup_pairs(data, prefix=prefix)

                rule_qs = []
                for lookup_expr, value in pairs:
                    sentinel_key = f"{prefix}{lookup_expr}__exclude"
                    exclude = data.get(sentinel_key) == "1"
                    rule_qs.append(_build_q(lookup_expr, value, exclude))

                if rule_qs:
                    if group_logic == "OR":
                        combined = rule_qs[0]
                        for q in rule_qs[1:]:
                            combined |= q
                    else:
                        combined = rule_qs[0]
                        for q in rule_qs[1:]:
                            combined &= q
                    group_qs.append(combined)

                gi += 1

            if group_qs:
                if top_logic == "OR":
                    final_q = group_qs[0]
                    for q in group_qs[1:]:
                        final_q |= q
                else:
                    final_q = group_qs[0]
                    for q in group_qs[1:]:
                        final_q &= q
                queryset = queryset.filter(final_q)

            return queryset

        # ── Flat single-group mode (standard FilterSet) ───────────────────────
        pairs = _get_lookup_pairs(data)
        for lookup_expr, value in pairs:
            sentinel_key = f"{lookup_expr}__exclude"
            exclude = data.get(sentinel_key) == "1"
            try:
                q = _build_q(lookup_expr, value, exclude)
                queryset = queryset.filter(q)
            except Exception:
                # Unknown lookup — skip gracefully
                continue

        return queryset


# ─── Example typed FilterSet (optional — for OpenAPI schema generation) ────────

class PostFilterSet(django_filters.FilterSet):
    """
    Typed FilterSet for the Post model.
    Defines the exact lookup expressions the frontend can send.
    Used alongside UniversalDRFFilterBackend for schema generation.
    """
    title__icontains    = django_filters.CharFilter(field_name="title",      lookup_expr="icontains")
    title__istartswith  = django_filters.CharFilter(field_name="title",      lookup_expr="istartswith")
    title__iendswith    = django_filters.CharFilter(field_name="title",      lookup_expr="iendswith")
    title               = django_filters.CharFilter(field_name="title",      lookup_expr="exact")
    title__isnull       = django_filters.BooleanFilter(field_name="title",   lookup_expr="isnull")

    status__in          = django_filters.BaseInFilter(field_name="status",   lookup_expr="in")
    status              = django_filters.CharFilter(field_name="status",      lookup_expr="exact")

    author_id__in       = django_filters.BaseInFilter(field_name="author_id", lookup_expr="in")
    author_id           = django_filters.NumberFilter(field_name="author_id", lookup_expr="exact")

    published_at__gte   = django_filters.DateFilter(field_name="published_at", lookup_expr="gte")
    published_at__lte   = django_filters.DateFilter(field_name="published_at", lookup_expr="lte")
    published_at__gt    = django_filters.DateFilter(field_name="published_at", lookup_expr="gt")
    published_at__lt    = django_filters.DateFilter(field_name="published_at", lookup_expr="lt")
    published_at        = django_filters.DateFilter(field_name="published_at", lookup_expr="exact")
    published_at__isnull = django_filters.BooleanFilter(field_name="published_at", lookup_expr="isnull")

    view_count__gt      = django_filters.NumberFilter(field_name="view_count", lookup_expr="gt")
    view_count__gte     = django_filters.NumberFilter(field_name="view_count", lookup_expr="gte")
    view_count__lt      = django_filters.NumberFilter(field_name="view_count", lookup_expr="lt")
    view_count__lte     = django_filters.NumberFilter(field_name="view_count", lookup_expr="lte")
    view_count          = django_filters.NumberFilter(field_name="view_count", lookup_expr="exact")

    featured            = django_filters.BooleanFilter(field_name="featured")
    tags__in            = django_filters.BaseInFilter(field_name="tags",     lookup_expr="in")

    class Meta:
        model  = None   # replace with your model: model = Post
        fields = []     # handled via explicit filters above


# ─── ViewSet wiring example ────────────────────────────────────────────────────
#
# class PostViewSet(viewsets.ModelViewSet):
#     queryset         = Post.objects.select_related("author").all()
#     serializer_class = PostSerializer
#     filter_backends  = [UniversalDRFFilterBackend]
#     filterset_class  = PostFilterSet   # optional: only needed for schema
#     ordering_fields  = ["created_at", "published_at", "view_count", "title"]
#     ordering         = ["-created_at"]


class ConstructionObjectFilter(django_filters.FilterSet):
    financed = django_filters.NumberFilter(field_name='financed', lookup_expr='exact')
    financed__gte = django_filters.NumberFilter(field_name='financed', lookup_expr='gte')
    financed__lte = django_filters.NumberFilter(field_name='financed', lookup_expr='lte')


    class Meta:
        model = ConstructionObject
        fields = {
            'deadline': ['range', 'gte', 'lte', 'exact'],
        }