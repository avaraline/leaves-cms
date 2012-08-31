from django.shortcuts import render, get_object_or_404
from leaves.plugins.blog.models import Post
from leaves.utils import get_page
from leaves.comments import comment

def index(request):
    return render(request, 'blog/index.html', {
        'page': get_page(request, Post.objects.stream(), request.site.preferences.stream_count),
    })

def post(request, year, month, slug):
    post = get_object_or_404(Post.objects.stream(), date_published__year=year, date_published__month=month,
        slug__iexact=slug)
    return comment(request, post) or render(request, post.get_page_templates(), {
        'post': post,
    })
