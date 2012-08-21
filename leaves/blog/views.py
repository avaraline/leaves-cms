from django.shortcuts import render, get_object_or_404
from leaves.blog.models import Post
from leaves.utils import get_page

def index(request):
    qs = Post.objects.stream(site=request.site, user=request.user)
    return render(request, 'blog/index.html', {
        'page': get_page(request, qs, request.site.preferences.stream_count),
    })

def post(request, year, month, slug):
    qs = Post.objects.stream(site=request.site, user=request.user)
    post = get_object_or_404(qs, date_published__year=year, date_published__month=month, slug__iexact=slug)
    return render(request, post.get_page_templates(), {
        'post': post,
    })
