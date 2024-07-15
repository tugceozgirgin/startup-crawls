from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
from celery.result import AsyncResult
from data_fetch import fetch_all_corporates

app = FastAPI()

@app.get("/")
async def root():
    content = """
    <html>
        <head>
            <title>Corporate Fetch</title>
        </head>
        <body>
            <h1>Hello World</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=content)

@app.post("/fetch-corporates")
def fetch_corporates(background_tasks: BackgroundTasks):
    task = fetch_all_corporates.apply_async()
    background_tasks.add_task(check_task_status, task.id)
    return {"message": "Fetching corporate details. Please check back later.", "task_id": task.id}

@app.get("/status/{task_id}")
def get_status(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.state == 'PENDING':
        return {"status": "Pending..."}
    elif task_result.state == 'PROGRESS':
        return {"status": "In progress..."}
    elif task_result.state == 'SUCCESS':
        return {"status": "Completed", "result": task_result.result}
    else:
        return {"status": task_result.state}

def check_task_status(task_id: str):
    result = AsyncResult(task_id)
    if result.state == 'SUCCESS':
        print("Task completed successfully!")
    elif result.state == 'FAILURE':
        print("Task failed.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




