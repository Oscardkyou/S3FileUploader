# File Upload Service

## Описание

Веб-приложение для загрузки больших файлов (более 1.5 ГБ) на S3-подобный сервис через бэкенд-приложение.

## Установка и запуск

### Бэкенд

1. Создайте виртуальное окружение и установите зависимости:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r backend/requirements.txt
    ```

2. Запустите бэкенд:
    ```bash
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
    ```

### Фронтенд

Откройте `frontend/index.html` в браузере.

## Конфигурация

Настройте параметры подключения к S3 в `backend/main.py`:

```python
s3_client = boto3.client('s3', aws_access_key_id='YOUR_ACCESS_KEY', aws_secret_access_key='YOUR_SECRET_KEY', endpoint_url='https://your-s3-endpoint.com')
```

## Использование

1. Перейдите на страницу фронтенда.
2. Выберите файл для загрузки и нажмите кнопку "Upload".
3. Файл будет загружен на S3-подобный сервис через бэкенд-приложение.
