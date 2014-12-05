'''
Created on Dec 3, 2014

@author: Stas Shtin <antisvin@gmail.com>
@author: Patrick Senti <miraculixx@gmx.ch>
'''
import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
#os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='tastypie-async',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    license='commercial',  # example license
    description='Asyncronous resources for tastypie',
    long_description=README,
    url='http://www.shrebo.com/',
    author='Stanislav Shtin',
    author_email='antisvin@gmail.com',
    maintainer='Patric Senti',
    maintainer_email='miraculixx@gmx.ch',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # replace these appropriately if you are using Python 3
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'Django==1.6',
        'django-tastypie',
        'South==1.0',
        'Celery==3.1.16',
        'pytz',
    ],
    dependency_links=[
    ]
)

