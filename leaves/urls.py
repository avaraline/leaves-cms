from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'leaves.views.index', name='home'),
    url(r'^page/(?P<slug>[^/]+)/$', 'leaves.views.page_view', name='page-view'),
    url(r'^tag/(?P<slug>[^/]+)/$', 'leaves.views.tag_view', name='tag-view'),
    url(r'^author/(?P<username>[^/]+)/$', 'leaves.views.author_view', name='author-view'),
    url(r'^admin/', include(admin.site.urls)),
)

# Configure plugin URLs here.
urlpatterns += patterns('',
    url('^blog/', include('leaves.blog.urls')),
)
