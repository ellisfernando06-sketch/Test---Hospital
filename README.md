# Bot de Discord — Hospital Roleplay

Bot completo de rol jerárquico para un servidor de Discord de temática
hospitalaria: roles/keys automáticos, ascensos y descensos por
departamento, sistema financiero, tickets, expedientes de personal,
cartas de solicitud rellenables que se enrutan solas hacia quien esté
a cargo de cada sección, y los sistemas operativos completos de un
hospital: **pacientes, inventario/logística, turnos, capacitaciones,
códigos de emergencia, quejas formales, ficha de personal y un panel
de estado general**.

## Archivos

| Archivo | Qué hace | ¿Se edita? |
|---|---|---|
| `config.py` | Nombres de keys/roles, departamentos, enrutamiento de solicitudes, canales de log, códigos de emergencia, token. | **Sí — es el único.** |
| `permisos.py` | Lógica de verificación de keys, niveles jerárquicos y detección de departamento. | No |
| `roles_store.py` | Guarda los IDs de rol que el bot crea (JSON local). | No |
| `roles_setup.py` | Crea/detecta automáticamente todos los roles al ejecutar `/configurar_roles`. | No |
| `registros.py` | Historial de asistencia, advertencias, licencias y cambios de cargo (expedientes). | No |
| `economia.py` | Sistema financiero persistente en JSON. | No |
| `estilos.py` | Estilo visual unificado de los embeds. | No |
| `paneles.py` | Botones: sistema de tickets y panel de acciones rápidas. | No |
| `solicitudes.py` | Modales rellenables: carta de solicitud, descargo y permiso, con enrutamiento automático (`enviar_solicitud` y `miembros_encargados` son públicas y las reutilizan `quejas.py` y `postulaciones.py`). | No |
| `pacientes.py` | Fichas clínicas: admisión, alta, notas, gravedad, traslados. | No |
| `inventario.py` | Stock por ítem, mínimos de alerta y bitácora de movimientos. | No |
| `turnos.py` | Turnos programados y control de entrada/salida (en servicio). | No |
| `capacitaciones.py` | Programación de capacitaciones y certificación de personal. | No |
| `codigos.py` | Estado de los códigos de emergencia activos. | No |
| `quejas.py` | Modal de queja formal + bitácora de pendientes/resueltas. | No |
| `postulaciones.py` | Postulaciones al staff: modal, enrutamiento y botones de aprobar/rechazar. | No |
| `ficha_personal.py` | Ficha administrativa editable (especialidad, licencia, contacto, notas). | No |
| `estado.py` | Agrega datos de todos los sistemas en el panel de estado general. | No |
| `bot_hospital.py` | El bot y todos los comandos. | No |

## Instalación

```
pip install discord.py
```

### 1. Crear el bot (Developer Portal)
1. Ve a https://discord.com/developers/applications → **New Application**.
2. Sección **Bot** → copia el **Token** y pégalo en `config.py` (`TOKEN = "..."`).
3. En la misma sección, activa **Server Members Intent** (obligatorio para gestionar roles).
4. Sección **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Permisos del bot: como mínimo `Manage Roles`, `Send Messages`, `Embed Links`, `Manage Channels` (para tickets).
   - Copia la URL generada y ábrela para invitar el bot a tu servidor.

### 2. Configurar roles automáticamente
Ya **no** necesitas copiar IDs de rol a mano. Con el bot corriendo en tu servidor, ejecuta:

```
/configurar_roles
```

(solo funciona para quien tenga la key `OWNER` — el primer OWNER debes
asignarlo tú mismo con un rol de Discord llamado exactamente igual al
que aparece en `config.KEYS_NOMBRES["OWNER"]`, o dándote el rol
manualmente una vez creado).

Esto crea (o detecta si ya existen con el mismo nombre) todos los
roles de `KEYS_NOMBRES`, todos los peldaños de cada departamento en
`DEPARTAMENTOS`, y el rol de suspensión — y guarda sus IDs solo en
`roles_ids.json`.

### 3. Jerarquía del rol del bot
En **Ajustes del servidor → Roles**, arrastra el rol del bot **por
encima** de todos los roles que deba poder asignar, quitar, ascender,
descender o suspender. Si el rol del bot queda por debajo, Discord
bloqueará la acción aunque el código sea correcto.

### 4. Restringir la visibilidad de comandos (opcional, recomendado)
El bot ya bloquea el uso de cada comando por código (según la key de
quien lo ejecuta), pero además puedes ocultar comandos completos a
nivel de Discord: **Ajustes del servidor → Integraciones → [tu bot] →
Permisos de comandos.**

