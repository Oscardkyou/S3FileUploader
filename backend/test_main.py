import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from dotenv import load_dotenv

client = TestClient(app)


@pytest.fixture
def setup_env(monkeypatch):
    load_dotenv()  # Загрузка переменных окружения из .env файла
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not aws_access_key_id or not aws_secret_access_key:
        raise ValueError(
            "AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY not set in .env file"
        )

    aws_region = os.getenv("AWS_REGION")
    aws_bucket = os.getenv("AWS_BUCKET")

    if not aws_region or not aws_bucket:
        raise ValueError("AWS_REGION or AWS_BUCKET not set in .env file")

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", aws_access_key_id)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", aws_secret_access_key)
    monkeypatch.setenv("AWS_REGION", aws_region)
    monkeypatch.setenv("AWS_BUCKET", aws_bucket)


def test_home(setup_env):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from file-upload 😄👋"}


def test_upload(setup_env):
    file_path = "backend/testfile.png"  # Убедитесь, что файл существует по этому пути
    with open(file_path, "rb") as file:
        response = client.post(
            "/upload", files={"file": ("testfile.png", file, "image/png")}
        )
    assert response.status_code == 200
    json_response = response.json()
    assert "file_name" in json_response


def test_download(setup_env):
    # This assumes that the file was uploaded previously
    file_name = "testfile.png"
    response = client.get(f"/download?file_name={file_name}")
    assert response.status_code == 200
    assert (
        response.headers["Content-Disposition"] == f"attachment; filename={file_name}"
    )
