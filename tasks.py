from data_fetch import get_corporates, fetch_corporate_details
import os
from celery import Celery
from celery import group
import logging

celery = Celery('tasks')
celery.config_from_object('celery_config')

API_URL = 'https://ranking.glassdollar.com/graphql'

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
    'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.188 Safari/537.36 CrKey/1.54.250320',
    'Origin': 'https://ranking.glassdollar.com',
    'Referer': 'https://ranking.glassdollar.com/',
}

logging.basicConfig(level=logging.INFO)

@celery.task
def fetch_details_task(corporate_id):
    logging.info(f"Fetching details for corporate ID: {corporate_id}")
    details = fetch_corporate_details(API_URL, HEADERS, corporate_id)
    return details

@celery.task
def crawl_all_corporates():
    corporates = get_corporates(API_URL, HEADERS)
    logging.info(f"Fetched corporate ids amk.")
    detail_tasks = group(fetch_details_task.s(corporate['id']) for corporate in corporates)
    detail_tasks.apply_async()




