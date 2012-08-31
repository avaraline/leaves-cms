from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, resolve
from django.contrib.sites.models import Site
from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator, InvalidPage
from django.template.base import TemplateDoesNotExist
from django.template.loader import BaseLoader
from django.utils import importlib
from django.db.models import get_apps
from django.shortcuts import redirect
import itertools
import hashlib
import os

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

def theme_choices():
    for app in get_apps():
        if hasattr(app, 'LEAVES_THEME_NAME'):
            app_mod = app.__name__.rsplit('.', 1)[0]
            yield app_mod, app.LEAVES_THEME_NAME

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
        'post_data': request.POST if request.method == 'POST' else None,
    }

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
        return Site.objects.select_related('preferences').get(pk=settings.SITE_ID)

def get_user():
    """
    Returns the current User object. If this is called while handling a request,
    it is equivalent to request.user. Otherwise, returns an AnonymousUser object.
    """
    try:
        from leaves.middleware import request_context
        return request_context.user
    except:
        return AnonymousUser()

def get_language():
    """
    Returns the current language. If one is set while handling a request, it is
    returned here. Otherwise, the current site's default language is returned.
    """
    try:
        from leaves.middleware import request_context
        return request_context.language
    except:
        return get_site().preferences.default_language

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

class SiteThemeLoader (BaseLoader):
    is_usable = True

    def load_template_source(self, template_name, template_dirs=None):
        try:
            theme_app = get_site().preferences.theme
            theme_mod = importlib.import_module(theme_app)
            template_path = os.path.join(os.path.dirname(theme_mod.__file__), 'templates', template_name)
            with open(template_path, 'rb') as fp:
                return (fp.read().decode(settings.FILE_CHARSET), template_path)
        except:
            pass
        raise TemplateDoesNotExist(template_name)

# TODO: this is probably ill-conceived, but the code might be useful in something like a templatetag that displays
#       a "This page is available in LANGUAGE" banner.
def translate(request, leaf):
    # If the page was specifically requested, or is already in the user's language, do nothing.
    if 'notrans' in request.GET or request.LANGUAGE_CODE == leaf.language:
        return
    # Get the "root" leaf, i.e. the one other translations are based on.
    root_leaf = leaf.translation_of if leaf.translation_of else leaf
    # If the root leaf is in the user's language, redirect to it.
    if root_leaf.language == request.LANGUAGE_CODE:
        return redirect(root_leaf.resolved.url)
    # Otherwise, try to find a translation of the root leaf in the user's language.
    try:
        trans_leaf = root_leaf.translations.get(language=request.LANGUAGE_CODE)
        return redirect(trans_leaf.resolved.url)
    except:
        pass
