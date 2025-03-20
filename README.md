# serve-well

Django with Docker, Redis, and Celery

---

## Prerequisites

Ensure you have the following installed on your system:

- **Docker**
- **Docker Compose**

---

## Getting Started

### Build the Project
```bash
docker-compose build
```

### Start the Project
```bash
docker-compose up
```

### Stop the Project
```bash
docker-compose down
```

### Restart the Project
```bash
docker-compose down && docker-compose up
```

### View Logs
```bash
docker-compose logs
```

### Access Django Shell
```bash
docker-compose exec web python manage.py shell
```

---

## Database Migrations

### Apply Migrations
```bash
docker-compose exec web python manage.py migrate
```

### Create a Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

---

## Environment Variables

Ensure you configure the following environment variables before running the project:

- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`

---

## Running Celery

To start Celery workers, use the following command:
```bash
docker-compose exec web celery -A your_project_name worker --loglevel=info
```

---

## Notes

- Replace `your_project_name` with the actual Django project name when running Celery commands.
- The `DJANGO_SECRET_KEY` should be changed to a secure value in production.

---

## License



