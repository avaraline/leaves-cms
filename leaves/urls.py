from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from leaves.utils import homepage

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'leaves.views.index', name='home'),
    url(r'^recent/$', 'leaves.views.recent', name='recent'),
    url(r'^page/(?P<slug>[^/]+)/$', 'leaves.views.page_view', name='page-view'),
    url(r'^tag/(?P<slug>[^/]+)/$', 'leaves.views.tag_view', name='tag-view'),
    url(r'^author/(?P<username>[^/]+)/$', 'leaves.views.author_view', name='author-view'),
    url(r'^lang/(?P<lang>[^/]+)/$', 'leaves.views.set_language', name='language'),
    url(r'^admin/', include(admin.site.urls)),
)

# Configure plugin URLs here. Should these be dynamically discovered based on INSTALLED_APPS?
urlpatterns += patterns('',
    url('^blog/', include('leaves.plugins.blog.urls')),
)

homepage.register('recent', 'Recent Leaves')
