from django import template

register = template.Library()


@register.filter(name='abs')
def absolute_value(value):
    """
    Returns the absolute value of a number.
    Usage: {{ some_number|abs }}
    """
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value


