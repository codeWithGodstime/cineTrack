FROM python:alpine3.20

RUN apk update && apk upgrade

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Expose the port Gunicorn will run on
EXPOSE 8000

# Start the application using Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "django_project.wsgi:application"]