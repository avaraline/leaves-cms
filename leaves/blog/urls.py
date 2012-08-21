from django.conf.urls import patterns, include, url
from leaves.utils import homepage

urlpatterns = patterns('',
    url(r'^$', 'leaves.blog.views.index', name='blog-index'),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<slug>[^/]+)/$', 'leaves.blog.views.post', name='blog-post'),
)

homepage.register('blog-index', 'Recent Blog Posts')
