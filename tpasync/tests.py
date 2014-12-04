import time
from django import http
from tpasync.resources import BaseAsyncResource
from tastypie.test import ResourceTestCase
from . import tasks


class EmptyTestResource(BaseAsyncResource):
    class Meta:
        resource_name = 'empty'


class TestResource(BaseAsyncResource):
    class Meta:
        include_resource_uri = False
        resource_name = 'test'
        fields = 'result',

    def async_get_detail(self, **kwargs):
        return tasks.successful_task.apply_async()

    def async_get_list(self, **kwargs):
        pass

    def async_post_detail(self, **kwargs):
        return tasks.failing_task.apply_async()


class AsyncResourceTest(ResourceTestCase):
    def setUp(self):
        super(AsyncResourceTest, self).setUp()
        self.empty_resource = EmptyTestResource()
        self.test_resource = TestResource()

    def test_empty_methods(self):
        for verb in ('get', 'put', 'post', 'delete', 'patch'):
            for suffix in ('detail', 'list'):
                request = http.HttpRequest()
                self.assertHttpNotImplemented(
                    getattr(
                        self.empty_resource,
                        '_'.join((verb, suffix)))(request))
        response = self.api_client.get('/api/v1/empty/')
        self.assertHttpNotImplemented(response)

    def test_successful_task(self):
        # Method returns None, should give HTTP bad request
        response = self.api_client.get('/api/v1/test/')
        self.assertHttpBadRequest(response)

        # Send task request and get its Location header
        result = self.api_client.get('/api/v1/test/1/')
        self.assertHttpAccepted(result)
        state_url = result['Location']

        # Location should contain state URL, but not result_uri
        response = self.api_client.get(state_url)
        self.assertHttpOK(response)
        data = self.deserialize(response)
        self.assertEqual(data['state'], 'PENDING')
        self.assertNotIn('result_uri', data)
        # Wait 4 seconds and retry. This time result_uri should be ready
        time.sleep(4)
        response = self.api_client.get(state_url)
        self.assertHttpOK(response)
        data = self.deserialize(response)
        self.assertIn('result_uri', data)
        self.assertEqual(data['state'], 'SUCCESS')
        # Go to result page.
        response = self.api_client.get(data['result_uri'])
        self.assertHttpOK(response)
        data = self.deserialize(response)
        self.assertEqual(data['result'], 'ok')

        # We can't delete task that is competed
        response = self.api_client.delete(state_url)
        self.assertHttpBadRequest(response)

    def test_canceling_task(self):
        # Method returns None, should give HTTP bad request
        response = self.api_client.get('/api/v1/test/')
        self.assertHttpBadRequest(response)

        # Send task request and get its Location header
        result = self.api_client.get('/api/v1/test/1/')
        self.assertHttpAccepted(result)
        state_url = result['Location']

        # We can delete the task until it has finisheed executing
        time.sleep(2)
        response = self.api_client.delete(state_url)
        self.assertHttpGone(response)

    def test_failing_task(self):
        # Method returns None, should give HTTP bad request
        response = self.api_client.get('/api/v1/test/')
        self.assertHttpBadRequest(response)

        # Send task request and get its Location header
        result = self.api_client.post('/api/v1/test/1/')
        self.assertHttpAccepted(result)
        state_url = result['Location']
        # This request will have failed in 1 second. Location should contain
        # result_uri.
        time.sleep(1)
        response = self.api_client.get(state_url)
        self.assertHttpOK(response)
        data = self.deserialize(response)
        self.assertEqual(data['state'], 'FAILURE')
        self.assertIn('result_uri', data)
        result_url = data['result_uri']
        # Get result, check error message.
        response = self.api_client.get(result_url)
        self.assertHttpOK(response)
        data = self.deserialize(response)
        self.assertEqual(data['error'], 'I failed miserably')

        response = self.api_client.delete(state_url)
        self.assertHttpBadRequest(response)