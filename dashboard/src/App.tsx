import { useMemo, useState } from "react";

type Mode = "online" | "mantenimiento" | "offline";

const MODULES = [
  { name: "Bot Discord", status: "ok" as const, label: "ACTIVO" },
  { name: "Comandos", status: "ok" as const, label: "LISTOS" },
  { name: "Registros", status: "ok" as const, label: "AL DÍA" },
  { name: "Solicitudes", status: "ok" as const, label: "EN MARCHA" },
  { name: "Verificación", status: "ok" as const, label: "OPERATIVA" },
  { name: "Certificaciones", status: "ok" as const, label: "ACTIVO" },
  { name: "RRHH / Inactividad", status: "ok" as const, label: "ACTIVO" },
  { name: "Finanzas", status: "ok" as const, label: "ACTIVO" },
];

const ROLES = [
  { key: "OWNER", name: "Gerente Developer" },
  { key: "CO_OWNER", name: "Co-Owner" },
  { key: "DIRECTOR_GENERAL", name: "Director General" },
  { key: "DIRECTOR_MEDICO", name: "Director Médico" },
  { key: "DIRECTOR_ENFERMERIA", name: "Director de Enfermería" },
  { key: "DIRECTOR_RRHH", name: "Director de RRHH" },
  { key: "DIRECTOR_DOCENCIA", name: "Director de Docencia" },
  { key: "ENCARGADO_AREA", name: "Encargado de Área" },
  { key: "STAFF", name: "Personal del Hospital" },
];

const CHANNELS = [
  { ch: "#estado-sistema", use: "bot_status · estado del bot" },
  { ch: "#aprobaciones", use: "aprobaciones · control OWNER" },
  { ch: "#aprobaciones-rrhh", use: "RRHH · altas / bajas" },
  { ch: "#log-general", use: "log_general" },
  { ch: "#log-roles", use: "log_roles" },
  { ch: "#sanciones", use: "log_sanciones" },
  { ch: "#certificados", use: "log_certificados" },
  { ch: "#guardia", use: "panel_guardia" },
  { ch: "#codigos", use: "alerta_codigos" },
];

export default function App() {
  const [tab, setTab] = useState<"resumen" | "modulos" | "roles" | "canales">("resumen");
  const [mode] = useState<Mode>("online");

  const modeLabel = useMemo(() => {
    if (mode === "online") return { text: "ONLINE", cls: "online" };
    if (mode === "mantenimiento") return { text: "MANTENIMIENTO", cls: "mantenimiento" };
    return { text: "OFFLINE", cls: "offline" };
  }, [mode]);

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="logo">🏥</div>
          <div>
            <h1>Hospital General</h1>
            <p>Panel de control · sistema de gestión</p>
          </div>
        </div>
        <span className={`badge ${modeLabel.cls}`}>● {modeLabel.text}</span>
      </header>

      <nav className="tabs">
        {(
          [
            ["resumen", "Resumen"],
            ["modulos", "Módulos"],
            ["roles", "Roles"],
            ["canales", "Canales"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={tab === id ? "active" : ""}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </nav>

      {tab === "resumen" && (
        <div className="grid">
          <section className="card span-8">
            <h2>Estado del sistema</h2>
            <div className="status-hero">
              <div className="title">Sistema en línea</div>
              <p className="sub">
                El bot de Discord está operativo. Comandos, registros y solicitudes
                funcionan con normalidad para el personal autorizado.
              </p>
              <div className="metrics">
                <div className="metric">
                  <div className="label">Bot</div>
                  <div className="value">ACTIVO</div>
                </div>
                <div className="metric">
                  <div className="label">Comandos</div>
                  <div className="value">LISTOS</div>
                </div>
                <div className="metric">
                  <div className="label">Datos</div>
                  <div className="value">SYNC</div>
                </div>
                <div className="metric">
                  <div className="label">Modo</div>
                  <div className="value">{mode.toUpperCase()}</div>
                </div>
              </div>
            </div>
          </section>

          <section className="card span-4">
            <h2>Accesos rápidos</h2>
            <ul className="module-list">
              <li>
                <span>Discord · estado</span>
                <span className="pill">/estado_bot</span>
              </li>
              <li>
                <span>Reglamento</span>
                <span className="pill">/reglas</span>
              </li>
              <li>
                <span>Certificar</span>
                <span className="pill">/certificar</span>
              </li>
              <li>
                <span>Panel reglas</span>
                <span className="pill">/panel_reglas</span>
              </li>
            </ul>
          </section>
        </div>
      )}

      {tab === "modulos" && (
        <div className="grid">
          <section className="card">
            <h2>Módulos del bot</h2>
            <ul className="module-list">
              {MODULES.map((m) => (
                <li key={m.name}>
                  <span>
                    <span className={`dot ${m.status}`} />
                    {m.name}
                  </span>
                  <span className="pill">{m.label}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}

      {tab === "roles" && (
        <div className="grid">
          <section className="card">
            <h2>Jerarquía (keys del sistema)</h2>
            <p className="sub" style={{ color: "var(--muted)", marginBottom: 12, fontSize: "0.9rem" }}>
              Los permisos usan el <strong>ID del rol</strong> guardado en el bot, no el nombre.
              No borres roles para "recrearlos".
            </p>
            <div className="roles">
              {ROLES.map((r) => (
                <div className="role-row" key={r.key}>
                  <div>
                    <div>{r.name}</div>
                    <div className="key">{r.key}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {tab === "canales" && (
        <div className="grid">
          <section className="card">
            <h2>Canales recomendados · config</h2>
            <div className="channels">
              {CHANNELS.map((c) => (
                <div className="ch" key={c.ch}>
                  <code>{c.ch}</code>
                  <span style={{ color: "var(--muted)" }}>{c.use}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      <footer className="footer">
        Hospital General · dashboard React · datos de demostración (conectar API del bot más adelante)
      </footer>
    </div>
  );
}
