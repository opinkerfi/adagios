import math
from datetime import datetime
from django import template
from django.utils.translation import ugettext as _

register = template.Library()

@register.filter("timestamp")
def timestamp(value):
    try:
        return datetime.fromtimestamp(value)
    except AttributeError:
        return ''

# Register filter
@register.filter("duration")
def duration(value, arg=''):
    """
    Given 'value' an amount of seconds, converts this in a friendly way.
    Provides support for Django's built-in internationalization.
    
    Example: 15615165|duration|"long"
              -> 180 days, 17 hours, 32 minutes and 45 seconds
    
    Usage in a template: {{ your_var|duration|["long"] }}
    """
    def plural_form((singular, plural), value):
        if value >= 2:
            return plural
        else:
            return singular
    
    def cr(arg, short, short_plural, long_, long_plural, seconds):
        if arg == 'long':
            strs = (long_, long_plural)
        else:
            strs = (short, short_plural)

        return {
            'strs':    strs,
            'short':   (short, short_plural),
            'long':    (long_, long_plural),
            'seconds': seconds,
            'value':   None,
            }
    
    secs = int(value)
    
    if secs <= 0:
        return _('No duration')
    
    day_unit  = cr(arg, _('day'), _('days'), _('day'),    _('days'),    86400)
    hour_unit = cr(arg, _('hr'),  _('hrs'),  _('hour'),   _('hours'),   3600)
    min_unit  = cr(arg, _('min'), _('mins'), _('minute'), _('minutes'), 60)
    sec_unit  = cr(arg, _('sec'), _('secs'), _('second'), _('seconds'), 1)
    
    times = [day_unit, hour_unit, min_unit, sec_unit]
    
    # Translators: this is a separator (followed by a space, in english typo)
    split = _(', ')
    last_split = _('and')
    
    result = []
    
    for t in times:
        t['value'] = int(math.floor(secs / t['seconds']))
        secs -= t['value'] * t['seconds']
        if t['value'] > 0:
            result.append('%d %s' % (t['value'], plural_form(t['strs'], t['value'])))
    
    
    if len(result) == 1:
        final = result[0]
    else:
        last = (' %s ' % last_split).join([result[-2], result[-1]])
        final = split.join(result[:-2] + [last])
    
    return final
