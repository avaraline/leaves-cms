from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from leaves.managers import NaturalKeyManager, LeafManager
from leaves.utils import *

class Tag (models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField()

    objects = NaturalKeyManager()

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.slug,)

class Leaf (models.Model):
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('pending', _('Needs Approval')),
        ('published', _('Published')),
    )

    CHANGEFREQ_OPTIONS = (
        ('never', _('Never')),
        ('yearly', _('Yearly')),
        ('monthly', _('Monthly')),
        ('weekly', _('Weekly')),
        ('daily', _('Daily')),
        ('hourly', _('Hourly')),
        ('always', _('Always')),
    )

    PRIORITY_OPTIONS = (
        (0.0, 0.0),
        (0.1, 0.1),
        (0.2, 0.2),
        (0.3, 0.3),
        (0.4, 0.4),
        (0.5, 0.5),
        (0.6, 0.6),
        (0.7, 0.7),
        (0.8, 0.8),
        (0.9, 0.9),
        (1.0, 1.0),
    )

    sites = models.ManyToManyField(Site, verbose_name=_('sites'), related_name='leaves')
    author = models.ForeignKey(User, verbose_name=_('author'), related_name='leaves')
    author_name = models.CharField(_('author name'), max_length=100)
    status = models.CharField(_('status'), max_length=10, choices=STATUS_CHOICES, db_index=True,
        default=settings.LEAVES_DEFAULT_LEAF_STATUS)
    show_in_stream = models.BooleanField(_('show in stream'), default=True,
        help_text=_('When checked, this content will appear in your stream.'))
    allow_comments = models.BooleanField(_('allow comments'), default=True)
    password = models.CharField(_('password'), max_length=30, blank=True,
        help_text=_('If set, this leaf will require a password to view.'))
    date_published = models.DateTimeField(_('publish date'), default=timezone.now,
        help_text=_('This content will only be visible after this date.'))
    date_expires = models.DateTimeField(_('expiration date'), blank=True, null=True,
        help_text=_('This content will not be visible after this date. Leave blank for indefinite visibility.'))
    changefreq = models.CharField(_('sitemap change frequency'), choices=CHANGEFREQ_OPTIONS, default='monthly',
        help_text=_('How often should search engines index this content?'), max_length=7)
    priority = models.FloatField(_('sitemap priority'), choices=PRIORITY_OPTIONS, default=0.5,
        help_text=_('How important is this relative to your other content? 1.0 is highest.'))
    language = models.CharField(_('language'), max_length=10, choices=language_choices(),
        default=default_language)
    translation_of = models.ForeignKey('self', verbose_name=_('translation of'), related_name='translations',
        null=True, blank=True, help_text=_('If this is a translation of another leaf, select it here.'))
    translator_name = models.CharField(_('translator name'), max_length=100, blank=True,
        help_text=_('Name of the person translating this leaf. Can be blank.'))
    custom_url = models.CharField(_('custom url'), max_length=200, blank=True,
        help_text=_('A custom URL for this leaf, e.g. /my-page/'))
    summary_template = models.CharField(_('summary template'), max_length=200, blank=True,
        help_text=_('(Optional) A custom template for rendering a summary of this leaf.'))
    page_template = models.CharField(_('page template'), max_length=200, blank=True,
        help_text=_('(Optional) A custom template for rendering this leaf in full.'))
    tags = models.ManyToManyField(Tag, verbose_name=_('tags'), related_name='leaves', blank=True)
    date_created = models.DateTimeField(default=timezone.now, editable=False)
    date_modified = models.DateTimeField(editable=False)
    leaf_type = models.ForeignKey(ContentType, related_name='leaves', editable=False)

    objects = LeafManager()

    class Meta:
        verbose_name_plural = 'leaves'
        ordering = ('-date_published',)
        unique_together = ('language', 'custom_url')

    def __unicode__(self):
        return u'%s: %s' % (self.leaf_type.model_class().__name__, unicode(self.resolved))

    def save(self, *args, **kwargs):
        assert self.__class__ is not Leaf, 'Attempted to save a bare Leaf model.'
        self.leaf_type = ContentType.objects.get_for_model(self.__class__)
        self.date_modified = timezone.now()
        if not self.pk:
            self.date_created = self.date_modified
        super(Leaf, self).save(*args, **kwargs)

    def resolve(self):
        if self.__class__ is self.leaf_type.model_class():
            return self
        return getattr(self, self.leaf_type.model)
    resolved = property(resolve)

    def get_url(self):
        return self.custom_url or self.get_absolute_url()
    url = property(get_url)

    def get_page_templates(self):
        return (
            self.page_template,
            '%s/%s.html' % (self.leaf_type.app_label, self.leaf_type.model),
            '%s.html' % self.leaf_type.model,
        )

    def get_summary_templates(self):
        return (
            self.summary_template,
            '%s/%s_summary.html' % (self.leaf_type.app_label, self.leaf_type.model),
            '%s_summary.html' % self.leaf_type.model,
        )

