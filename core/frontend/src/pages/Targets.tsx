import { useEffect, useState } from "react";
import { api, type Target } from "../api";

const emptyForm = { name: "", description: "", authorized_by: "", domains: "", usernames: "", emails: "", ip_ranges: "" };

function toList(s: string): string[] {
  return s.split(/[\s,]+/).map((x) => x.trim()).filter(Boolean);
}

export function Targets() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [err, setErr] = useState<string>();

  const load = () => api.listTargets().then(setTargets).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(undefined);
    try {
      await api.createTarget({
        name: form.name,
        description: form.description,
        authorized_by: form.authorized_by,
        scope: {
          domains: toList(form.domains),
          usernames: toList(form.usernames),
          emails: toList(form.emails),
          ip_ranges: toList(form.ip_ranges),
          hosts: [],
        },
      });
      setForm(emptyForm);
      load();
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  return (
    <section aria-labelledby="t-h">
      <h1 id="t-h" className="page-title">Цели</h1>
      <p className="subtitle">Каждая цель требует авторизации и scope. Сканы вне scope блокируются.</p>
      {err && <div className="notice error">{err}</div>}

      <form className="card" onSubmit={submit} style={{ marginBottom: "2rem" }}>
        <div className="row">
          <div className="field"><label>Название</label><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
          <div className="field"><label>Кем авторизовано</label><input value={form.authorized_by} onChange={(e) => setForm({ ...form, authorized_by: e.target.value })} /></div>
        </div>
        <div className="field"><label>Описание</label><input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
        <div className="row">
          <div className="field"><label>Домены (scope)</label><input placeholder="acme.com, *.acme.io" value={form.domains} onChange={(e) => setForm({ ...form, domains: e.target.value })} /></div>
          <div className="field"><label>Usernames</label><input placeholder="acme_admin" value={form.usernames} onChange={(e) => setForm({ ...form, usernames: e.target.value })} /></div>
        </div>
        <div className="row">
          <div className="field"><label>Emails</label><input value={form.emails} onChange={(e) => setForm({ ...form, emails: e.target.value })} /></div>
          <div className="field"><label>IP-диапазоны (CIDR)</label><input placeholder="10.0.0.0/24" value={form.ip_ranges} onChange={(e) => setForm({ ...form, ip_ranges: e.target.value })} /></div>
        </div>
        <button className="btn" type="submit">Создать цель</button>
      </form>

      {targets.length === 0 ? (
        <p className="empty">Целей пока нет — создайте первую выше.</p>
      ) : (
        <div className="grid">
          {targets.map((t) => (
            <article className="card" key={t.id}>
              <h3>{t.name}</h3>
              <div className="meta">{t.description || "—"}</div>
              <div className="meta" style={{ marginTop: ".5rem" }}>
                Домены: <code>{(t.scope.domains ?? []).join(", ") || "—"}</code>
              </div>
              <div className="meta">Авторизовал: {t.authorized_by || "—"}</div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
