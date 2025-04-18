build:
	docker-compose build

up:
	docker-compose up

down:
	docker-compose down

restart:
	docker-compose down && docker-compose up -d

logs:
	docker-compose logs -f

shell:
	docker-compose exec django bash

migrate:
	docker-compose exec django python manage.py migrate

createsuperuser:
	docker-compose exec django python manage.py createsuperuser

restart-celery:
	docker restart celery_worker celery_beat
