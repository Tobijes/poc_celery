from celery import Celery
from minio import Minio
from faster_whisper import WhisperModel
import os

# Initialize Celery with environment variables for broker and backend
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

# Initialize Whisper model
model_size = "large-v3"
model = WhisperModel(model_size, device="cpu", compute_type="int8", download_root="models", local_files_only=True)

@celery_app.task
def process_audio_task(object_name):

    file_path = f"/tmp/{object_name}"
    
    response = minio_client.fget_object(
        bucket_name=bucket_name,
        object_name=object_name,
        file_path=file_path
    )
    content_type = response.content_type
    print(f"Received task with content type: {content_type}")

    segments, info = model.transcribe(file_path, beam_size=5)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    return True
