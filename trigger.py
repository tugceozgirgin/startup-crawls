from tasks import crawl_all_corporates

if __name__ == '__main__':
    result = crawl_all_corporates.delay()
    print("Task triggered. Check the Celery logs for progress.")
