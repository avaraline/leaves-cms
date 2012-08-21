from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, resolve
from django.contrib.sites.models import Site
from django.core.paginator import Paginator, InvalidPage
import itertools
import hashlib

class Homepage (object):
    """
    A class to encapsulate registering and rendering homepage views. Plugins may call the register method with a view
    name and label. Pages will be automatically listed as choices. This class is iterable so it can be used as an
    argument to a model field, e.g. CharField(choices=homepage)
    """

    def __init__(self):
        self.view_choices = []

    def register(self, view, label):
        self.view_choices.append((view, label))

    def render(self, request):
        parts = [str(p) for p in request.site.preferences.homepage.split(':')]
        if len(parts) > 1:
            url = reverse(parts[0], args=tuple(parts[1:]))
        else:
            url = reverse(parts[0])
        match = resolve(url)
        return match.func(request, *match.args, **match.kwargs)

    def __iter__(self):
        try:
            from leaves.models import Page
            page_choices = [('page-view:%s' % p.slug, 'Page: %s' % p.title) for p in Page.objects.all()]
        except:
            page_choices = []
        return itertools.chain(self.view_choices, page_choices)

homepage = Homepage()
del Homepage

def language_choices():
    for code, name in settings.LANGUAGES:
        yield code, _(name)

def default_language():
    available_codes = set(lang[0] for lang in settings.LANGUAGES)
    if settings.LANGUAGE_CODE in available_codes:
        return code
    lang = settings.LANGUAGE_CODE.split('-')[0]
    if lang in available_codes:
        return lang
    return 'en'

def attachment_path(instance, filename):
    return 'attachments/%s/%s/%s' % (instance.leaf.leaf_type.model, instance.leaf.pk, filename)

def attachment_checksum(f):
    try:
        h = hashlib.md5()
        for chunk in f.chunks():
            h.update(chunk)
        return h.hexdigest()
    except:
        return ''

def template_context(request):
    return {
        'site': request.site,
    }

CACHED_SITE = None

def get_site():
    """
    Returns the current Site object. If this is called while handling a request,
    the Site will have been loaded dynamically based on the hostname. Otherwise,
    fall back to using settings.SITE_ID.
    """
    try:
        from leaves.middleware import request_context
        return request_context.site
    except:
        if CACHED_SITE is None:
            CACHED_SITE = Site.objects.select_related('preferences').get(pk=settings.SITE_ID)
        return CACHED_SITE

def get_page(request, queryset, per_page=None):
    """
    Returns a django.core.pagination.Page object based on the page number
    in the request, the stream_count preference for the site, and the specified
    queryset.
    """
    if per_page is None:
        per_page = get_site().preferences.stream_count
    paginator = Paginator(queryset, per_page)
    try:
        pagenum = int(request.GET.get('page', 1))
        if pagenum < 1:
            pagenum = 1
    except ValueError:
        pagenum = 1
    try:
        page = paginator.page(pagenum)
    except InvalidPage:
        page = paginator.page(paginator.num_pages)
    return page