import os
from uuid import uuid4
import boto3
from botocore.exceptions import ClientError
import magic
import uvicorn
from fastapi import FastAPI, HTTPException, Response, UploadFile, status, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
AWS_BUCKET = os.getenv('AWS_BUCKET')

KB = 1024
MB = 1024 * KB
GB = 1024 * MB

SUPPORTED_FILE_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'application/pdf': 'pdf'
}

# S3 Configuration
s3_client = boto3.client('s3', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

app = FastAPI()

# Middleware для подключения CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для обслуживания статических файлов
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def home():
    return FileResponse('frontend/index.html')

def s3_upload(contents: bytes, key: str):
    logger.info(f'Uploading {key} to S3')
    try:
        s3_client.put_object(Bucket=AWS_BUCKET, Key=key, Body=contents)
    except ClientError as err:
        logger.error(f'Failed to upload {key}: {err}')
        raise HTTPException(status_code=500, detail='Failed to upload file')

def s3_download(key: str):
    try:
        response = s3_client.get_object(Bucket=AWS_BUCKET, Key=key)
        return response['Body'].read()
    except ClientError as err:
        logger.error(f'Failed to download {key}: {err}')
        raise HTTPException(status_code=404, detail='File not found')

@app.post("/upload")
async def upload(file: UploadFile):
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No file found!!'
        )

    contents = await file.read()
    size = len(contents)

    if not 0 < size <= 2 * GB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Supported file size is 0 - 2 GB'
        )

    file_type = magic.from_buffer(buffer=contents, mime=True)
    if file_type not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Unsupported file type: {file_type}. Supported types are {SUPPORTED_FILE_TYPES}'
        )
    file_name = f'{uuid4()}.{SUPPORTED_FILE_TYPES[file_type]}'
    s3_upload(contents=contents, key=file_name)
    return {'file_name': file_name}

@app.post("/upload_chunk")
async def upload_chunk(file: UploadFile, chunk_number: int = Form(...), total_chunks: int = Form(...), file_id: str = Form(...)):
    temp_dir = 'temp_uploads'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    temp_file_path = os.path.join(temp_dir, f'{file_id}_{chunk_number}')

    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(await file.read())

    if chunk_number == total_chunks:
        final_file_path = os.path.join(temp_dir, f'{file_id}_final')
        with open(final_file_path, 'wb') as final_file:
            for i in range(1, total_chunks + 1):
                chunk_path = os.path.join(temp_dir, f'{file_id}_{i}')
                with open(chunk_path, 'rb') as chunk_file:
                    final_file.write(chunk_file.read())
                os.remove(chunk_path)

        with open(final_file_path, 'rb') as final_file:
            contents = final_file.read()
            file_type = magic.from_buffer(buffer=contents, mime=True)
            if file_type not in SUPPORTED_FILE_TYPES:
                os.remove(final_file_path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Unsupported file type: {file_type}. Supported types are {SUPPORTED_FILE_TYPES}'
                )
            file_name = f'{uuid4()}.{SUPPORTED_FILE_TYPES[file_type]}'
            s3_upload(contents=contents, key=file_name)
            os.remove(final_file_path)
            return {'file_name': file_name}

    return {'message': 'Chunk uploaded successfully'}

@app.get("/download")
async def download(file_name: str):
    if not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No file name provided'
        )

    contents = s3_download(key=file_name)
    return Response(
        content=contents,
        headers={
            'Content-Disposition': f'attachment; filename={file_name}',
            'Content-Type': 'application/octet-stream',
        }
    )

if __name__ == '__main__':
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
