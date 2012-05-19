from urlparse import urlparse
from cgi import parse_qs

from django.conf import settings


class IframedMiddleware(object):
    """
    Checks META referer header for 'id' parameter and uses it as request path
    """
    def __init__(self):
        self.mappings = getattr(settings, 'IFRAMED_MAPPINGS', [])
        self.aliases = getattr(settings, 'IFRAMED_ALIASES', {})
        self.query_id = getattr(settings, 'IFRAMED_QUERY_ID', 'id')
    

    def process_request(self, request):
        # parse HTTP_REFERER header.
        # This is the URL of the page embedding the iframe.
        referer = urlparse(request.META.get('HTTP_REFERER', ''))
        query_parsed = parse_qs(referer.query)
        
        aliased_path, is_aliased = self.find_alias(referer.path)
        
        # Match referer path to app name
        path_info = self.match_path(aliased_path)
        if path_info is None:
            return
        
        # Parse query parameter
        query_id = self.query_id
        if query_parsed.get(query_id) and len(query_parsed[query_id]):
            path_info += query_parsed[query_id][0]
        else:
            path_info += '/'
        
        if not is_aliased:
            request.path_info = path_info
        request.referer = referer
        request.aliased_referer_path = aliased_path
        
    def find_alias(self, path):
        if path.endswith('/'):
            path = path[:-1]
        
        if self.aliases.get(path):
            return self.aliases.get(path), True
        
        return path, False
    
    def match_path(self, referer_path):
        """Tries to match referer path to internal path"""
        for prefix_internal, prefix_external in self.mappings:
            if referer_path.startswith(prefix_external):
                return prefix_internal
        
        return None
