from django.shortcuts import render, get_object_or_404
from django import http
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, resolve
from leaves.models import Leaf, Page, Tag
from leaves.utils import homepage, get_page
from leaves.comments import handle_comment

def index(request):
    return homepage.render(request)

def recent(request):
    qs = Leaf.objects.stream(site=request.site, user=request.user)
    return render(request, 'index.html', {
        'page': get_page(request, qs, request.site.preferences.stream_count),
    })

def page_view(request, slug):
    qs = Page.objects.published(site=request.site, user=request.user)
    page = get_object_or_404(qs, slug__iexact=slug)
    return handle_comment(request, page) or render(request, page.get_page_templates(), {
        'page': page,
    })

def tag_view(request, slug):
    tag = get_object_or_404(Tag, slug__iexact=slug)
    qs = Leaf.objects.stream(site=request.site, user=request.user).filter(tags__in=(tag,))
    return render(request, 'tag.html', {
        'tag': tag,
        'page': get_page(request, qs, request.site.preferences.stream_count),
    })

def author_view(request, username):
    author = get_object_or_404(User, username__iexact=username)
    qs = Leaf.objects.stream(site=request.site, user=request.user).filter(author=author)
    return render(request, 'author.html', {
        'author': author,
        'page': get_page(request, qs, request.site.preferences.stream_count),
    })
