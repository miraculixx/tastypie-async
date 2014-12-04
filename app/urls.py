from django.conf.urls import patterns, include, url
from tastypie.api import Api
from tpasync.tests import EmptyTestResource, TestResource


tpa_api = Api(api_name='v1')
tpa_api.register(EmptyTestResource())
tpa_api.register(TestResource())


urlpatterns = patterns(
    '',
    url(r'^api/', include(tpa_api.urls))
)
