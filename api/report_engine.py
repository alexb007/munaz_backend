from django.db.models import Count, Sum, Avg, Min, Max, Q, DecimalField
from django.db.models.functions import Coalesce

from api.models import *
from api.pagination import MainPagination

AGG_MAP = {
    "count": Count,
    "sum": Sum,
    "avg": Avg,
    "min": Min,
    "max": Max,
}


class ReportQueryEngine:
    ENTITY_MAP = {
        "objects": ConstructionObject,
        "issues": Issue,
        "reviews": Review,
        "public_issues": PublicIssue,
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
    def base_queryset(cls, entity: str, user, filters, period, period_by='created_at', diff=False):
        model = cls.ENTITY_MAP[entity]
        # qs = model.objects.filter(**{cls.SHOP_FILTER[entity]: shop})

        if filters:
            qs = qs.filter(**filters)

        if period:
            period_filter = {f'{period_by}__range': (period['from'], period['to'])}
            # diff_period = {f'{period_by}__range': ((period['from'] is datetime), period['from'])}

            qs = qs.filter(
                **period_filter
            )


        return qs


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