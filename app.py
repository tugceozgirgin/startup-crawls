import logging

from fastapi import FastAPI
from celery import Celery
from celery import group
from data_fetch import get_corporates
from tasks import fetch_details_task, initialize_task

app = FastAPI()

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

def crawl_all_corporates():
    corporates = get_corporates(API_URL, HEADERS)
    detail_tasks = group(fetch_details_task.s(corporate['id']) for corporate in corporates)
    result = detail_tasks.apply_async()

@app.post("/crawl_corporates")
async def start_crawl():
    try:
        initialize_task.delay()

        return {"message": "Crawling corporates initiated."}
    except Exception as e:
        logging.error(f"Failed to start crawling corporates: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
