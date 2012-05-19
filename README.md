django-iframed
==============

`iframed` seamlessly integrates a Django site running in an iframe into a surrounding site.

## Scenario ##

The app was built for a specific use case. [A large organisation](http://www.wu.ac.at/) uses a CMS for its web presence. [One department](http://www.wu.ac.at/library/) of this organisation wants to offer a number of features not available in the CMS. Although the CMS supports custom extensions, the organisation's IT department wants to avoid development effort and support responsibility for additional features that are specific to one department.

Instead, the IT department introduces an `iframe` extension into the CMS. This allows the tech-savvy department to display additional content without the limitations of the CMS. It also makes the department free to choose the technology for its custom features. In this case, the department decides to create a Django project that contains all the custom features.

## iframe? eugh! ##

True, use of `iframe` elements introduces a range of problems, both technical and relating to user experience, and is frowned upon with good reason. Simply put, `iframes` are best avoided wherever possible.

However, in some scenarios like the one described above, an `iframe` is the only feasible solution. `django-iframed` attempts to make the user experience as seamless as possible.

## Operation ##

`iframed` provides several mechanisms that improve integration of `iframe` content into a site.

 - It allows unique links to any view of the Django project through a single iframe instance. This is achieved using a GET query parameter that gets appended to the parent page URL and a Django middleware that inspects the `HTTP_REFERER` request header for this parameter.
 - It provides a custom `reverse` URL resolver and a custom `{% url %}` template tag. These are used like their regular Django counterparts but create URLs that link to the parent page containing the iframe. They also contain the necessary GET parameter to open the correct view in the project within the iframe. Links created by the template tag contain the `target="_top"` attribute.

### Middleware ###

A middleware class inspects the `HTTP_REFERER` header of all incoming requests. Conveniently, if a page is contained within an `iframe`, the referer points to the URL of the parent page that contains the `iframe`.

The referer URL is inspected. The request path is matched against a list of mappings. These map external request paths to Django request paths. If a match is found the request path is replaced.

Additionally, a configurable GET parameter is inspected and appended to the internal request path. This allows unique URLs for any view in the project through a single iframe element.

### URL reversal ###

The custom `reverse` URL resolver uses the opposite approach. It first uses Django's `reverse` function to create a standard domain-absolute URL. Then, the URL is re-written into a URL suitable for the browser address bar. The result is a URL that opens a page in the embedding site that contains the `iframe`, with a GET query parameter that in turn instructs the Django project to show the right content.

The URL template tag provided by `iframed` uses this `reverse` function. Additionally, it appends the attribute `target='_top'` to parent site links. The custom URL template tag can be used in place of the default one without requiring further changes. Links will change the overall location of the browser location, not just within the `iframe`, making the integration of the iframe much more seamless.

### Example ###

The referer header is set to the following:
http://www.commondomain.com/page_containing_iframe/?id=/page/2

The URL is inspected and divided up as follows:

<table>
	<tr>
		<td style="color:#0071BC">http://www.commondomain.com</td>
		<td style="color:#006837">/page_containing_iframe</td>
		<td style="color:#998675">/?id=</td>
		<td style="color:#9E005D">/page/2</td>
	</tr>
	<tr>
		<td>Base domain for external site</td>
		<td>Maps to a specific app in the project</td>
		<td>Query parameter inspected by Iframed</td>
		<td>Django request path</td>
	</tr>
</table>


## Installation ##

- Include the `iframed` app in your project path and add `'iframed'` to your `INSTALLED_APPS` tuple.
- Add `'django.core.context_processors.request'` to your `TEMPLATE_CONTEXT_PROCESSORS` tuple.
- Add `'iframed.middleware.IframedMiddleware'` to the top of your `MIDDLEWARE_CLASSES` tuple.

### Available settings ###

```python

IFRAMED_MAPPINGS = [
    # format:
    # (<internal_prefix>, <external_prefix>)
    ('/appname', '/page_containing_iframe'),
]
# Maps Django-specific URLs to locations in the embedding site. Required.
# The example rewrites requests originating from
# `/page_containing_iframe/?id=<request_path>` to `/appname<request_path>`.
# For example, `/page_containing_iframe/?id=/page/2` is rewritten as if a
# request had been sent to `/appname/page/2`. 
# Installations not located at a root URL are detected correctly. If the
# Django project is located at `/path_to_django`, requests to
# `/page_containing_iframe/?id=/page/2` get rewritten to
# `/path_to_django/appname/page/2`.

IFRAMED_QUERY_ID = '<query_id>'
# Configures the GET parameter that is inspected for the internal path.
# Optional, defaults to `'id'`.

IFRAMED_ALIASES = {
	# format:
	# ('<alternative_location>': '<target_location>')
    ('/alernative_page', '/page_containing_iframe'),
}
# Defines alternative entry locations for existing mappings.
# Dictionary values must correspond to (the right half of) an entry in
# IFRAMED_MAPPINGS.  An iframe placed in the alternative location will behave
# as if placed in the target location. Optional.

IFRAMED_REWRITES = {
   # format:
   # <internal_path>: <external_path>
   '/feed/rss/': 'http://www.example.com/news/feed/',
}
# Defines manual overrides for URL reversal. Optional.

IFRAMED_DEFAULT_BASE = 'http://localhost:8000'
# Defines fallback base domain to be used for reversed URLs if the
# `HTTP_REFERER` request header was not defined. Optional.
```


## Additional steps for seamless iframes ##

### Cross-domain policy issues ###

Modern browsers have strict cross-domain policies governing what information is shared between iframe and parent page. If possible, the iframed content should be served on the same domain as the parent content.

One case of cross-domain communication that can be enabled easily is where the parent page and the iframe content are served from different subdomains of the same domain. In this case, both parent page and iframed page need to include a short script that explicitly allows communication across subdomains. Assuming the parent page is hosted on `www.commondomain.com` and the iframe content is hosted on `custom.commondomain.com`, both pages include the following:
```javascript
<script type="text/javascript" charset="utf-8">
	try {
		document.domain = 'commondomain.com';
	}
	catch (e) {}
</script>
```

### Automatic iframe height adjustment ###

The parent page should use the following code to embed the iframed content.

```html
<iframe src="<iframed_src>" onload="this.style.height = (this.contentWindow.document.body.scrollHeight) + 'px';" scroll="auto"></iframe>
```

As soon as the page within the iframe finishes loading, the parent page adjusts the height of the iframe to the height of the iframed document. The iframe is configured to show scrollbars only when the iframed content does not fit in the available space. As soon as the iframe is resized, the content fits neatly and the scrollbars disappear.

There are a number of important caveats with this approach:

#### Outer margin fail ####

The iframed page must ensure that there are no margins between its body and its elements, as this breaks the accuracy of the height calculation in some browsers (Firefox, for the most part). If the calculation is incorrect, the scrollbars do not disappear. Note that it is not sufficient to just have a wrapper element without margins - all elements that are aligned with any edge of the page need to have no margin towards the edge.

#### Flashing scrollbar ####

It is possible that the iframe briefly displays a scrollbar until the resize occurs.

One way to avoid this behaviour is to disable the scrollbar for the iframe altogether (`scroll="no"`). However, this means that if the user has JavaScript disabled or if the height calculation fails for whatever reason, the iframed content will get cut off and becomes inaccessible.

Ultimately, the flashing scrollbar is one of the UX tradeoffs we need to accept when using an iframe.

