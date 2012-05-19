from contextlib import contextmanager

from django.test import TestCase
from django.test.client import RequestFactory

from iframed.middleware import IframedMiddleware
from iframed import urlresolvers

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
    
    def test_process_request_match(self):
        settings = {
            'IFRAMED_MAPPINGS': [
                ('/appname/viewname', '/refererpath/'),
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

    def test_process_request_explicit_query_id(self):
        settings = {
            'IFRAMED_QUERY_ID': 'url',
            'IFRAMED_MAPPINGS': [
                ('/appname/viewname', '/refererpath/'),
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

class IframedReverseTest(TestCase):
    def setUp(self):
        urlresolvers = reload(urlresolvers)
        
