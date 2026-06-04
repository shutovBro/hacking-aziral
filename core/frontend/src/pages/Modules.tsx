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
];

export function Modules() {
  const root = window.location.hostname.split(".").slice(-2).join(".");
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
