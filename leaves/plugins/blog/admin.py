from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from leaves.admin import LeafAdmin, PUBLISHING_OPTIONS, ADVANCED_PUBLISHING_OPTIONS, SITEMAP_OPTIONS, \
    TRANSLATION_OPTIONS
from leaves.plugins.blog.models import Post

class PostAdmin (LeafAdmin):
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'summary', 'content'),
        }),
        PUBLISHING_OPTIONS,
        ADVANCED_PUBLISHING_OPTIONS,
        SITEMAP_OPTIONS,
        TRANSLATION_OPTIONS,
    )
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(Post, PostAdmin)
