.PHONY: help secrets up down logs test build core

help:
	@echo "Hacking-Aziral — команды:"
	@echo "  make secrets   — сгенерировать .env с секретами"
	@echo "  make core      — поднять ядро (Traefik, SSO, БД, Core)"
	@echo "  make up        — поднять всё (основные профили)"
	@echo "  make up-extra  — добавить расширения (pdf, webui, monitoring)"
	@echo "  make down      — остановить всё"
	@echo "  make logs      — логи"
	@echo "  make test      — тесты backend"

secrets:
	./scripts/gen-secrets.sh

core:
	docker compose --profile core up -d --build

up:
	docker compose --profile core --profile osint --profile automation \
	  --profile analytics --profile ai --profile net --profile terminal up -d --build

up-extra:
	docker compose \
	  -f docker-compose.yml -f docker-compose.extra-modules.yml \
	  --profile core --profile osint --profile automation \
	  --profile analytics --profile ai --profile net --profile terminal \
	  --profile pdf --profile webui --profile monitoring up -d --build

down:
	docker compose --profile core --profile osint --profile automation \
	  --profile analytics --profile ai --profile net --profile terminal down

logs:
	docker compose logs -f --tail=100

test:
	cd core/backend && . .venv/bin/activate && python -m pytest -q

build:
	docker compose --profile core build