class LeafMeta (models.Model):
    leaf = models.ForeignKey(Leaf, verbose_name=_('leaf'), related_name='metadata')
    key = models.CharField(_('key'), max_length=50)
    value = models.TextField(_('value'))

    class Meta:
        verbose_name = _('metadata')
        verbose_name_plural = _('metadata')

    def __unicode__(self):
        return self.key

class Comment (models.Model):
    STATUS_CHOICES = (
        ('spam', _('Spam')),
        ('pending', _('Needs Approval')),
        ('published', _('Published')),
    )

    leaf = models.ForeignKey(Leaf, verbose_name=_('leaf'), related_name='comments')
    reply_to = models.ForeignKey('self', verbose_name=_('in reply to'), blank=True, null=True, related_name='replies')
    author_name = models.CharField(_('author name'), max_length=50)
    user = models.ForeignKey(User, verbose_name=_('user'), blank=True, null=True, related_name='comments')
    email = models.EmailField(_('email'), help_text=_('Your email address will never be shown publicly.'))
    website = models.URLField(_('website'), blank=True, verify_exists=False)
    status = models.CharField(_('status'), max_length=10, choices=STATUS_CHOICES, db_index=True,
        default=settings.LEAVES_DEFAULT_COMMENT_STATUS)
    date_posted = models.DateTimeField(_('date posted'), default=timezone.now)
    comment = models.TextField(_('comment'))

    class Meta:
        ordering = ('date_posted',)

    def __unicode__(self):
        return unicode(self.pk)

    def get_absolute_url(self):
        return self.leaf.resolved.url + '#comment-%s' % self.pk

class Attachment (models.Model):
    leaf = models.ForeignKey(Leaf, verbose_name=_('leaf'), related_name='attachments')
    attachment = models.FileField(_('attachment'), upload_to=attachment_path)
    filename = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200, blank=True)
    md5_checksum = models.CharField(max_length=32, editable=False)
    download_count = models.PositiveIntegerField(default=0, editable=False)
    rank = models.IntegerField(default=0, help_text=_('Used for ordering attachments.'))

    class Meta:
        ordering = ('rank', 'title', 'filename')

    def __unicode__(self):
        if self.title:
            return self.title
        elif self.filename:
            return self.filename
        else:
            return os.path.basename(self.attachment.name)

    def save(self, **kwargs):
        if kwargs.pop('checksum', True):
            self.md5_checksum = attachment_checksum(self.attachment)
        super(Attachment, self).save(**kwargs)

class Redirect (models.Model):
    REDIRECT_TYPES = (
        (301, '301 - Moved Permanently'),
        (302, '302 - Found'),
        (307, '307 - Temporary Redirect'),
        (410, '410 - Gone'),
    )

    site = models.ForeignKey(Site, verbose_name=_('site'), related_name='redirects')
    old_path = models.CharField(_('old path'), max_length=250, db_index=True)
    new_path = models.CharField(_('new path'), max_length=250, blank=True,
        help_text=_('Leave the new path blank to indicate a page that no longer exists.'))
    redirect_type = models.IntegerField(_('redirect type'), choices=REDIRECT_TYPES, default=301)

    class Meta:
        unique_together = ('site', 'old_path')
        ordering = ('old_path',)

    def __unicode__(self):
        return '%s --> %s (%s)' % (self.old_path, self.new_path, self.redirect_type)

class Preferences (models.Model):
    site = models.OneToOneField(Site, verbose_name=_('site'), unique=True, related_name='preferences')
    homepage = models.CharField(_('homepage'), max_length=200, choices=homepage)
    theme = models.CharField(_('theme'), max_length=100, choices=theme_choices())
    stream_count = models.PositiveIntegerField(_('stream count'), default=10)
    feed_count = models.PositiveIntegerField(_('feed count'), default=10)
    analytics_id = models.CharField(_('analytics id'), max_length=50, blank=True)
    default_language = models.CharField(_('default language'), max_length=10, choices=language_choices(),
        default=default_language)
    default_comment_status = models.CharField(_('default comment status'), max_length=10,
        choices=Comment.STATUS_CHOICES, default=settings.LEAVES_DEFAULT_COMMENT_STATUS)

    class Meta:
        verbose_name_plural = _('preferences')

class Page (Leaf):
    title = models.CharField(_('title'), max_length=200)
    slug = models.SlugField(_('slug'), unique=True)
    summary = models.TextField(_('summary'), blank=True)
    content = models.TextField(_('content'))
    show_in_navigation = models.BooleanField(_('show in navigation'), default=True,
        help_text=_('When checked, this content will appear in your site navigation.'))
    rank = models.IntegerField(_('rank'), default=0,
        help_text=_('Determines the ordering of pages, i.e. for navigation.'))

    objects = LeafManager()

    class Meta:
        ordering = ('rank',)

    def __unicode__(self):
        return self.title
    __unicode__.admin_order_field = 'title'

    def natural_key(self):
        return (self.slug,)

    @models.permalink
    def get_absolute_url(self):
        return ('page-view', (), {'slug': self.slug})
