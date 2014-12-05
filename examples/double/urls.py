from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from tastypie.api import Api
from . import api


demo_api = Api(api_name='v1')
demo_api.register(api.DoubleResource())


urlpatterns = patterns(
    '',
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^api/', include(demo_api.urls))
)
