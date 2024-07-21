import logging

from bson import ObjectId
from fastapi import FastAPI
from mongo import mongo_client
from tasks import initialize_task

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

@app.post("/crawl_corporates")
async def start_crawl():
    try:
        analysis_id = initialize_task()
        return {"message": "Crawling corporates initiated.", "analysis_id": analysis_id}
    except Exception as e:
        logging.error(f"Failed to start crawling corporates: {str(e)}")
        return {"error": str(e)}


@app.get("/get-results/{analysis_id}")
async def get_results(analysis_id: str):
    try:
        results_db = mongo_client["results_db"]["results"]
        result_entries = list(results_db.find({"_id": ObjectId(analysis_id)}))

        if not result_entries:
            return {"message": "Analysis_id not found."}
        if result_entries[0]["status"] == "PENDING":
            return {"message": "Task is pending."}
        elif result_entries[0]["status"] == "SUCCESS":
            return {"results": result_entries[0]["clusters"]}

    except Exception as e:
        logging.error(f"Failed to fetch results: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