### 5. Ejecutar el bot
```
python bot_hospital.py
```

Una vez conectado y sincronizado (puede tardar hasta 1 hora la
primera vez, o al instante si reinicias el bot), escribe `/` en
cualquier canal donde el bot tenga acceso para ver todos los comandos.

## Cómo funcionan las solicitudes (el corazón del sistema)

Cada carta o solicitud sube automáticamente a la **entidad superior
encargada de esa sección**, sin que nadie tenga que buscarla a mano:

- **`/carta_solicitud`** — el usuario elige el área (un departamento,
  o "General / Junta Directiva") y escribe el contenido en un
  formulario emergente. Se envía por **DM** al Director de ese
  departamento (o al Presidente del Consejo si es general).
- **`/solicitud_descargo`** — pensada para pedir el descargo o
  degradación de alguien. Va **siempre** al encargado de Recursos
  Humanos (`DIRECTOR_RRHH`), sin importar el departamento del
  afectado.
- **`/solicitud_permiso`** — el propio miembro del personal pide una
  licencia; el bot detecta solo a qué departamento pertenece (por sus
  roles) y la envía al director de ESE departamento.

Si nadie tiene todavía la key destino asignada, el bot sube un nivel
automáticamente (al Presidente del Consejo y, en última instancia, al
Owner) para que ninguna solicitud se pierda. Si el DM falla porque la
persona tiene los mensajes privados cerrados, o no hay nadie
disponible, la solicitud queda publicada igualmente en el canal de
log configurado en `config.CANALES`.

## Resumen de comandos por key

