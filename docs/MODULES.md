# Модули Фазы 6: AI, Прокси, Утилиты и десктоп-компаньоны

Эти модули разнородны: часть — веб-сервисы, часть — библиотеки/агенты, часть —
десктопные приложения. Поэтому интеграция у каждого своя.

## Веб-сервисы (за Traefik + SSO)

Сначала склонируйте исходники:
```bash
./scripts/init-vendor.sh
cp docker-compose.modules.yml.example docker-compose.modules.yml
# заполните env по README каждого репо, затем:
docker compose -f docker-compose.yml -f docker-compose.modules.yml \
  --profile core --profile ai --profile net up -d
```

### sub2api — единый AI API-gateway (`https://ai.${ROOT_DOMAIN}`)
- Консолидирует квоты Claude/OpenAI/Gemini в один API-ключ.
- Используется AI-функциями платформы (и внешними агентами: MobileAgent, openhuman).
- Env — из `tools/vendor/sub2api/.env.example`. Порт — см. репо.

### remnawave — панель прокси/egress (`https://proxy.${ROOT_DOMAIN}`)
- Управление Xray-прокси для контролируемого исходящего трафика разведки.
- Env — из `tools/vendor/remnawave/.env.sample`.
- ⚠️ Используйте прокси/egress только для авторизованных задач.

## Библиотеки / агенты (не отдельные сервисы)

### fingerprint-suite (анти-детект отпечатки)
- JS-библиотека Apify; используется **внутри** browser-worker автоматизации
  (Playwright/Puppeteer) для реалистичных отпечатков при веб-разведке.
- Интеграция: добавить `fingerprint-injector` + `fingerprint-generator` в
  npm-зависимости browser-воркера и инжектить в контекст браузера.

### MobileAgent (AI-управление мобильными GUI)
- Требует Android-устройство/эмулятор + ADB; запускается как спец-задача, а не
  всегда-онлайн сервис. Интеграция: отдельный воркер с ADB-доступом, ключи AI —
  через sub2api. Запускать точечно под конкретную задачу.

## Утилиты

### clifm (терминальный файловый менеджер)
- Уже установлен в образе **webterm** (профиль `terminal`).
- Доступ: `https://term.${ROOT_DOMAIN}` → команда `clifm` для работы с артефактами/евиденсом.

## Десктоп-компаньоны (клиентские приложения, не контейнеры)

Подключаются к платформе по API/ссылкам, ставятся на рабочую машину оператора:

| Приложение | Назначение | Связка с платформой |
|---|---|---|
| **openhuman** (Tauri/Rust) | персональный AI-ассистент | модели через sub2api; контекст из Core API |
| **superset-sh/superset** (Electron) | IDE для AI-агентов | разработка/расширение платформы |
| **free-claude-code** | доступ к Claude Code | dev-ассистент при доработке |
| **mattpocock/skills** | набор Claude-skills | подключить как skills в дев-окружении |

> Эти инструменты не разворачиваются на VPS — это клиентский слой. На платформе
> для них предусмотрены точки входа: AI-gateway (sub2api) и Core API.
