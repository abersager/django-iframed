import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='django-iframed',
    version='0.1',
    description='Seamless Django iframe integration',
    classifiers = [ 'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    author='Oliver Spindler',
    author_email='os@oliverspindler.com',
    url='http://github.com/abersager/django-iframed',
    packages=['iframed', 'iframed.templatetags'],
    long_description=read('README.md'),
)
