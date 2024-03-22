import io
import os
import uuid

from fastapi import FastAPI, UploadFile, File
from minio import Minio
from celery import Celery
from celery.result import AsyncResult

# Initialize Celery
broker_url = os.getenv('CELERY_BROKER_URL', 'pyamqp://guest@localhost:5672//')
backend_url = os.getenv('CELERY_BACKEND_URL', 'rpc://')

celery_app = Celery('tasks', broker=broker_url, backend=backend_url)

# Initialize Minio client
minio_client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    secure=False
)
bucket_name = os.getenv("MINIO_BUCKET_NAME", "defaultbucket")

# Initialize FastAPI
app = FastAPI()


@app.post("/transcribe/")
async def transcribe_file(file: UploadFile = File(...)):
    
    object_name = f"{uuid.uuid4()}__{file.filename}"
    file_data = await file.read()

    create_bucket_if_not_exists(bucket_name)

    minio_client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=io.BytesIO(file_data),
        length=len(file_data),
        content_type=file.content_type
    )

    # Trigger Celery task
    task = celery_app.send_task('tasks.process_audio_task', args=[object_name])
    return {"filename": file.filename, "task_id": task.id, "object_name": object_name}


@app.get("/task/status/{task_id}")
async def get_job_status(task_id):
    task = AsyncResult(task_id, app=celery_app)
    if not task.ready():
        return {"status": "PENDING"}
    else:
        return {"status": task.status, "result": task.result}

def create_bucket_if_not_exists(bucket_name):
    if not minio_client.bucket_exists(bucket_name=bucket_name):
        minio_client.make_bucket(bucket_name=bucket_name)
        minio_client.set_bu
        print("Created bucket")

