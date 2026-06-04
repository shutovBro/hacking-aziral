import { NavLink, Route, Routes } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { Targets } from "./pages/Targets";
import { RunRecon } from "./pages/RunRecon";
import { ResultsExplorer } from "./pages/ResultsExplorer";
import { Modules } from "./pages/Modules";

export function App() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          Hacking<b>·</b>Aziral
        </div>
        <nav className="nav" aria-label="Основная навигация">
          <NavLink to="/" end>Обзор</NavLink>
          <NavLink to="/targets">Цели</NavLink>
          <NavLink to="/recon">Запустить разведку</NavLink>
          <NavLink to="/results">Результаты</NavLink>
          <NavLink to="/modules">Модули</NavLink>
        </nav>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/targets" element={<Targets />} />
          <Route path="/recon" element={<RunRecon />} />
          <Route path="/results" element={<ResultsExplorer />} />
          <Route path="/modules" element={<Modules />} />
        </Routes>
      </main>
    </div>
  );
}
