import time

from tasks import crawl_all_corporates, test_mongodb_connection
from celery.result import GroupResult
from celery import Celery

celery = Celery('tasks')
celery.config_from_object('celery_config')

if __name__ == '__main__':
    # Test MongoDB connection
    test_result = test_mongodb_connection.delay()
    print("Testing MongoDB connection...")
    test_result.wait()
    print(test_result.get())

    # Trigger the main task
    result = crawl_all_corporates()
    print(result)






