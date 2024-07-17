from data_fetch import get_corporates, fetch_corporate_details
import os
from celery import Celery, chord
from celery import group
import logging
from mongo import mongo_client
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

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
def initialize_task():
    corporates = get_corporates(API_URL, HEADERS)
    detail_tasks = group(fetch_details_task.s(corporate['id']) for corporate in corporates)
    workflow = chord(detail_tasks, analysis_task.s())
    workflow.apply_async()


@celery.task
def fetch_details_task(corporate_id):
    logging.info(f"Fetching details for corporate ID: {corporate_id}")
    details = fetch_corporate_details(API_URL, HEADERS, corporate_id)
    inserted = mongo_client["db"]["corporates"].insert_one(jsonable_encoder(details))
    return str(inserted.inserted_id)

@celery.task
def test_mongodb_connection():
    return "MongoDB connection is successful!"

@celery.task
def analysis_task(corporate_ids):
    corporates = list(mongo_client["db"]["corporates"].find(
        {'_id': {'$in': [ObjectId(_id) for _id in corporate_ids]}}
    ))
    print(f"CORPORATES: {corporates}")


