# Bot Hospitalario Discord (Roleplay)

Bot completo para un servidor de roleplay hospitalario con sistema de **keys** (cargos), departamentos, pacientes, inventario, turnos, códigos de emergencia, economía, postulaciones, quejas y control del bot.

## Características

- **Keys / jerarquía**: OWNER, CO_OWNER, Junta, Directores, Jefes, Supervisores, Staff.
- **Roles por ID**: el bot **no duplica roles**. Busca por nombre exacto (con emoji), guarda el ID y los reutiliza.
- **Orden por categorías**: `/configurar_roles` o `/ordenar_roles` ordena roles (RRHH, Médico, Enfermería, etc.).
- **Control del bot** (solo OWNER ejecuta al momento; CO_OWNER envía solicitud de aprobación al OWNER):
  - `/apagar_bot`
  - `/encender_bot`
  - `/mantenimiento_bot`
  - `/reiniciar_bot`
  - `/estado_bot`
- Pacientes, inventario, turnos, capacitaciones, códigos de emergencia, ficha de personal, postulaciones, quejas, tickets, economía, expedientes.

## Instalación

### Local
```bash
pip install -r requirements.txt
export TOKEN="tu_token_del_bot"
python bot_hospital.py
```

### Railway (recomendado)
1. Sube el proyecto (o conecta el repo).
2. **Variables** → añade:
   - `TOKEN` = token del bot (obligatorio)
   - Opcional: `DISCORD_TOKEN` / `BOT_TOKEN` (aliases)
3. Start command: `python bot_hospital.py`
4. El bot **no lee el token desde ningún archivo**; solo desde esas variables.


## Configuración (solo `config.py`)

1. Token (o variable de entorno).
2. Nombres de roles con **un emoji** representativo (deben coincidir con los del servidor).
3. IDs de canales de log (opcional) y `bot_status` / `aprobaciones`.
4. Departamentos y escalafones.
5. En el Developer Portal: activa **Server Members Intent** y **Message Content Intent**.
6. Sube el **rol del bot** por encima de todos los roles que vaya a gestionar.
7. Ejecuta una vez `/configurar_roles` (OWNER): detecta roles existentes, guarda IDs y ordena por categorías.

## Comandos de control (OWNER / CO_OWNER)

| Comando | OWNER | CO_OWNER |
|---------|-------|----------|
| `/apagar_bot` | Ejecuta | Envía solicitud de aprobación al OWNER |
| `/encender_bot` | Ejecuta | Idem |
| `/mantenimiento_bot` | Ejecuta | Idem |
| `/reiniciar_bot` | Ejecuta | Idem |
| `/estado_bot` | Cualquiera | Cualquiera |

La solicitud llega al canal `aprobaciones` (si está configurado) o por DM a quien tenga la key OWNER, con botones **Aprobar / Rechazar**.

## Estructura de módulos

```
bot_hospital.py      # Comandos slash y orquestación
config.py            # ÚNICO archivo a editar (token, roles, canales…)
permisos.py          # Keys y jerarquía
roles_store.py       # Persistencia de IDs de roles
roles_setup.py       # Detectar roles + ordenar por categorías
bot_control.py       # Estado online/mantenimiento/offline + aprobación
economia.py, pacientes.py, inventario.py, turnos.py, …
data/                # JSON generados en runtime (no editar a mano)
```

## Notas

- Si un rol ya existe con el **mismo nombre** (incluido el emoji), se usa su ID; no se crea otro.
- Para que el ordenamiento funcione, el rol del bot debe estar **por encima** de los roles a mover.
- En mantenimiento el bot sigue respondiendo; puedes filtrar comandos según `bot_control.get_mode()` si lo necesitas.
