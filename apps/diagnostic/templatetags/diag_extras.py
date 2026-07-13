"""Custom template filters for the smart diagnostic quiz."""
from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """Get a value from a dict by key: {{ answers|dict_get:q.name }}"""
    if isinstance(d, dict):
        return d.get(key, '')
    return ''


@register.filter
def is_checked(answers, key_value):
    """
    Check if a value is in the answers dict for a given field.
    Usage: {% if answers|is_checked:"fieldname:value" %}
    """
    if ':' not in key_value:
        return False
    key, value = key_value.split(':', 1)
    if isinstance(answers, dict):
        v = answers.get(key, '')
        if isinstance(v, list):
            return value in v
        return v == value
    return False


@register.filter
def in_answers(opt_value, answers_value):
    """Check if opt_value is in a saved multi-select answer (list or string).
    Usage: {% if opt.value|in_answers:saved %}"""
    if isinstance(answers_value, list):
        return opt_value in answers_value
    if isinstance(answers_value, str):
        return answers_value == opt_value
    return False
