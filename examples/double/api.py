from tpasync.resources import BaseAsyncResource
from . import tasks


class DoubleResource(BaseAsyncResource):
    def async_post_list(self, request, **kwargs):
        number = request.POST['number']
        return tasks.double.delay(number)

    class Meta:
        resource_name = 'double'