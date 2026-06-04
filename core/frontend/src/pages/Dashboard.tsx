import { useEffect, useState } from "react";
import { api, type Job, type Target } from "../api";

export function Dashboard() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [err, setErr] = useState<string>();

  useEffect(() => {
    Promise.all([api.listTargets(), api.listJobs()])
      .then(([t, j]) => {
        setTargets(t);
        setJobs(j);
      })
      .catch((e) => setErr(e.message));
  }, []);

  const blocked = jobs.filter((j) => j.status === "blocked").length;
  const done = jobs.filter((j) => j.status === "completed").length;

  return (
    <section aria-labelledby="dash-h">
      <h1 id="dash-h" className="page-title">Обзор платформы</h1>
      <p className="subtitle">Единая консоль авторизованной разведки</p>
      {err && <div className="notice error">{err}</div>}
      <div className="grid">
        <article className="card"><div className="meta">Авторизованных целей</div><h3>{targets.length}</h3></article>
        <article className="card"><div className="meta">Сканов завершено</div><h3>{done}</h3></article>
        <article className="card"><div className="meta">Заблокировано scope-gate</div><h3>{blocked}</h3></article>
        <article className="card"><div className="meta">Всего задач</div><h3>{jobs.length}</h3></article>
      </div>
    </section>
  );
}
