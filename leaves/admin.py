from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.sites.models import Site
from leaves.models import Tag, Comment, Attachment, Redirect, Preferences, Page

PUBLISHING_OPTIONS = (_('Publishing Options'), {
    'fields': ('author', 'author_name', 'status', 'date_published', 'date_expires', 'tags'),
})

ADVANCED_PUBLISHING_OPTIONS = (_('Advanced Publishing Options'), {
    'classes': ('collapse',),
    'fields': ('sites', 'show_in_stream', 'allow_comments', 'password', 'custom_url', 'summary_template',
               'page_template'),
})

SITEMAP_OPTIONS = (_('Sitemap Options'), {
    'classes': ('collapse',),
    'fields': ('changefreq', 'priority'),
})

TRANSLATION_OPTIONS = (_('Translation Options'), {
    'classes': ('collapse',),
    'fields': ('language', 'translation_of', 'translator_name'),
})

class AttachmentInline (admin.TabularInline):
    model = Attachment
    extra = 1

class LeafAdmin (admin.ModelAdmin):
    list_display = ('__unicode__', 'language', 'author_name', 'status', 'date_published', 'date_expires',
        'date_created', 'date_modified', 'show_in_stream', 'url')
    list_filter = ('author', 'sites', 'status', 'show_in_stream', 'language')
    list_select_related = True
    date_hierarchy = 'date_published'
    inlines = (AttachmentInline,)

    def url(self, obj):
        if obj.custom_url:
            return obj.custom_url
        elif hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url()
        return ''
    url.short_description = 'URL'

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'author_name' and 'request' in kwargs:
            kwargs['initial'] = kwargs['request'].user.get_full_name().strip()
        return super(LeafAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'author':
            if not request.user.is_superuser:
                kwargs['queryset'] = User.objects.filter(pk=request.user.pk)
            kwargs['initial'] = request.user.pk
        return super(LeafAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'sites':
    		kwargs['initial'] = Site.objects.all()
        return super(LeafAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

class CommentAdmin (admin.ModelAdmin):
    list_display = ('leaf', 'title', 'author_name', 'email', 'status', 'date_posted')
    list_filter = ('date_posted', 'status', 'leaf__sites')
    date_hierarchy = 'date_posted'
    search_fields = ('title', 'comment', 'author_name', 'email')
    actions = ('approve_comments',)
    ordering = ('-date_posted',)

    def approve_comments(self, request, queryset):
        update_count = queryset.update(status='published')
        term = 'comment was' if update_count == 1 else 'comments were'
        self.message_user(request, '%s %s successfully approved.' % (update_count, term))
    approve_comments.short_description = 'Mark selected comments as published'

class TagAdmin (admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

class RedirectAdmin (admin.ModelAdmin):
    list_display = ('old_path', 'new_path', 'site', 'redirect_type')
    list_filter = ('site', 'redirect_type')

class PreferencesAdmin (admin.ModelAdmin):
    list_display = ('site', 'homepage', 'stream_count', 'feed_count', 'analytics_id', 'default_comment_status')

class PageAdmin (LeafAdmin):
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

admin.site.register(Tag, TagAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Redirect, RedirectAdmin)
admin.site.register(Preferences, PreferencesAdmin)
admin.site.register(Page, PageAdmin)
