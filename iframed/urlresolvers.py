from django.core.urlresolvers import reverse as django_reverse, get_script_prefix

from django.conf import settings

mappings = getattr(settings, 'IFRAMED_MAPPINGS', [])
rewrites = getattr(settings, 'IFRAMED_REWRITES', {})
query_id = getattr(settings, 'IFRAMED_QUERY_ID', 'id')
default_base = getattr(settings, 'IFRAMED_DEFAULT_BASE', None)

def reverse(viewname, request=None, use_default_base=False, *args, **kwargs):
    """
    Django reverse lookup that returns URLs suitable for iframe-embedding
    """
    
    # perform standard reverse lookup and strip out script_prefix
    absolute_url = django_reverse(viewname, *args, **kwargs)
    script_prefix = get_script_prefix()
    url = absolute_url[len(script_prefix)-1:]
    
    # check if a manual override is defined
    if rewrites.get(url):
        return rewrites.get(url)
        
    # try to find a suitable internal-external mapping in configuration
    prefix_internal = None
    prefix_external = None
    for pin, pex in mappings:
        if url.startswith(pin):
            prefix_internal = pin
            prefix_external = pex
            break
    if prefix_internal is None:
        # no match found, fall back to standard URL
        return absolute_url
    
    query_url = url[len(prefix_internal):]
    
    if use_default_base and default_base is not None:
        # use default location
        iframed_url = '%(base)s%(prefix)s?%(query_id)s=%(url)s' % {
            'base': default_base,
            'prefix': prefix_external,
            'query_id': query_id,
            'url': query_url,
        }
        return iframed_url
    
    elif request is not None and hasattr(request, 'referer'):
        # build absolute URL from referer attribute
        referer = request.referer
        if hasattr(request, 'aliased_referer_path'):
            path = request.aliased_referer_path
        else:
            path = referer.path
        iframed_url = '%(scheme)s://%(netloc)s%(path)s?%(query_id)s=%(url)s' % {
            'scheme': referer.scheme,
            'netloc': referer.netloc,
            'path': path,
            'query_id': query_id,
            'url': query_url,
        }
        return iframed_url
    
    else:
        # referer not set but required, fall back to standard URL
        return absolute_url
        
