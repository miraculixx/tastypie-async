import time

from celery import shared_task


@shared_task
def successful_task():
    # We do extremely difficult and long computation here :-)
    time.sleep(3)
    return {'result': 'ok', 'id': 1}


@shared_task
def list_task():
    return [{'result': 'ok', 'id': 1}, {'result': 'not bad', 'id': 2}]


@shared_task
def failing_task():
    raise Exception('I failed miserably')

