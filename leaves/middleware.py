from django.shortcuts import get_object_or_404
from django.core.urlresolvers import resolve
from django.contrib.sites.models import Site
from django.utils.encoding import iri_to_uri
from django.conf import settings
from django import http
from leaves.models import Leaf, Redirect
import threading

request_context = threading.local()

class LeavesSiteMiddleware (object):

    def process_request(self, request):
        host = request.get_host().lower().split(':')[0]
        # In order to support subdomains, we need to check all the sites
        # to find the most specific.
        all_sites = {}
        default_site = None
        for s in Site.objects.select_related('preferences'):
            all_sites[s.domain.lower()] = s
            if s.pk == settings.SITE_ID:
                default_site = s
        # If all else fails, fall back to using SITE_ID.
        request.site = default_site
        if host in all_sites:
            request.site = all_sites[host]
        else:
            # Find the most specific match, determined by match suffix length.
            best_match = None
            match_len = 0
            for domain, site in all_sites.items():
                if host.endswith(domain) and len(domain) > match_len:
                    best_match = site
                    match_len = len(domain)
            if best_match:
                request.site = best_match
        request_context.site = request.site
        # Also keep track of the current user. Helpful for template tags.
        request_context.user = request.user

    def process_response(self, request, response):
        if hasattr(request_context, 'site'):
            del request_context.site
        if hasattr(request_context, 'user'):
            del request_context.user
        return response

class LeavesFallbackMiddleware (object):

    def process_response(self, request, response):
        if response.status_code != 404:
            return response
        try:
            url = request.path_info
            if not url.endswith('/') and settings.APPEND_SLASH:
                return http.HttpResponseRedirect('%s/' % request.path)
            if not url.startswith('/'):
                url = '/' + url
            leaf = get_object_or_404(Leaf, custom_url=url)
            leaf = leaf.resolve()
            # We need to try to find the view that normally renders this Leaf
            # type. Since the URL is custom, we fall back to trying
            # get_absolute_url on the Leaf subclass, which should return a URL
            # mapped in the plugin's urlconf.
            match = resolve(leaf.get_absolute_url())
            r = match.func(request, *match.args, **match.kwargs)
            # If the response is a TemplateResponse, we need to bake it.
            if hasattr(r, 'render'):
                r.render()
            return r
        except http.Http404:
            # If we still haven't found anything, check the redirects.
            try:
                url = request.get_full_path()
                r = Redirect.objects.get(old_path=url, site=request.site)
                if not r.new_path:
                    return http.HttpResponseGone()
                resp = http.HttpResponse(status=r.redirect_type)
                resp['Location'] = iri_to_uri(r.new_path)
                return resp
            except Redirect.DoesNotExist:
                return response
        except:
            if settings.DEBUG:
                raise
            return response
