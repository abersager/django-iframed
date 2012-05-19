from contextlib import contextmanager

from django.test import TestCase
from django.test.client import RequestFactory

from iframed.middleware import IframedMiddleware

class SettingDoesNotExist:
    pass

@contextmanager
def patch_settings(**kwargs):
    from django.conf import settings
    old_settings = []
    for key, new_value in kwargs.items():
        old_value = getattr(settings, key, SettingDoesNotExist)
        old_settings.append((key, old_value))
        setattr(settings, key, new_value)
    yield
    for key, old_value in old_settings:
        if old_value is SettingDoesNotExist:
            delattr(settings, key)
        else:
            setattr(settings, key, old_value)


class IframedMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
    def tearDown(self):
        pass
    
    def test_process_request_match(self):
        settings = {
            'IFRAMED_MAPPINGS': [
                ('/appname/viewname', '/refererpath'),
            ]
        }
        request = self.factory.get('/appnameignored/viewnameignored', **{
            'HTTP_REFERER': 'http://www.referer.com/refererpath/?id=/viewparams/moreparams'
        })
        expected_path_info = '/appname/viewname/viewparams/moreparams'
        with patch_settings(**settings):
            middleware = IframedMiddleware()
            middleware.process_request(request)
            
            self.assertEqual(request.path_info, expected_path_info)

    def test_process_request_no_mappings(self):
        settings = {
        }
        request = self.factory.get('/appnameoriginal/viewnameoriginal', **{
            'HTTP_REFERER': 'http://www.referer.com/refererpath/?id=/viewparams/moreparams'
        })
        expected_path_info = '/appnameoriginal/viewnameoriginal'
        with patch_settings(**settings):
            middleware = IframedMiddleware()
            middleware.process_request(request)
            
            self.assertEqual(request.path_info, expected_path_info)

    def test_process_request_aliased(self):
        settings = {
            'IFRAMED_ALIASES': {
                '/alternative_location': '/refererpath',
            },
            'IFRAMED_MAPPINGS': [
                ('/appname/viewname', '/refererpath'),
            ]
        }
        request = self.factory.get('/appnamehonoured/viewnamehonoured', **{
            'HTTP_REFERER': 'http://www.referer.com/alternative_location/?id=/viewparamsignored/moreparamsignored'
        })
        expected_path_info = '/appnamehonoured/viewnamehonoured'
        with patch_settings(**settings):
            middleware = IframedMiddleware()
            middleware.process_request(request)
            
            self.assertEqual(request.path_info, expected_path_info)

    def test_process_request_explicit_query_id(self):
        settings = {
            'IFRAMED_QUERY_ID': 'url',
            'IFRAMED_MAPPINGS': [
                ('/appname/viewname', '/refererpath'),
            ]
        }
        request = self.factory.get('/appnameignored/viewnameignored', **{
            'HTTP_REFERER': 'http://www.referer.com/refererpath/?url=/viewparams/moreparams'
        })
        expected_path_info = '/appname/viewname/viewparams/moreparams'
        with patch_settings(**settings):
            middleware = IframedMiddleware()
            middleware.process_request(request)
            
            self.assertEqual(request.path_info, expected_path_info)


# URLconf for IframedReverseTest
from django.conf.urls.defaults import *
urlpatterns = patterns('',
    url(r'^appname/viewname/(.*)$', 'test', name='test'),
)

from iframed import urlresolvers

class IframedReverseTest(TestCase):
    
    def setUp(self):
        self.factory = RequestFactory()
        
    def test_reverse_with_referer(self):
        settings = {
            'ROOT_URLCONF': 'iframed.tests',
            'IFRAMED_MAPPINGS': [
                ('/appname/viewname', '/refererpath'),
            ]
        }
        
        request = self.factory.get('/appnameignored/viewnameignored', **{
            'HTTP_REFERER': 'http://www.referer.com/refererpath/?id=/viewparams/moreparams'
        })
        expected_result = 'http://www.referer.com/refererpath?id=/param'
        
        with patch_settings(**settings):
            reload(urlresolvers)
            middleware = IframedMiddleware()
            middleware.process_request(request)
            result = urlresolvers.reverse('test', request=request,  args=['param'])
            self.assertEqual(result, expected_result)
        
    def test_reverse_without_mapping(self):
        settings = {
            'ROOT_URLCONF': 'iframed.tests',
            'IFRAMED_MAPPINGS': [
                ('/appname/viewname', '/refererpath'),
            ]
        }
        expected_result = '/appname/viewname/param'
        with patch_settings(**settings):
            reload(urlresolvers)
            result = urlresolvers.reverse('test',  args=['param'])
            self.assertEqual(result, expected_result)

    def test_reverse_without_mapping_using_default_base(self):
        settings = {
            'ROOT_URLCONF': 'iframed.tests',
            'IFRAMED_DEFAULT_BASE': 'http://parentdomain.com',
            'IFRAMED_MAPPINGS': [
                ('/appname/viewname', '/refererpath'),
            ]
        }
        expected_result = 'http://parentdomain.com/refererpath?id=/param'
        with patch_settings(**settings):
            reload(urlresolvers)
            result = urlresolvers.reverse('test', use_default_base=True,  args=['param'])
            self.assertEqual(result, expected_result)
    
    def test_reverse_with_rewrite(self):
        settings = {
            'ROOT_URLCONF': 'iframed.tests',
            'IFRAMED_REWRITES': {
                '/appname/viewname/': 'http://www.otherdomain/arbitrarypath/',
            },
            'IFRAMED_MAPPINGS': [
                ('/appname/viewname', '/refererpath'),
            ]
        }
        
        expected_result = 'http://www.otherdomain/arbitrarypath/'
        
        with patch_settings(**settings):
            reload(urlresolvers)
            result = urlresolvers.reverse('test', args=[''])
            self.assertEqual(result, expected_result)
        
