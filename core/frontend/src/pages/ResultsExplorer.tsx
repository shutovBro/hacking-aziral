import { useEffect, useState } from "react";
import { api, type Entity, type Finding, type Target } from "../api";

export function ResultsExplorer() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [targetId, setTargetId] = useState<number | "">("");
  const [entities, setEntities] = useState<Entity[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);

  useEffect(() => { api.listTargets().then(setTargets).catch(() => {}); }, []);

  useEffect(() => {
    if (targetId === "") return;
    api.entities(targetId).then(setEntities).catch(() => {});
    api.findings(targetId).then(setFindings).catch(() => {});
  }, [targetId]);

  const byKind = entities.reduce<Record<string, number>>((acc, e) => {
    acc[e.kind] = (acc[e.kind] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <section aria-labelledby="re-h">
      <h1 id="re-h" className="page-title">Результаты</h1>
      <p className="subtitle">Единый граф нормализованных сущностей и находок по цели.</p>

      <div className="field" style={{ maxWidth: 320 }}>
        <label>Цель</label>
        <select value={targetId} onChange={(e) => setTargetId(Number(e.target.value))}>
          <option value="">— выбрать —</option>
          {targets.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
      </div>

      {targetId !== "" && (
        <>
          <div className="grid" style={{ margin: "1.5rem 0" }}>
            {Object.entries(byKind).map(([k, n]) => (
              <article className="card" key={k}><div className="meta">{k}</div><h3>{n}</h3></article>
            ))}
            {entities.length === 0 && <p className="empty">Находок пока нет. Запустите разведку.</p>}
          </div>

          <h3>Находки ({findings.length})</h3>
          <table>
            <thead><tr><th>Инструмент</th><th>Уверенность</th><th>Данные</th><th>Время</th></tr></thead>
            <tbody>
              {findings.map((f) => (
                <tr key={f.id}>
                  <td>{f.source_tool}</td>
                  <td className="mono">{f.confidence.toFixed(2)}</td>
                  <td className="mono" style={{ fontSize: ".78rem" }}>{JSON.stringify(f.raw_json)}</td>
                  <td className="meta">{new Date(f.discovered_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
