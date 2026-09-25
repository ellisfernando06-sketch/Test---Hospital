# 🎓 Sistema de Certificaciones con Firmas Triple

## 📋 Descripción General

Sistema completo de certificaciones para Hospital General que requiere **3 firmas obligatorias** para validar un certificado:

1. **Encargado/Instructor** — Quien otorga y valida la certificación
2. **Director de Investigación y Docencia** — Aprobación académica
3. **Director del Departamento/Ala** — Aprobación del área específica donde se otorga la certificación

## 🚀 Flujo de Uso

### 1. Registrar Firma Digital (previo)
```
/registrar_firma
  - imagen: [tu firma en PNG/JPG]
  - cargo: [tu rol: Docencia, Médico, Admin, Logística, RRHH, Seguridad, etc.]
```
Cada director debe registrar su firma **una sola vez**.

### 2. Crear Certificación Abierta (admin)
```
En código (editor):
import certificaciones_abiertas

aid = certificaciones_abiertas.crear_certificacion(
    nombre="Laboratorista",
    descripcion="Capacitación en técnicas de laboratorio",
    departamento="Laboratorio Clínico",
    director_zona_key="DIRECTOR_MEDICO",  # Director del departamento que otorga
    requiere_dos_firmas=True,
    activa=True
)
```

### 3. Certificar Estudiante
```
/certificar @usuario
  - Seleccionar certificación de la lista
  - Cédula: [número de identificación]
  - Ala/departamento: [área responsable]
  - Observaciones: [notas opcionales]
```

### 4. Autorización Triple (automático)
Se envían **3 mensajes separados** al canal de aprobaciones:

#### 📝 **Confirmación del Encargado**
- Quien inició la certificación confirma que el estudiante cumplió
- Opción: Confirmar ✅ o Rechazar ❌

#### 📚 **Autorización de Docencia**
- Director de Investigación y Docencia firma académicamente
- Opción: Autorizar ✅ o Rechazar ❌

#### 🏛️ **Autorización del Director del Departamento/Ala**
- **El Director específico del departamento** que otorga la certificación da visto bueno
- Puede ser: Médico, Administrativo, Logística, RRHH, Seguridad, etc.
- **Al autorizar aquí**, se genera automáticamente el certificado final

### 5. Certificado Generado
```
Imagen PNG con:
  ✓ Datos del estudiante (nombre, cédula)
  ✓ Certificación específica
  ✓ Tres firmas digitalizadas
  ✓ Fecha y número de certificado
  ✓ Áreas de autorización
```

Se envía a:
- **Canal de aprobaciones** (para registro)
- **DM del estudiante** (para su archivo)

## 📁 Archivos del Sistema

| Archivo | Función |
|---------|---------|
| `certificaciones_abiertas.py` | Gestión de certificaciones disponibles |
| `capacitacion_cert_ui.py` | Interfaz `/certificar` con menú de selección |
| `firmas.py` | Sistema de firmas, autorización triple e emisión |
| `certificado_imagen.py` | Generador de imagen PNG con tres firmas |
| `data/certificaciones_abiertas.json` | DB de certificaciones |
| `data/autorizaciones_pendientes.json` | DB de solicitudes en proceso |
| `data/firmas.json` | Registro de firmas por usuario/rol |
| `data/firmas_img/` | Imágenes de firmas digitales |

## ⚙️ Configuración

### Roles Disponibles (en `config.py`)
Cualquiera de estos puede ser el `director_zona_key` según el departamento:

```python
DIRECTOR_MEDICO         → "🩺 Director Médico"
DIRECTOR_ADMINISTRATIVO → "📋 Director Administrativo"
DIRECTOR_LOGISTICA      → "📦 Director de Logística"
DIRECTOR_RRHH           → "👥 Director de RRHH"
DIRECTOR_ENFERMERIA     → "💉 Director de Enfermería"
DIRECTOR_SEGURIDAD      → "🛡️ Director de Seguridad"
DIRECTOR_DISCIPLINA     → "⚖️ Director de Disciplina"
DIRECTOR_GENERAL        → "🖥️ Director General"
```

