from django import template
from django.utils import timezone


register = template.Library()


@register.filter
def money(value):
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


@register.filter
def col_time(value):
    if not value:
        return ""
    return timezone.localtime(value).strftime("%d/%m/%Y %H:%M")
