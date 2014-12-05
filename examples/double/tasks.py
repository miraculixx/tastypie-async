import time
from celery import task


@task
def double(number):
    time.sleep(5)
    # Just 5 seconds of extremely hard computation, and...
    return {'result': int(number) * 2}