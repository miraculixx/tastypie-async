from celery.result import AsyncResult
from django.conf.urls import url
from tastypie import resources, http, utils


class AsyncResourceMixin(object):
    def async_get_detail(self, request, **kwargs):
        raise NotImplementedError

    def async_post_detail(self, request, **kwargs):
        raise NotImplementedError

    def async_put_detail(self, request, **kwargs):
        raise NotImplementedError

    def async_delete_detail(self, request, **kwargs):
        raise NotImplementedError

    def async_patch_detail(self, request, **kwargs):
        raise NotImplementedError

    def async_get_list(self, request, **kwargs):
        raise NotImplementedError

    def async_post_list(self, request, **kwargs):
        raise NotImplementedError

    def async_put_list(self, request, **kwargs):
        raise NotImplementedError

    def async_delete_list(self, request, **kwargs):
        raise NotImplementedError

    def async_patch_list(self, request, **kwargs):
        raise NotImplementedError

    def async_state(self, request, task_id, **kwargs):
        """
        Task state.

        If request method is GET, it returns a JSON dict with state. If task
        has completed, that dict also contains ``result_uri`` entry.

        If request method is DELETE and task hasn't run yet, it revokes this
        task. See http://celery.readthedocs.org/en/latest/userguide/workers.html#persistent-revokes
        for details about running workers with persitent revokes. If task can't be
        revoked (is in progress or finished), we return response with HTTP Bad
        Request state.

        Other methods are forbidden.
        """
        task = AsyncResult(task_id)
        if request.method == 'GET':
            data = {
                'state': task.state, 'id': task.id,
                'resource_uri': request.get_full_path()}
            if task.ready():
                data['result_uri'] = self._build_reverse_url(
                    'api_async_result',
                    kwargs={
                        'api_name': self._meta.api_name,
                        'resource_name': self._meta.resource_name,
                        'task_id': task_id})
            return self.create_response(request, data)
        elif request.method == 'DELETE':
            if not task.ready():
                try:
                    task.revoke(terminate=True)
                    return http.HttpGone()
                except Exception, e:
                    pass
            return http.HttpBadRequest()
        else:
            return http.HttpForbidden()

    def async_result(self, request, task_id, **kwargs):
        """
        Task results.

        If request is ready, return Http 200 response with serialized data.

        If request is not ready (or doesn't exist - we can't tell this),
        return Http 404 Not Found.
        """
        task = AsyncResult(task_id)
        if task.ready():
            try:
                result = task.get()
            except Exception, error:
                result = {'error': unicode(error)}

            if isinstance(result, http.HttpResponse):
                return result
            elif isinstance(result, basestring):
                return http.HttpResponse(result)
            elif isinstance(result, list):
                objects = result
                sorted_objects = self.apply_sorting(
                    objects, options=request.GET)

                paginator = self._meta.paginator_class(
                    request.GET, sorted_objects,
                    resource_uri=self.get_resource_uri(),
                    limit=self._meta.limit, max_limit=self._meta.max_limit,
                    collection_name=self._meta.collection_name)
                to_be_serialized = paginator.page()

                # Dehydrate the bundles in preparation for serialization.
                bundles = []

                for obj in to_be_serialized[self._meta.collection_name]:
                    bundle = self.build_bundle(obj=obj, request=request)
                    bundles.append(self.full_dehydrate(bundle, for_list=True))

                to_be_serialized[self._meta.collection_name] = bundles
                to_be_serialized = self.alter_list_data_to_serialize(
                    request, to_be_serialized)
                return self.create_response(request, to_be_serialized)
            else:
                bundle = self.build_bundle(obj=result, request=request)
                bundle = self.full_dehydrate(bundle)
                bundle = self.alter_detail_data_to_serialize(request, bundle)
                return self.create_response(request, bundle)
        else:
            return http.HttpNotFound()

    def dehydrate(self, bundle):
        bundle.data = bundle.obj
        return bundle

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/state/(?P<task_id>[\w\-]{36})%s$" % (
                    self._meta.resource_name, utils.trailing_slash()),
                self.wrap_view('async_state'), name="api_async_state"),
            url(
                r"^(?P<resource_name>%s)/result/(?P<task_id>[\w\-]{36})%s$" % (
                    self._meta.resource_name, utils.trailing_slash()),
                self.wrap_view('async_result'), name="api_async_result")
        ]

    def _async_method(method):
        """
        This is a wrapper that's used to generate methods like
        VERB_KIND using hooks named async_VERB_KIND.
        """
        def inner(self, request, **kwargs):
            """
            Handle ``{method}`` request.

            Implement ``async_{method} to add custom request, returning
            celery.result.AsyncResult. If it returns None, HttpBadRequest
            is returned from this method. If you don't implement the
            custom method, it will return HttpNotImplemented.
            """
            try:
                result = getattr(self, 'async_' + method)(
                    request, **self.remove_api_resource_names(kwargs))
                if result is None:
                    return http.HttpBadRequest()
            except NotImplementedError:
                return http.HttpNotImplemented()

            if isinstance(result, AsyncResult):
                response = http.HttpAccepted()
                response['Location'] = self._build_reverse_url(
                    'api_async_state',
                    kwargs={
                        'api_name': self._meta.api_name,
                        'resource_name': self._meta.resource_name,
                        'task_id': result.id})
                return response
            else:
                return result
        inner.__doc__ = inner.__doc__.format(method=method)
        return inner

    get_detail = _async_method('get_detail')
    put_detail = _async_method('put_detail')
    post_detail = _async_method('post_detail')
    delete_detail = _async_method('delete_detail')
    patch_detail = _async_method('patch_detail')
    get_list = _async_method('get_list')
    put_list = _async_method('put_list')
    post_list = _async_method('post_list')
    delete_list = _async_method('delete_list')
    patch_list = _async_method('patch_list')


class BaseAsyncResource(AsyncResourceMixin, resources.Resource):
    pass