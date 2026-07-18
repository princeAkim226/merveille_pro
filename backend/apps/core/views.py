from datetime import datetime, timedelta
from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import ActionLog, CompanySettings
from apps.core.serializers import CompanySettingsSerializer
from apps.users.permissions import IsAdmin
from apps.finance.models import Expense
from apps.products.models import Product
from apps.sales.models import Sale, SaleItem
from apps.shops.utils import resolve_shop_scope


def _parse_date(value):
  return datetime.strptime(value, '%Y-%m-%d').date()


def _resolve_period(request):
  """Résout la période depuis ?period=today|week|month|year|custom&from=&to="""
  today = timezone.now().date()
  period = request.query_params.get('period', 'month')
  from_param = request.query_params.get('from')
  to_param = request.query_params.get('to')

  if period == 'today':
    start, end = today, today
    label = "Aujourd'hui"
  elif period == 'week':
    start = today - timedelta(days=today.weekday())
    end = today
    label = 'Cette semaine'
  elif period == 'year':
    start = today.replace(month=1, day=1)
    end = today
    label = 'Cette année'
  elif period == 'custom' and from_param and to_param:
    start = _parse_date(from_param)
    end = _parse_date(to_param)
    if start > end:
      start, end = end, start
    label = f'{start.strftime("%d/%m/%Y")} — {end.strftime("%d/%m/%Y")}'
  else:
    period = 'month'
    start = today.replace(day=1)
    end = today
    label = 'Ce mois'

  return period, start, end, label


def _shop_stats(shops_qs, period_start, period_end, today):
  sales_period = Sale.objects.filter(
    shop__in=shops_qs,
    date__date__gte=period_start,
    date__date__lte=period_end,
  )
  sales_today = Sale.objects.filter(shop__in=shops_qs, date__date=today)

  revenue_period = sales_period.aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
  revenue_today = sales_today.aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
  expenses_period = Expense.objects.filter(
    shop__in=shops_qs,
    date__gte=period_start,
    date__lte=period_end,
  ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

  profit_items = SaleItem.objects.filter(
    sale__shop__in=shops_qs,
    sale__date__date__gte=period_start,
    sale__date__date__lte=period_end,
  ).select_related('product')
  gross_profit = sum(item.profit for item in profit_items)
  net_profit = gross_profit - expenses_period

  low_stock = Product.objects.filter(
    is_active=True,
    shop__in=shops_qs,
    stock_quantity__lte=models.F('alert_threshold'),
  ).count()
  total_products = Product.objects.filter(is_active=True, shop__in=shops_qs).count()
  total_sales_period = sales_period.count()

  recent_sales = Sale.objects.filter(shop__in=shops_qs).select_related('user', 'shop').order_by('-date')[:5]
  recent_sales_data = [
    {
      'id': s.pk,
      'date': s.date.isoformat(),
      'total_amount': str(s.total_amount),
      'user': s.user.username,
      'shop': s.shop.name,
    }
    for s in recent_sales
  ]

  return {
    'revenue_today': str(revenue_today),
    'revenue_period': str(revenue_period),
    'revenue_month': str(revenue_period),
    'expenses_period': str(expenses_period),
    'expenses_month': str(expenses_period),
    'gross_profit_period': str(gross_profit),
    'gross_profit_month': str(gross_profit),
    'net_profit_period': str(net_profit),
    'net_profit_month': str(net_profit),
    'low_stock_count': low_stock,
    'total_products': total_products,
    'total_sales_period': total_sales_period,
    'total_sales_month': total_sales_period,
    'recent_sales': recent_sales_data,
  }


class DashboardView(APIView):
  """GET /api/dashboard/?shop=all|id&period=today|week|month|year|custom&from=&to="""
  permission_classes = (IsAuthenticated,)

  def get(self, request):
    today = timezone.now().date()
    period, period_start, period_end, period_label = _resolve_period(request)
    shops, single_shop = resolve_shop_scope(request.user, request.query_params.get('shop'))

    stats = _shop_stats(shops, period_start, period_end, today)

    breakdown = []
    if single_shop is None:
      for shop in shops:
        shop_stats = _shop_stats(shops.filter(pk=shop.pk), period_start, period_end, today)
        breakdown.append({
          'shop_id': shop.pk,
          'shop_name': shop.name,
          'shop_code': shop.code,
          **shop_stats,
        })

    return Response({
      **stats,
      'period': period,
      'period_label': period_label,
      'period_from': period_start.isoformat(),
      'period_to': period_end.isoformat(),
      'scope': 'single' if single_shop else 'all',
      'shop_id': single_shop.pk if single_shop else None,
      'shop_name': single_shop.name if single_shop else 'Toutes les boutiques',
      'shops_breakdown': breakdown,
    })


class CompanySettingsView(APIView):
  """GET /api/settings/ — lecture publique. PUT/PATCH — admin uniquement."""

  def get_permissions(self):
    if self.request.method == 'GET':
      return [AllowAny()]
    return [IsAdmin()]

  def get(self, request):
    settings_obj = CompanySettings.get_solo()
    return Response(CompanySettingsSerializer(settings_obj).data)

  def put(self, request):
    return self._update(request, partial=False)

  def patch(self, request):
    return self._update(request, partial=True)

  def _update(self, request, partial):
    settings_obj = CompanySettings.get_solo()
    serializer = CompanySettingsSerializer(settings_obj, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


class ActionLogListView(APIView):
  permission_classes = (IsAuthenticated,)

  def get(self, request):
    if not request.user.is_admin:
      logs = ActionLog.objects.filter(user=request.user)
    else:
      logs = ActionLog.objects.all()

    logs = logs.select_related('user').order_by('-created_at')[:50]
    data = [
      {
        'id': log.pk,
        'user': log.user.username if log.user else '',
        'action': log.action,
        'details': log.details,
        'created_at': log.created_at.isoformat(),
      }
      for log in logs
    ]
    return Response(data)
