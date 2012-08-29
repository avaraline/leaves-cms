from django import template
from django.template import loader
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.conf import settings
from leaves.models import Leaf, Page
from leaves.utils import get_site, get_user
from leaves.comments import make_comment_form

register = template.Library()

@register.simple_tag
def leaf_summary(leaf):
    return loader.render_to_string(leaf.get_summary_templates(), {
        leaf.leaf_type.model: leaf.resolved,
    })

@register.assignment_tag
def get_leaves(*types, **kwargs):
    site = kwargs.get('site', get_site())
    user = kwargs.get('user', get_user())
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

@register.assignment_tag
def get_navigation_pages(*args, **kwargs):
    site = kwargs.get('site', get_site())
    user = kwargs.get('user', get_user())
    return Page.objects.published(site=site, user=user).filter(show_in_navigation=True)

@register.assignment_tag
def get_comment_form(leaf, **kwargs):
    data = kwargs.get('data', None)
    site = kwargs.get('site', get_site())
    user = kwargs.get('user', get_user())
    return make_comment_form(leaf, data=data, site=site, user=user)
