from django import template
from urllib.parse import urlparse

register = template.Library()

@register.filter(name="base_path")
def base_path(url):
    return urlparse(url).path.split('/')[1]

@register.filter(name='addclass_to_label')
def addclass_to_label(value, arg):
    return value.label_tag(attrs={'class': arg})

@register.filter(name='addclass_to_input')
def addclass_to_input(field, css_class):
    attrs = field.field.widget.attrs
    original_class = attrs.get('class', '')
    attrs.update({'class': f'{original_class} {css_class}'.strip()})
    return field

@register.filter(name='add_autofocus')
def add_autofocus(field):
    if 'autofocus' in field.field.widget.attrs:
        return field
    else:
        field.field.widget.attrs.update({'autofocus': ''})
        return field