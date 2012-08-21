from django import template
from django.template import loader
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.conf import settings
from leaves.models import Leaf
from leaves.utils import get_site
from leaves.middleware import request_context

register = template.Library()

@register.assignment_tag
def leaf_stream(*types, **kwargs):
    site = kwargs.get('site', get_site())
    user = kwargs.get('user', getattr(request_context, 'user', None))
    author = kwargs.get('author', None)
    tag = kwargs.get('tag', None)
    num = int(kwargs.get('num', site.preferences.stream_count))
    qs = Leaf.objects.stream(site=site, user=user)
    if types:
        models = [t.lower() for t in types]
        qs = qs.filter(leaf_type__model__in=models)
    if author:
        qs = qs.filter(author__username__iexact=author)
    if tag:
        qs = qs.filter(tags__slug__iexact=tag)
    return [leaf.resolved for leaf in qs[:num]]

@register.simple_tag
def leaf_summary(leaf):
    return loader.render_to_string(leaf.get_summary_templates(), {
        leaf.leaf_type.model: leaf.resolved,
    })
