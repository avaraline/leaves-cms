from django.db import models
from django.utils.translation import ugettext_lazy as _
from leaves.models import Leaf
from leaves.managers import LeafManager

class Post (Leaf):
    title = models.CharField(_('title'), max_length=200)
    slug = models.SlugField(_('slug'), unique=True)
    summary = models.TextField(_('summary'), blank=True)
    content = models.TextField(_('content'))

    objects = LeafManager()

    def __unicode__(self):
        return self.title
    __unicode__.admin_order_field = 'title'

    def natural_key(self):
        return (self.slug,)

    @models.permalink
    def get_absolute_url(self):
        return ('blog-post', (), {
            'year': str(self.date_published.year),
            'month': '%02d' % self.date_published.month,
            'slug': self.slug,
        })
