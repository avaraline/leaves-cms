from django.db import models
from django.utils import timezone
from leaves.utils import get_site, get_user, get_language

class NaturalKeyManager (models.Manager):
    """
    """

    def __init__(self, *field_names):
        self.field_names = tuple(field_names) or ('slug',)
        super(NaturalKeyManager, self).__init__()

    def get_by_natural_key(self, *keys):
        if len(self.field_names) != len(keys):
            raise ValueError('Could not get %s by natural key: %s' % (self.model.__class__, keys))
        params = dict(zip(self.field_names, keys))
        return self.get(**params)

class LeafManager (NaturalKeyManager):
    """
    """

    def get_query_set(self):
        qs = super(LeafManager, self).get_query_set()
        related = getattr(self.model, '_leaves_related_field_names', None)
        if related is None:
            # Get all the non-null ForeignKey fields.
            related = [f.name for f in self.model._meta.fields if isinstance(f, models.ForeignKey) and not f.null]
            if self.model.__name__ == 'Leaf':
                # Now get all the subclasses of Leaf to select the reverse relation of the OneToOneFields.
                related += [cls.__name__.lower() for cls in self.model.__subclasses__()]
            self.model._leaves_related_field_names = related
        return qs.select_related(*related)

    def published(self, site=None, user=None, language=None, asof=None, bypass=False):
        if site is None:
            site = get_site()
        if user is None:
            user = get_user()
        if asof is None:
            asof = timezone.now()
        q_exp = models.Q(date_expires__isnull=True) | models.Q(date_expires__gt=asof)
        q_pub = models.Q(status='published') & models.Q(date_published__lte=asof)
        q_auth = models.Q(author=user)
        qs = self.get_query_set().filter(sites__pk=site.pk)
        if language:
            qs = qs.filter(language=language)
        else:
            qs = qs.filter(translation_of__isnull=True)
        if bypass:
            if user.is_superuser:
                # Superusers can see anything on the site, if we're bypassing the publishing checks.
                return qs
            elif user.is_authenticated():
                # Otherwise, an authenticated user may see unpublished leaves if they are the author.
                return qs.filter((q_exp & q_pub) | q_auth)
        # By default, make sure only published, unexpired leaves are returned.
        return qs.filter(q_exp & q_pub)

    def stream(self, site=None, user=None, language=None, asof=None, bypass=False):
        qs = self.published(site=site, user=user, language=language, asof=asof, bypass=bypass)
        return qs.filter(show_in_stream=True)
