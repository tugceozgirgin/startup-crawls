# Celery configuration
broker_url = 'amqp://guest:guest@rabbit:5672'
result_backend = 'mongodb://mongodb:27017/celery_backend'
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True
