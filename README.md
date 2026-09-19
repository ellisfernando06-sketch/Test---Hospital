# Bot Hospitalario Discord (Roleplay)

Sistema por **keys** (cargos). Cada **Director** ejecuta los comandos de su departamento.
**Despidos, sanciones internas e investigaciones** van a **RRHH**.

## Jerarquía (sin Junta Directiva)

| Nivel | Keys |
|-------|------|
| Cúpula | 👑 Owner, 🤝 Co-Owner, ⚖️ Director de Disciplina |
| Directores de área | 🩺 Médico, 💉 Enfermería, 👥 RRHH, 💰 Financiero, 📦 Logística, 🛡️ Seguridad |
| Mandos | 🎖️ Encargado de Área, ⭐ Jefe de Departamento, 📌 Supervisor |
| Staff | 📚 Residente, 🏥 Personal, 📝 Pasante, 💚 Voluntario |

## Departamentos y roles (escalafón)

- **Cuerpo Médico** + **Especialidades** (Cardiología, Neurología, Trauma, Pediatría, etc.) → Director Médico  
- **Enfermería** → Director de Enfermería  
- **RRHH** → Director de RRHH (despidos / sanciones / investigaciones)  
- **Finanzas, Logística, Seguridad, Administración** → su Director  
- **Staff del Servidor** (Trial → Head Staff) → Owner  

## Comandos de personal → RRHH

- `/despedir` — solo **DIRECTOR_RRHH** / OWNER  
- `/suspender` — solo **DIRECTOR_RRHH** / OWNER  
- `/sancion_interna` — RRHH / Disciplina / OWNER  
- `/solicitud_investigacion` — mandos / directores → notifica a RRHH  
- `/solicitud_descargo` → RRHH  

## Instalación

```bash
pip install -r requirements.txt
export TOKEN="tu_token"
python bot_hospital.py
```

Railway: variable `TOKEN`, start `python bot_hospital.py`.

1. Sube el rol del bot por encima de todos los roles.  
2. Intents: Server Members + Message Content.  
3. OWNER ejecuta `/configurar_roles` (crea roles con emoji si faltan).  
