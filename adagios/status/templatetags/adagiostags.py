import math
from datetime import datetime, timedelta
from django import template
from django.utils.timesince import timesince
from django.utils.translation import ugettext as _

register = template.Library()

@register.filter("timestamp")
def timestamp(value):
    try:
        return datetime.fromtimestamp(value)
    except AttributeError:
        return ''

@register.filter("duration")
def duration(value):
    """ Used as a filter, returns a human-readable duration.
    'value' must be in seconds.
    """
    zero = datetime.min
    return timesince(zero, zero + timedelta(0, value))
