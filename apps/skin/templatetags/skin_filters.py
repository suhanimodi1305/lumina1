from django import template

register = template.Library()


@register.filter(name='replace')
def replace_filter(value, arg):
    """
    Replace occurrences of a substring in a string.
    Usage: {{ value|replace:"old:new" }}  or  {{ value|replace:"old":" " }}
    Supports both "old:new" colon syntax and passing a single char to replace with space.
    """
    if ':' in str(arg):
        old, new = str(arg).split(':', 1)
    else:
        old = str(arg)
        new = ' '
    return str(value).replace(old, new)
