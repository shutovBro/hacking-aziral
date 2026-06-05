// Единая точка доступа ко всем модулям платформы (поддомены за SSO).

interface Module {
  name: string;
  desc: string;
  sub: string;
  group: string;
}

const MODULES: Module[] = [
  { name: "SpiderFoot", desc: "OSINT-автоматизация, 200+ модулей", sub: "spiderfoot", group: "OSINT" },
  { name: "Web Terminal", desc: "recon-ng, hackingtool, clifm", sub: "term", group: "OSINT" },
  { name: "Superset", desc: "Аналитика и дашборды", sub: "superset", group: "Аналитика" },
  { name: "Activepieces", desc: "No-code плейбуки", sub: "flows", group: "Автоматизация" },
  { name: "Cronicle", desc: "Расписания сканов", sub: "cron", group: "Автоматизация" },
  { name: "Remnawave", desc: "Прокси/egress (Xray)", sub: "proxy", group: "Сеть" },
  { name: "Authentik", desc: "SSO и пользователи", sub: "auth", group: "Платформа" },
  { name: "Uptime Kuma", desc: "Мониторинг доступности сервисов", sub: "uptime", group: "Платформа" },
  { name: "Stirling-PDF", desc: "Обработка PDF: merge/split/OCR/метаданные", sub: "pdf", group: "Утилиты" },
  { name: "Open WebUI", desc: "Чат с LLM (через OpenAI API)", sub: "webui", group: "AI" },
];

// Известные префиксы наших модулей — чтобы корректно вычислить «корневой» домен,
// когда страница открыта НЕ с главного хоста (вдруг попали на flow.* или term.*).
const KNOWN_PREFIXES = new Set([
  "spiderfoot", "term", "superset", "flows", "cron", "proxy", "auth", "traefik",
  "uptime", "pdf", "webui",
]);

/**
 * Возвращает базовый домен платформы.
 * - Если хост = `<prefix>.<root>` и prefix известен — отрезаем prefix.
 * - Иначе хост сам и есть корень (например `cybersecurity.aziral.com`).
 *
 * Это безопасно работает и на 2-уровневых (`aziral.localhost`),
 * и на 3+-уровневых (`cybersecurity.aziral.com`) доменах.
 */
function rootDomain(): string {
  const host = window.location.hostname;
  const parts = host.split(".");
  if (parts.length > 1 && KNOWN_PREFIXES.has(parts[0])) {
    return parts.slice(1).join(".");
  }
  return host;
}

export function Modules() {
  const root = rootDomain();
  return (
    <section aria-labelledby="m-h">
      <h1 id="m-h" className="page-title">Модули</h1>
      <p className="subtitle">Все инструменты под единым SSO. Открываются в своём интерфейсе.</p>
      <div className="grid">
        {MODULES.map((m) => (
          <a className="card" key={m.sub} href={`https://${m.sub}.${root}`} target="_blank" rel="noreferrer">
            <div className="meta">{m.group}</div>
            <h3>{m.name}</h3>
            <div className="meta">{m.desc}</div>
          </a>
        ))}
      </div>
    </section>
  );
}
