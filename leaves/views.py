from django.shortcuts import render, get_object_or_404
from django import http
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, resolve
from django.conf import settings
from leaves.models import Leaf, Page, Tag
from leaves.utils import homepage, get_page
from leaves.comments import comment

def index(request):
    return homepage.render(request)

def recent(request):
    qs = Leaf.objects.stream()
    return render(request, 'index.html', {
        'page': get_page(request, qs, request.site.preferences.stream_count),
    })

def page_view(request, slug):
    qs = Page.objects.published(bypass=True)
    page = get_object_or_404(qs, slug__iexact=slug)
    return comment(request, page) or render(request, page.get_page_templates(), {
        'page': page,
    })

def tag_view(request, slug):
    tag = get_object_or_404(Tag, slug__iexact=slug)
    qs = Leaf.objects.stream().filter(tags__in=(tag,))
    return render(request, 'tag.html', {
        'tag': tag,
        'page': get_page(request, qs, request.site.preferences.stream_count),
    })

def author_view(request, username):
    author = get_object_or_404(User, username__iexact=username)
    qs = Leaf.objects.stream().filter(author=author)
    return render(request, 'author.html', {
        'author': author,
        'page': get_page(request, qs, request.site.preferences.stream_count),
    })

def set_language(request, lang):
    next = request.REQUEST.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', None)
    if not next:
        next = reverse('home')
    for code, name in settings.LANGUAGES:
        if lang == code:
            request.session['django_language'] = lang
            break
    return http.HttpResponseRedirect(next)
