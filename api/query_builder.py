from django.db.models import Q, Count, Sum, Avg, Min, Max, StdDev, Variance
from django.core.exceptions import ValidationError

# Map JSON operator names to Django ORM lookups
OPERATOR_MAP = {
    "exact": "exact",
    "iexact": "iexact",
    "contains": "contains",
    "icontains": "icontains",
    "gt": "gt",
    "gte": "gte",
    "lt": "lt",
    "lte": "lte",
    "in": "in",
    "isnull": "isnull",
    "startswith": "startswith",
    "istartswith": "istartswith",
    "endswith": "endswith",
    "iendswith": "iendswith",
    "range": "range",
    # add more as needed
}

# Map JSON function names to Django aggregation classes
AGGREGATION_MAP = {
    "Count": Count,
    "Sum": Sum,
    "Avg": Avg,
    "Min": Min,
    "Max": Max,
    "StdDev": StdDev,
    "Variance": Variance,
}

class QueryBuilder:
    def __init__(self, model):
        self.model = model

    def build_filters(self, filters_data):
        """Recursively construct a Q object from the filters JSON."""
        if not filters_data:
            return Q()

        if "connector" in filters_data:
            connector = filters_data["connector"].upper()
            if connector not in ("AND", "OR"):
                raise ValidationError("Connector must be AND or OR")
            child_qs = [self.build_filters(cond) for cond in filters_data["conditions"]]
            if connector == "AND":
                q = Q()
                for child in child_qs:
                    q &= child
                return q
            else:  # OR
                q = Q()
                for child in child_qs:
                    q |= child
                return q

        # Leaf condition
        field = filters_data.get("field")
        operator = filters_data.get("operator")
        value = filters_data.get("value")

        if not field or not operator:
            raise ValidationError("Leaf filter requires field and operator")

        # if self.allowed_fields is not None and field not in self.allowed_fields:
        #     raise ValidationError(f"Field '{field}' is not allowed for filtering")

        django_lookup = OPERATOR_MAP.get(operator)
        if not django_lookup:
            raise ValidationError(f"Unsupported operator: {operator}")

        # Special handling for `isnull` (value should be boolean)
        if operator == "isnull":
            value = value in (True, "true", "True", 1, "1")

        # Construct the lookup string: e.g., "price__gte"
        lookup = f"{field}__{django_lookup}"
        return Q(**{lookup: value})

    def build_annotations(self, annotations_data):
        """Convert annotation definitions into Django annotate() kwargs."""
        if not annotations_data:
            return {}

        annotations = {}
        for alias, defn in annotations_data.items():
            # if self.allowed_annotations is not None and alias not in self.allowed_annotations:
            #     raise ValidationError(f"Annotation '{alias}' is not allowed")
            func_name = defn.get("function")
            field_path = defn.get("field")
            filter_def = defn.get("filter")

            agg_class = AGGREGATION_MAP.get(func_name)
            if not agg_class:
                raise ValidationError(f"Unsupported aggregation function: {func_name}")

            # Basic aggregation without extra filter
            if not filter_def:
                annotations[alias] = agg_class(field_path)
                continue

            # Aggregation with a built-in filter (e.g., Sum(…, filter=Q(…)))
            # if self.allowed_fields is not None and filter_def["field"] not in self.allowed_fields:
            #     raise ValidationError(f"Filter field in annotation not allowed")
            filter_q = self.build_filters(filter_def)
            annotations[alias] = agg_class(field_path, filter=filter_q)

        return annotations

    def apply_to_queryset(self, queryset, annotations_json):
        """Parse JSON and return queryset with filters and annotations applied."""
        # print(json_data)
        # filters_json = json_data.get("filters")
        # annotations_json = json_data.get("annotations")

        # q_obj = self.build_filters(filters_json) if filters_json else Q()
        annotations = self.build_annotations(annotations_json) if annotations_json else {}

        # queryset = queryset.filter(q_obj)
        if annotations:
            queryset = queryset.annotate(**annotations)
        return queryset