from django.conf.urls import patterns, include, url
from leaves.utils import homepage

urlpatterns = patterns('leaves.plugins.blog.views',
    url(r'^$', 'index', name='blog-index'),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<slug>[^/]+)/$', 'post', name='blog-post'),
)

homepage.register('blog-index', 'Recent Blog Posts')
