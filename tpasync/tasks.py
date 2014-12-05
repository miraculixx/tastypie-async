import time
from celery import task


@task
def successful_task():
    # We do extremely difficult and long computation here :-)
    time.sleep(3)
    return {'result': 'ok', 'id': 1}


@task
def list_task():
    return [{'result': 'ok', 'id': 1}, {'result': 'not bad', 'id': 2}]


@task
def failing_task():
    raise Exception('I failed miserably')