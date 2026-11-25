# Mishi — Control de Gastos Personales para Estudiantes Universitarios

**Proyecto Integrador · Aplicaciones Web II / Diseño de Software**  
Corporación Universitaria Rafael Núñez — Facultad de Ingeniería (Cartagena, Colombia)  
**Docente:** Maybelline Castro  
**Equipo:** Melvis Morales, Karla Amaranto, Isabel Álvarez y Harrinson Bonilla

---

## Descripción

**Mishi** es una aplicación web responsiva (*Mobile-First*, verificada desde `360 px` hasta escritorio `1440 px`) construida en **Django 5.2** para ayudar a estudiantes universitarios a administrar su mesada o ingresos:

- Registro ágil de ingresos y gastos con categorías base y personalizadas (**RF-01**, **RF-02**).
- Cálculo centralizado de saldo disponible y límite diario sin doble descuento ni divisiones por cero (**RF-03**, **RF-04**, **RNF-06**).
- Alertas preventivas (80%), límite superado (>100%), saldo insuficiente y centro de notificaciones in-app con descarte persistente (**RF-05**).
- Historial filtrable, editable y eliminable con calendario y selectores personalizados (**RF-06**).
- Estadísticas semanales, mensuales y anuales, comparación entre períodos, evolución del ahorro a 6 meses y recomendaciones personalizadas con datos reales (**RF-07**, **RF-08**, **RF-13**).
- Umbral de gastos hormiga configurable por usuario, metas de ahorro con fecha objetivo y cálculo real de cuotas, presupuestos mensuales reales por categoría, préstamos y gastos compartidos sin doble contabilización (**RF-09** a **RF-12**).
- Autenticación segura (`PBKDF2-SHA256`), validación de contraseñas en servidor, cambio de contraseña en Perfil, política de privacidad con consentimiento versionado (referencia Ley 1581 de 2012) y 15 avatares Mishi personalizables (**RF-14**, **RNF-04**).

---

## Requisitos previos

- **Python 3.11+** (probado en Python `3.11.9`)
- `pip` y `venv`
- Opcional: **MySQL 8+** (el proyecto incluye modo inmediato con **SQLite** para ejecución y evaluación rápida)

---

## Instalación y ejecución rápida (SQLite — recomendado para pruebas y demostración)

### 1. Crear y activar entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar SQLite local

Copia el archivo de ejemplo en la raíz del proyecto:

**Windows (PowerShell):**
```powershell
Copy-Item local_settings.example.py local_settings.py
```

**macOS / Linux:**
```bash
cp local_settings.example.py local_settings.py
```

### 4. Aplicar las migraciones (0001 a 0012)

```bash
python manage.py migrate --settings=local_settings
```

### 5. Iniciar el servidor

```bash
python manage.py runserver --settings=local_settings
```

Abre en tu navegador: **http://127.0.0.1:8000/**

---

## Ejecución opcional con MySQL (variables de entorno)

1. Copia `.env.example` como `.env` y completa tus credenciales (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).
2. Crea la base de datos `mishi_db` en MySQL.
3. Ejecuta:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

> **Nota transparente:** La verificación de las migraciones `0005` a `0012` está completada en SQLite; su ejecución sobre un servidor MySQL queda pendiente hasta configurar credenciales válidas en `.env`.

---

## Ejecución de pruebas automatizadas (58 pruebas)

```bash
pytest -v --ds=local_settings
```

También puedes validar la integridad de Django con:

```bash
python manage.py check --settings=local_settings
```

---

## Estructura del proyecto

```text
Mishi-1/
├── manage.py
├── requirements.txt
├── pytest.ini
├── .env.example
├── local_settings.example.py
├── mishi_project/                  # Configuración Django, seguridad de entorno y rutas raíz
├── finanzas/
│   ├── models.py                   # 10 modelos relacionales (Usuario, Transaccion, MetaAhorro, AporteMeta, ...)
│   ├── views.py                    # Controladores HTTP delgados (aislamiento por usuario y CSRF)
│   ├── urls.py                     # Rutas públicas y del panel /app/
│   ├── context_processors.py       # Contexto global (bottom sheet, avatares, notificaciones livianas)
│   ├── ui_helpers.py               # Helpers de presentación y agrupación
│   ├── migrations/                 # Migraciones independientes 0001 a 0012
│   ├── services/                   # Lógica de negocio modular
│   │   ├── finanzas_service.py     # Motor financiero central (saldo, ciclos, límite diario, RF-05, RF-09)
│   │   ├── categorias_service.py   # Categorías base y personalizadas (RF-02)
│   │   ├── metas_service.py        # Metas con fecha objetivo, cuotas reales y AporteMeta (RF-10)
│   │   ├── presupuestos_service.py # Presupuestos mensuales reales por categoría (RF-11)
│   │   ├── compartidos_service.py  # Préstamos y gastos compartidos idempotentes (RF-12)
│   │   ├── analitica_service.py    # Comparación entre períodos y evolución del ahorro (RF-08)
│   │   ├── recomendaciones_service.py # Recomendaciones personalizadas reales (RF-13)
│   │   ├── notificaciones_service.py  # Motor de alertas in-app sin reaparición de descartadas
│   │   ├── seguridad_service.py    # Validación de contraseñas y consentimiento versionado
│   │   └── avatares.py             # Catálogo de 15 avatares Mishi
│   ├── test_pytest.py              # Suite principal pytest-django
│   └── tests.py                    # Pruebas base Django TestCase
├── templates/                      # Plantillas HTML responsivas (Mobile-First + Desktop)
├── static/
│   ├── css/styles.css              # Sistema de diseño Mishi
│   ├── js/                         # Chart.js local + selectores/calendario personalizados Mishi
│   └── img/                        # Ilustraciones Mishi y 15 avatares PNG
├── database/schema.sql             # Esquema SQL de referencia
└── documentacion/
    ├── MATRIZ_CUMPLIMIENTO_RF_RNF.md         # Matriz actualizada de 14 RF y 6 RNF (verificados vs pendientes)
    ├── ARQUITECTURA_Y_BASE_DE_DATOS_REAL.md  # Arquitectura modular y modelo relacional real implementado
    ├── arquitectura-sistema-mishi.md         # Documento académico original de Clase 4
    ├── IDENTIDAD_VISUAL.md                   # Guía de identidad visual
    └── Reporte_Clase_4_Pruebas_y_Correcciones.md
```

---

## Documentación clave para evaluación

- **Matriz de cumplimiento (14 RF + 6 RNF):** [documentacion/MATRIZ_CUMPLIMIENTO_RF_RNF.md](documentacion/MATRIZ_CUMPLIMIENTO_RF_RNF.md)
- **Arquitectura real y base de datos actualizada:** [documentacion/ARQUITECTURA_Y_BASE_DE_DATOS_REAL.md](documentacion/ARQUITECTURA_Y_BASE_DE_DATOS_REAL.md)