| Comando | Key requerida |
|---|---|
| `/configurar_roles` | OWNER |
| `/otorgar_key`, `/quitar_key` | OWNER, JEFE_JUNTA_DIRECTIVA, JUNTA_DIRECTIVA, DIRECTOR, JEFE_DEPARTAMENTO (según jerarquía) |
| `/dar_rol`, `/quitar_rol` | OWNER, JEFE_JUNTA_DIRECTIVA, JUNTA_DIRECTIVA, DIRECTOR, JEFE_DEPARTAMENTO (según jerarquía) |
| `/ascenso`, `/descenso` | Director del departamento correspondiente, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/transferir_departamento` | Director de ambos departamentos, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/contratar` | DIRECTOR_RRHH, Director del departamento destino, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/despedir` | DIRECTOR_RRHH, JEFE_JUNTA_DIRECTIVA, OWNER (jerarquía superior al afectado) |
| `/suspender`, `/reincorporar` | SUPERVISOR, JEFE_DEPARTAMENTO, DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER (jerarquía superior al afectado) |
| `/licencia` | SUPERVISOR, JEFE_DEPARTAMENTO, DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/expediente` | SUPERVISOR, JEFE_DEPARTAMENTO, DIRECTOR, DIRECTOR_RRHH, JUNTA_DIRECTIVA, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/mi_expediente` | Cualquiera (sobre sí mismo) |
| `/documento_medico` | DIRECTOR_MEDICO, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/formulario` | Cualquier DIRECTOR, JEFE_DEPARTAMENTO, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/reporte_departamento` | Director del departamento, JEFE_DEPARTAMENTO/SUPERVISOR de ese depto. |
| `/depositar`, `/retirar`, `/pagar_salario` | DIRECTOR_FINANCIERO, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/balance_general` | DIRECTOR_FINANCIERO, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/balance` (propio) | Cualquiera |
| `/balance` (de otro) | DIRECTOR_FINANCIERO, JUNTA_DIRECTIVA, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/transferir`, `/historial_financiero` | Cualquiera (sobre su propio dinero) |
| `/panel_tickets` | DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/panel_acciones` | Cualquiera (cada botón valida el cargo al pulsarlo) |
| `/convocar_junta`, `/votacion` | JEFE_JUNTA_DIRECTIVA, OWNER |
| `/anuncio` | JEFE_JUNTA_DIRECTIVA, DIRECTOR, OWNER |
| `/organigrama` | Cualquiera |
| `/marcar_asistencia`, `/advertencia`, `/historial_advertencias` | SUPERVISOR, JEFE_DEPARTAMENTO, DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/convocar_reunion_departamento` | Director del departamento, o JEFE_DEPARTAMENTO/SUPERVISOR de ese depto. |
| `/asignar_tarea` | SUPERVISOR, JEFE_DEPARTAMENTO, DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/carta_solicitud` | Cualquiera (se enruta según el área elegida) |
| `/solicitud_descargo` | SUPERVISOR, JEFE_DEPARTAMENTO, DIRECTOR, JUNTA_DIRECTIVA, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/solicitud_permiso` | Cualquiera (se enruta a su propio departamento) |
| `/mis_permisos` | Cualquiera |
| `/paciente admitir`, `alta`, `nota`, `gravedad`, `transferir`, `ver`, `listar` | Cuerpo Médico, Enfermería, DIRECTOR_MEDICO, DIRECTOR_ENFERMERIA, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/inventario agregar`, `retirar`, `set_minimo` | DIRECTOR_LOGISTICA, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/inventario stock`, `solicitar` | Cualquiera |
| `/turno asignar`, `horario` | SUPERVISOR, JEFE_DEPARTAMENTO, DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/turno entrar`, `salir`, `en_servicio`, `mis_turnos` | Cualquiera |
| `/capacitacion programar`, `certificar`, `historial` | SUPERVISOR, JEFE_DEPARTAMENTO, DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/capacitacion mis_capacitaciones`, `listar` | Cualquiera |
| `/codigo activar` | STAFF, SUPERVISOR, JEFE_DEPARTAMENTO, DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER (cualquier miembro del personal) |
| `/codigo cancelar` | SUPERVISOR, JEFE_DEPARTAMENTO, DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/codigo activos` | Cualquiera |
| `/ficha editar` | DIRECTOR_RRHH, DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/ficha ver` | Cualquiera (sobre sí mismo); SUPERVISOR o superior sobre otros |
| `/queja` | Cualquiera (se envía siempre a RRHH) |
| `/quejas_pendientes`, `/queja_resolver` | DIRECTOR_RRHH, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/postulacion aplicar` | Cualquiera (una pendiente a la vez) |
| `/postulacion pendientes` | DIRECTOR, DIRECTOR_RRHH, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/postulacion mias` | Cualquiera (sobre sí mismo) |
| Botones ✅ Aprobar / ❌ Rechazar de una postulación | Director del departamento postulado, DIRECTOR_RRHH, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/panel_estado` | DIRECTOR, JEFE_JUNTA_DIRECTIVA, OWNER |
| `/estado_hospital` | Cualquiera |

## Sistema de tickets (botones)
1. Un director/OWNER ejecuta `/panel_tickets` una vez en el canal que quieras usar como soporte.
2. Se publica un mensaje fijo con el botón **🎫 Abrir Ticket**.
3. Cualquier usuario que lo presione obtiene un canal privado (solo él + el staff definido en `TICKET_STAFF_KEYS` de `config.py`), con un botón **🔒 Cerrar Ticket** dentro para archivarlo.
4. Opcional: define `TICKET_CATEGORIA_ID` en `config.py` para que los tickets se creen ordenados dentro de una categoría específica.

## Panel de acciones rápidas (botones + modal)
Ejecuta `/panel_acciones` para publicar un panel con botones: **Nuevo
formulario**, **Mi balance**, **Mis permisos** y **Abrir Ticket**.
Cada botón sigue verificando la key de quien lo presiona.

## Votaciones de Junta Directiva
`/votacion "Tema"` publica un mensaje con tres botones (Sí / No /
Abstención). Solo cuentan los votos de quienes tengan
`JUNTA_DIRECTIVA`, `JEFE_JUNTA_DIRECTIVA` u `OWNER`. El conteo vive
mientras el bot siga corriendo (no sobrevive un reinicio).

## Sistemas operativos del hospital

### 🛏️ Pacientes (`/paciente`)
`admitir` crea la ficha clínica (gravedad, motivo, área/cama). `nota`
agrega notas clínicas con fecha y autor. `gravedad` y `transferir`
actualizan el estado sin perder el historial. `alta` cierra el
ingreso y lo mueve al historial de admisiones anteriores (hasta las
últimas 50). `ver` muestra la ficha completa; `listar` muestra a
todos los admitidos ahora mismo. Solo personal del Cuerpo Médico o
Enfermería (o sus directores) puede usar el grupo.

### 📦 Inventario / Logística (`/inventario`)
Stock por ítem con categoría y mínimo de alerta. `agregar`/`retirar`
quedan en `movimientos_inventario.json` y notifican automáticamente
en `log_inventario` si un ítem queda en o bajo su mínimo. Cualquiera
puede consultar `stock` o pedir insumos con `solicitar` (se enruta
por DM a `DIRECTOR_LOGISTICA`, igual que una carta de solicitud).

### 🗓️ Turnos (`/turno`)
`asignar` programa un turno (lo notifica por DM). `entrar`/`salir`
son autoservicio: cualquier miembro del personal marca su propia
entrada/salida de servicio, y `en_servicio` muestra quién está
trabajando ahora mismo — esto alimenta el panel de estado general.

### 🎓 Capacitaciones (`/capacitacion`)
`programar` anuncia una capacitación (opcionalmente mencionando el
escalafón de un departamento). `certificar` registra que alguien la
completó; `mis_capacitaciones`/`historial` consultan lo certificado.

### 🚨 Códigos de emergencia (`/codigo`)
Códigos predefinidos en `config.CODIGOS_EMERGENCIA` (Azul, Rojo,
Plata, Negro, Naranja, Amarillo, Ámbar, Verde — agrega o quita los
que tu servidor use). `activar` lo puede usar cualquier miembro del
personal (STAFF o superior, como en un hospital real) y menciona
automáticamente a los roles configurados en `mencion_keys` de cada
código; se recomienda configurar `CANALES["alerta_codigos"]`.
`cancelar` requiere SUPERVISOR o superior.

### 📢 Quejas formales (`/queja`)
Modal rellenable, disponible para cualquiera, que siempre se enruta
por DM al encargado de RRHH (reutilizando el mismo mecanismo de
`solicitudes.py`, incluido el "sube un nivel si no hay nadie
disponible"). RRHH gestiona las pendientes con `/quejas_pendientes`
y `/queja_resolver`.

### 🗂️ Ficha de personal (`/ficha`)
Complementa a `/expediente` (que es el *historial* de eventos):
aquí vive el *estado actual* editable — especialidad, licencia,
contacto RP y notas administrativas. La edita RRHH/Dirección; cada
quien puede ver la suya con `/ficha ver`.

### 📋 Postulaciones al staff (`/postulacion`)
`aplicar` abre un modal (experiencia/motivación + disponibilidad) y
la postulación se enruta por DM al Director del departamento elegido
(mismo mecanismo de `solicitudes.py`), con botones **✅ Aprobar** /
**❌ Rechazar**. Aprobar contrata automáticamente (da STAFF + el rol
base del departamento, igual que `/contratar`) y notifica al
postulante por DM; rechazar solo lo notifica. Solo el Director de ese
departamento (o RRHH/JEFE_JUNTA_DIRECTIVA/OWNER) puede resolverla.
Cada quien puede tener una única postulación pendiente a la vez, y
consultar su estado con `/postulacion mias`. A diferencia del resto
de paneles, estos botones **no sobreviven un reinicio del bot**
(igual que `/votacion`) — si el bot se reinicia con postulaciones
sin resolver, resuélvelas con `/contratar` manualmente y usa
`/postulacion pendientes` para verlas.

### 🩺 Panel de estado general (`/panel_estado`, `/estado_hospital`)
Un embed que resume en vivo: pacientes admitidos por gravedad,
códigos de emergencia activos, personal en turno, ítems de
inventario bajo mínimo y quejas pendientes. `/panel_estado` lo
publica de forma fija con un botón **🔄 Actualizar** (vista
persistente, sigue funcionando tras reiniciar el bot);
`/estado_hospital` da una foto puntual efímera.

## Ampliar el bot
- Para agregar un departamento nuevo: añade una entrada en `DEPARTAMENTOS` dentro de `config.py` y vuelve a correr `/configurar_roles`.
- Para agregar una dirección nueva: añade su key `DIRECTOR_X` en `KEYS_NOMBRES` (se integra sola a la key genérica `DIRECTOR`).
- Para agregar un canal de logs: pon el ID del canal en `config.CANALES`.
- Para agregar un comando exclusivo de una dirección: usa el decorador `@require_key("DIRECTOR_X", "JEFE_JUNTA_DIRECTIVA", "OWNER")` sobre la función del nuevo comando en `bot_hospital.py`.
- Para agregar/quitar un código de emergencia: edita `config.CODIGOS_EMERGENCIA`, no hace falta tocar código.

## Archivos de datos (se crean solos, no los edites a mano)

Todo el estado del bot vive en archivos JSON junto a `bot_hospital.py`,
creados automáticamente la primera vez que se usan: `roles_ids.json`,
`registros.json`, `economia.json`, `movimientos_financieros.json`,
`pacientes.json`, `inventario.json`, `movimientos_inventario.json`,
`turnos.json`, `capacitaciones.json`, `codigos_activos.json`,
`quejas.json`, `postulaciones.json` y `ficha_personal.json`. Haz backup de esta carpeta
periódicamente si te importa conservar el historial del servidor.
