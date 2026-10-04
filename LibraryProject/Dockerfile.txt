FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install django Pillow
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