### Canales Configurables (en `config.py`)
```python
"aprobaciones"       → Donde se envían las 3 solicitudes
"log_certificados"   → Backup de certificados generados
```

## 🔑 Permisos Requeridos

**Para iniciar certificación:**
- OWNER, CO_OWNER, DIRECTOR_DOCENCIA, DIRECTOR_GENERAL, DIRECTOR, ENCARGADO_AREA, JEFE_DEPARTAMENTO

**Para confirmar (Encargado):**
- Debe tener firma registrada

**Para autorizar (Docencia):**
- DIRECTOR_DOCENCIA o OWNER
- Debe tener firma registrada

**Para autorizar (Director del Departamento):**
- El rol especificado en `director_zona_key` de la certificación
- Ejemplos: DIRECTOR_MEDICO, DIRECTOR_ADMINISTRATIVO, DIRECTOR_LOGISTICA, etc.
- Debe tener firma registrada

## 📊 Datos del Certificado

El archivo PNG incluye:
```
┌─────────────────────────────────────┐
│      HOSPITAL GENERAL               │
│      [Logo/Emblema HG]              │
├─────────────────────────────────────┤
│  Se certifica que                   │
│  [NOMBRE ESTUDIANTE]                │
│  ────────────────────              │
│  ha completado satisfactoriamente   │
│  la certificación:                  │
│  "[NOMBRE CERTIFICACIÓN]"           │
│                                     │
│  Identificación: [CÉDULA]           │
│  Observaciones: [Si existen]        │
│  Área/departamento: [Área]          │
│                                     │
│  Fecha: [DD/MM/YYYY] · N.º [CER-#] │
│                                     │
│ [FIRMA 1]  [FIRMA 2]  [FIRMA 3]    │
│ Otorgado   Docencia   Director Ala  │
│ Encargado  e Invest.  del Depto.    │
└─────────────────────────────────────┘
```

## 🛠️ Comandos Disponibles

```
/certificar @usuario                   — Inicia nueva certificación
/registrar_firma imagen cargo          — Registra tu firma
/ver_mi_firma                          — Muestra tu firma guardada
```

## 📝 Ejemplos de Uso

### Ejemplo 1: Certificación Médica (Director Médico)
```python
certificaciones_abiertas.crear_certificacion(
    nombre="RCP Básico",
    descripcion="Reanimación cardiopulmonar nivel básico",
    departamento="Urgencias",
    director_zona_key="DIRECTOR_MEDICO",
)
```
**Flujo:** Encargado → Docencia → **Director Médico** → Certificado

### Ejemplo 2: Certificación Administrativa (Director Admin)
```python
certificaciones_abiertas.crear_certificacion(
    nombre="Gestión de Documentos",
    descripcion="Protocolo de archivo y gestión documental",
    departamento="Administración",
    director_zona_key="DIRECTOR_ADMINISTRATIVO",
)
```
**Flujo:** Encargado → Docencia → **Director Administrativo** → Certificado

### Ejemplo 3: Certificación de Logística (Director Logística)
```python
certificaciones_abiertas.crear_certificacion(
    nombre="Manejo de Insumos",
    descripcion="Gestión de bodega y control de inventario",
    departamento="Logística",
    director_zona_key="DIRECTOR_LOGISTICA",
)
```
**Flujo:** Encargado → Docencia → **Director de Logística** → Certificado

## ⚠️ Notas Importantes

- **Las 3 firmas son OBLIGATORIAS** para que se genere el certificado
- El tercer director **depende del departamento** que otorga la certificación
- Si alguno rechaza, la solicitud se marca como rechazada y se detiene el proceso
- Las firmas se guardan en `data/firmas_img/` para reutilización
- El sistema usa la **plantilla oficial** de `assets/certificado_base.png`
- Cada certificación puede tener un **director de departamento diferente** según su área

## 🔄 Extensiones Futuras

Este sistema puede adaptarse para:
- Otras autorizaciones que requieren firmas (diplomas, permisos)
- Auditoría de quién autorizó qué y cuándo
- Historial de certificaciones por estudiante
- Generación en lote de certificados
- Certificaciones con más de 3 firmas si es necesario
