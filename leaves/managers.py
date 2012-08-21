from django.db import models
from django.utils import timezone

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
        # Get all the non-null ForeignKey fields.
        related = [f.name for f in self.model._meta.fields if isinstance(f, models.ForeignKey) and not f.null]
        if self.model.__name__ == 'Leaf':
            # Now get all the subclasses of Leaf to select the reverse relation of the OneToOneFields.
            related += [cls.__name__.lower() for cls in self.model.__subclasses__()]
        return qs.select_related(*related)

    def published(self, site=None, user=None, asof=None):
        if asof is None:
            asof = timezone.now()
        exp = models.Q(date_expires__isnull=True) | models.Q(date_expires__gt=asof)
        q = models.Q(status='published') & models.Q(date_published__lte=asof) & exp
        if site:
            q &= models.Q(sites__in=(site,))
        # Show the user's leaves in the published stream, even if they aren't. This is particularly useful for the
        # admin's "Show on site" feature.
        if user and user.is_authenticated():
            q |= models.Q(author=user)
        return self.get_query_set().filter(q)

    def stream(self, site=None, user=None, asof=None):
        qs = self.published(site=site, user=user, asof=asof)
        return qs.filter(show_in_stream=True)
