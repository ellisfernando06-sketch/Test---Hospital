# Dashboard Hospital (React)

Panel web tecnológico para el bot del hospital.

## Cómo arrancar

```bash
cd dashboard
npm install
npm run dev
```

Abre `http://localhost:5173`.

## Qué incluye

- Resumen del estado del sistema (online / mantenimiento / offline)
- Lista de módulos del bot
- Keys de roles (recordatorio: permisos por **ID**, no por nombre)
- Mapa de canales → keys de `config.CANALES`

## Nota

Hoy usa datos de demostración. Más adelante se puede conectar a una API del bot
(estado real, logs, etc.) sin cambiar la estructura del panel.
