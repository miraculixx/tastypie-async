## tastypie-async

State-of-the art async REST APIs for [django tastypie](https://github.com/django-tastypie/django-tastypie).

tastypie-async follows the [recommended practice](http://restful-api-design.readthedocs.io/en/latest/methods.html#asynchronous-requests) for async REST APIs, which is to return 202 CREATED on task submission, and issue a 303 SEE OTHER on status requests when the result is available. 

### Hello world

In good tastypie tradition, API implementation is [straight forward](https://github.com/miraculixx/tastypie-async/blob/master/examples/double/api.py):

```python
from tpasync.resources import AsyncResourceMixin
import myapp.tasks as tasks

# resources.py
# -- define the resource
class DoubleResource(AsyncResourceMixin, Resource):
    def async_get_list(self, request, **kwargs):
        number = request.GET['foo']
        return tasks.double.delay(foo)
    
    class Meta:
        resource_name = 'double'
```

Adding the API to your Django app is the same as with any tastypie API:

```python
# -- register
api = Api(api_name='v1')
api.register(DoubleResouce())

# urls.py
urlpatterns += [
    r('^api/', include(api.urls),
]
``` 


The above example provides the `/api/v1/double/` URL supporting async `GET` requests:

``` 
# submits the celery task and returns a state location
GET /api/v1/foo/?foo=1
Status: 202 ACCEPTED
Location:/api/v1/double/state/30049f59-b619-4890-a1eb-d53b245797d1/
````

### Getting results

1.  query the state to get updates

    ```
    GET /api/v1/double/state/30049f59-b619-4890-a1eb-d53b245797d1/
    Status: 200 OK
    {  
       "id":"7fbd961a-75d8-4aae-bd41-64296de661fa",
       "resource_uri":"/api/v1/double/state/7fbd961a-75d8-4aae-bd41-64296de661fa/",
       "state":"PENDING"
    }
    ```
    
2. when the result is ready it will be notified in the state response

    ```
    GET /api/v1/double/state/30049f59-b619-4890-a1eb-d53b245797d1/
    Status: 200 OK
    {  
       "id":"394daac4-3daa-4a0f-87b8-f9e2c8c73749",
       "resource_uri":"/api/v1/double/state/394daac4-3daa-4a0f-87b8-f9e2c8c73749/",
       "result_uri":"/api/v1/double/result/394daac4-3daa-4a0f-87b8-f9e2c8c73749/",
       "state":"SUCCESS"
    }
    ```
    
3. get results. this returns whatever result was provided by the celery task, serialized by tastypie as usual:

    ```
    GET http://localhost:8001/api/v1/double/result/394daac4-3daa-4a0f-87b8-f9e2c8c73749/
    Status: 200 OK
    {
     "result": 2
    }
    ```
    
4. cancel tasks. you may also choose to cancel a task

    ```
    DELETE http://localhost:8001/api/v1/double/state/7fbd961a-75d8-4aae-bd41-64296de661fa/
    Status: 410 Gone
    ```

### Implementing operations

tastypie-async supports the usual tastypie operations, `GET/PUT/POST/DELETE` for list and detail. To implement override the respective `async_<method>` operation:

* `GET /` => `async_get_list`
* `GET /<pk>/` => `async_get_detail`
* `POST /` => `async_post_list`
* `POST /<pk>/` => `async_post_detail`
* `PUT /` => `async_put_list`
* `PUT /<pk>/` => `async_put_detail`
* `DELETE /` => `async_delete_list`
* `DELETE /<pk>/` => `async_delete_detail`
* `PATCH /` => `async_patch_list`
* `PATCH /<pk>/` => `async_patch_detail`

Implementation of any of these methods is straight forward, just return the `AsyncResult` returned by the celery task:

```
def async_get_list(request, **kwargs):
    return myapp.tasks.double.delay(requests.GET.get('foo'))
```

Task implementation is the same as with any other Celery task:

```python
# tasks.py
def double(number):
   return number * 2
```

Note that it is the responsibility of the task to execute actions that correspond to the API method called, 
tastypie-async is only the broker between the API call and Celery.

### Installation

Just add `tpasync` to `INSTALLED_APPS`:

```python
# settings.py

INSTALLED_APPS = (
    ...
    'tastypie',
    'tpasync',
    ...
)
```

### Why not use the Celery REST API?

tastypie-async uses Celery as the execution engine. Any AsyncResource submits tasks to Celery 
the same way any Celery task is executed. While Celery provides a REST API itself, 
[Celery webhooks](http://docs.celeryproject.org/en/latest/userguide/remote-tasks.html), it is less flexible than tastypie-async and has a few other drawbacks. For example, the tasks submitted via Celery need to be aware of their use as a REST API, which means they are hard to be reused outside of celery webhooks. In contrast, tasks used in a `AsyncResource` 
remain unaware of their use as a REST API, seperation of concerns is thus maintained.

Also adding authentication, authorization and throttling  to an AsyncResource is straight forward -- it works
the same as with any tastypie Resource because the method dispatcher is the same. 

### License

see the `LICENSE` file
