from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def rupiah(value):
    if value is None:
        return "0"

    try:
        value = int(Decimal(value))
    except Exception:
        return "0"

    return "{:,}".format(value).replace(",", ".")