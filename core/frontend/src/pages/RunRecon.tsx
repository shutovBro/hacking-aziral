import { useEffect, useState } from "react";
import { api, type Job, type Target } from "../api";

const TOOL_KINDS: Record<string, string> = {
  sherlock: "username",
  holehe: "email",
  theharvester: "domain",
  spiderfoot: "domain",
};

export function RunRecon() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [tools, setTools] = useState<string[]>([]);
  const [targetId, setTargetId] = useState<number | "">("");
  const [tool, setTool] = useState("theharvester");
  const [value, setValue] = useState("");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [msg, setMsg] = useState<{ kind: "error" | "warn" | "ok"; text: string }>();

  const loadJobs = () => api.listJobs().then(setJobs).catch(() => {});
  useEffect(() => {
    api.listTargets().then(setTargets).catch(() => {});
    api.tools().then((t) => setTools(t.tools)).catch(() => {});
    loadJobs();
    const id = setInterval(loadJobs, 4000);
    return () => clearInterval(id);
  }, []);

  async function launch(e: React.FormEvent) {
    e.preventDefault();
    setMsg(undefined);
    if (targetId === "") return;
    try {
      await api.launchScan({ target_id: targetId, tool, kind: TOOL_KINDS[tool] ?? "domain", value });
      setMsg({ kind: "ok", text: "Скан поставлен в очередь" });
      setValue("");
      loadJobs();
    } catch (e) {
      setMsg({ kind: "error", text: (e as Error).message });
    }
  }

  return (
    <section aria-labelledby="r-h">
      <h1 id="r-h" className="page-title">Запустить разведку</h1>
      <p className="subtitle">Инструмент → цель → значение. Scope-gate проверит авторизацию.</p>
      {msg && <div className={`notice ${msg.kind === "ok" ? "" : msg.kind}`}>{msg.text}</div>}

      <form className="card" onSubmit={launch} style={{ marginBottom: "2rem" }}>
        <div className="row">
          <div className="field">
            <label>Цель</label>
            <select value={targetId} onChange={(e) => setTargetId(Number(e.target.value))} required>
              <option value="">— выбрать —</option>
              {targets.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div className="field">
            <label>Инструмент</label>
            <select value={tool} onChange={(e) => setTool(e.target.value)}>
              {(tools.length ? tools : Object.keys(TOOL_KINDS)).map((t) => (
                <option key={t} value={t}>{t} ({TOOL_KINDS[t] ?? "?"})</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Значение ({TOOL_KINDS[tool]})</label>
            <input required value={value} onChange={(e) => setValue(e.target.value)} placeholder="acme.com / alice / a@acme.com" />
          </div>
        </div>
        <button className="btn" type="submit">▶ Запустить</button>
      </form>

      <h3>Последние задачи</h3>
      <table>
        <thead><tr><th>#</th><th>Инструмент</th><th>Статус</th><th>Лог</th></tr></thead>
        <tbody>
          {jobs.map((j) => (
            <tr key={j.id}>
              <td className="mono">{j.id}</td>
              <td>{j.tool}</td>
              <td><span className={`badge ${j.status}`}>{j.status}</span></td>
              <td className="meta">{j.log}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
