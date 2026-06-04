# Деплой Hacking-Aziral на сервер (за внешним NPM)

## Контекст

На сервере AZIRAL (46.225.166.18) уже работает Nginx Proxy Manager (NPM) на 80/443
вместе с десятками других сервисов. Поэтому Traefik платформы Hacking-Aziral
**не публикует портов наружу** — он живёт только в Docker-сети, а NPM проксирует
снаружи `cybersecurity.aziral.com` → внутрь к Traefik.

```
Internet → :443/NPM (TLS, LE) ─→ http://aziral-traefik:80 ─→ forward-auth → сервисы
```

## Что нужно сделать ДО запуска

### 1. DNS A-запись
В панели регистратора домена `aziral.com` добавь:
```
A   cybersecurity.aziral.com   46.225.166.18   TTL 300
```
Проверь распространение: `dig cybersecurity.aziral.com +short` → должен вернуть IP.

### 2. Свободное место и RAM
Платформа требует ≈4 GB RAM и 20 GB диска под образы и данные.
На сервере сейчас: 30 GB RAM (13 свободно), 226 GB диска (120 свободно) — норм.

## Деплой (с локали — одной командой синхронизируем код)

```bash
# 1. На локалке: запушить актуальное состояние через rsync
rsync -avz --exclude='.git' --exclude='.env' --exclude='*.db' --exclude='node_modules' \
  --exclude='__pycache__' --exclude='.venv' --exclude='htmlcov' --exclude='dist' \
  /Users/mpmr/Documents/projects/КИБЕРБЕЗОПАСНОСТЬ/hacking-aziral/ \
  aziral:/home/olzhas/hacking-aziral/
```

## Развёртывание на сервере

```bash
ssh aziral
cd ~/hacking-aziral

# 1. Сгенерировать секреты
./scripts/gen-secrets.sh

# 2. Задать production-домен в .env
sed -i "s|^ROOT_DOMAIN=.*|ROOT_DOMAIN=cybersecurity.aziral.com|" .env

# 3. Применить домен в конфиги file-provider и blueprints
./scripts/configure-domain.sh

# 4. Поднять ядро (через prod-оверлей: без публичных портов)
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --profile core up -d
```

## Подключить Traefik к сети NPM

Чтобы NPM мог достучаться до контейнера Traefik:

```bash
# Узнать имя сети, в которой сидит NPM (контейнер fenix-nginx):
NPM_NET=$(docker inspect fenix-nginx -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' | head -1)
echo "NPM network: $NPM_NET"

# Подключить Traefik к этой сети
docker network connect "$NPM_NET" aziral-traefik-1
```

## Настроить proxy host в NPM

Открой `http://46.225.166.18:81` → **Proxy Hosts → Add Proxy Host**:

| Поле | Значение |
|---|---|
| Domain Names | `cybersecurity.aziral.com` |
| Scheme | `http` |
| Forward Hostname / IP | `aziral-traefik-1` |
| Forward Port | `80` |
| Block Common Exploits | ✓ |
| Websockets Support | ✓ |

**SSL tab**:
- SSL Certificate: **Request a new SSL Certificate** (Let's Encrypt)
- Force SSL: ✓
- HTTP/2 Support: ✓
- Email: твой email

Сохрани. NPM получит серт от Let's Encrypt и начнёт проксировать.

## Войти

`https://cybersecurity.aziral.com` → форма Authentik:
- **user**: `akadmin`
- **password**: `grep AUTHENTIK_BOOTSTRAP_PASSWORD ~/hacking-aziral/.env`

## Поднять остальные модули

```bash
# Аналитика
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --profile core --profile analytics up -d superset

# Применить аналитические VIEW
docker compose exec -T postgres psql -U aziral -d aziral_core \
  < analytics/superset/views.sql

# Автоматизация
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --profile core --profile automation up -d activepieces cronicle

# Web-terminal
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --profile core --profile terminal up -d webterm

# Spiderfoot
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --profile core --profile osint up -d spiderfoot
```

Все они слушают только на edge-сети и доступны через тот же Traefik+SSO.
Снаружи доступен **только один URL** — `cybersecurity.aziral.com`.

## Обновление

```bash
# На локалке — повторить rsync
rsync -avz ... aziral:/home/olzhas/hacking-aziral/

# На сервере — пересоздать только изменённые
ssh aziral 'cd ~/hacking-aziral && docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile core up -d --build'
```

## Откат / удаление

```bash
ssh aziral 'cd ~/hacking-aziral && docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v'
# в NPM: удалить proxy host для cybersecurity.aziral.com
# в DNS: удалить A-запись (или оставить — не используется)
```
