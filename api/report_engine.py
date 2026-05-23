import operator
from datetime import datetime
from functools import reduce

from django.db.models import Count, Sum, Avg, Min, Max, Q, DecimalField, F
from django.db.models.functions import Coalesce

from api.models import *
from api.pagination import MainPagination
from api.query_builder import QueryBuilder

AGG_MAP = {
    "count": Count,
    "sum": Sum,
    "avg": Avg,
    "min": Min,
    "max": Max,
}

FUNC_MAP = {
    "sum": Sum,
    "count": Count,
    "f": F,
}

annotate = {
    "field": "financed",
    "func": "sum",
    "annotated_field": "constructionfinancing__amount",
    "filters": [{'field': 'field', 'value': 'value'}],
    "default": 0,
}

def _functionCombine(obj: list, op = None):
    if obj is None or len(obj) == 0:
        return None
    conditions = list(map(lambda x: Q(**{x['field']: x['value']}), obj))
    oper = operator.and_
    if op == 'div':
        oper = operator.truediv

    return reduce(oper, conditions)

def _operationCombine(operation):
    if operation['func'] == 'f':
        return FUNC_MAP[operation['func']](operation['value'])
    else:
        return FUNC_MAP[operation['func']](operation['value'], filter=_functionCombine(operation.get('filters', [])))

def _operationsCombine(obj: list, op = None):
    if obj is None or len(obj) == 0:
        return None
    obj.sort(key=lambda x: x.get('order', 0))
    operations = list(map(_operationCombine, obj))
    oper = operator.and_
    if op == 'div':
        oper = operator.truediv

    return reduce(oper, operations)

def _annotateToMap(obj: list):
    annotations = {}
    for o in obj:
        operations = _operationsCombine(o.get('operations', []), op=o.get('operator', None))
        if o['default'] is not None:
            annotations[o['field']] = Coalesce(operations, o['default'], output_field=DecimalField())
        else:
            annotations[o['field']] = operations
    return annotations


class ReportQueryEngine:
    ENTITY_MAP = {
        "objects": ConstructionObject,
        "issues": Issue,
        "reviews": Review,
        "public_issues": PublicIssue,
        "assignments": Assignment,
    }

    OWNER_FILTER = {
        'objects': 'workplace__clinic',
        'warehouses': 'shops',
        'kpilog': 'worker__shop',
        'clients': 'shop',
        'sales': 'shift__shop',
        'services': 'shop',
    }

    @classmethod
    def base_queryset(cls, entity: str, user, filters, annotations, period, period_by='created_at', diff=False):
        model = cls.ENTITY_MAP[entity]
        queryset = model.objects.all()
        if annotations:
            mapped_annotations = _annotateToMap(annotations)
            queryset = queryset.annotate(**mapped_annotations)

        if filters:
            queryset = queryset.filter(**filters)

        if period:
            period_filter = {f'{period_by}__range': (period['from'], period['to'])}
            diff_period = {f'{period_by}__range': ((period['from'] is datetime), period['from'])}

            queryset = queryset.filter(
                **period_filter
            )


        return queryset


    @staticmethod
    def process_kpi(block, qs):
        agg = block["aggregation"]
        func = AGG_MAP[agg["function"]]

        if agg["function"] == "count":
            value = qs.count()
        else:
            value = qs.aggregate(
                value=Coalesce(func(agg["field"]), 0, output_field=DecimalField())
            )["value"]

        return value

    @staticmethod
    def process_chart(block, qs):
        agg = block["aggregation"]

        func = AGG_MAP[agg["function"]]
        agg_field = agg.get('field', 'id')
        group = agg["group_by"]
        annotates = {
            "value": Coalesce(func(agg_field), 0, output_field=DecimalField())
        }

        data = (
            qs.values(group)
            .annotate(**annotates)
            .order_by(group)
        )

        return list(data)

    @staticmethod
    def process_table(block, qs, request):
        paginator = MainPagination()
        page = paginator.paginate_queryset(qs.values(*block['fields']), request)

        return {
            "rows": list(page),
            "pagination": {
                "count": paginator.page.paginator.count,
                "page": paginator.page.number,
                "page_size": paginator.page.paginator.per_page,
            },
        }