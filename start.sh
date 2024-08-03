#!/bin/bash

# Активировать виртуальное окружение
source venv/bin/activate

# Запустить сервер
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
