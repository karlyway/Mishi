
<div align="center">

# M I S H I

### Una nueva forma de entender tus finanzas.

Controla tus gastos. Organiza tus ingresos. Construye tu futuro.

Aplicación web de finanzas personales diseñada para estudiantes universitarios.

<br>

![Python](https://img.shields.io/badge/Python-3.11+-18181B?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-18181B?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-18181B?style=for-the-badge&logo=sqlite&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8+-18181B?style=for-the-badge&logo=mysql&logoColor=white)

![JavaScript](https://img.shields.io/badge/JavaScript-18181B?style=flat-square&logo=javascript&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-18181B?style=flat-square&logo=chartdotjs&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-58_tests-18181B?style=flat-square&logo=pytest&logoColor=white)
![Responsive](https://img.shields.io/badge/Mobile_First-360px_to_1440px-18181B?style=flat-square)

<br>

[Explorar Mishi](#01--sobre-mishi) ·
[Funcionalidades](#02--funcionalidades) ·
[Instalación](#04--instalación) ·
[Arquitectura](#05--arquitectura) ·
[Documentación](#09--documentación)

<br>

**Proyecto Integrador — 2026**

Corporación Universitaria Rafael Núñez

</div>

---

## 01 / Sobre Mishi

> Entender tus finanzas no debería ser complicado.

La vida universitaria implica tomar decisiones financieras constantemente: administrar una mesada, cubrir gastos diarios, compartir cuentas y ahorrar para objetivos personales.

**Mishi** transforma estas necesidades en una experiencia digital centralizada, intuitiva y personalizada.

Más que un registro de gastos, es una herramienta diseñada para ayudar a los estudiantes a comprender cómo utilizan su dinero, identificar patrones de consumo y desarrollar mejores hábitos financieros.

Construida con Django 5.2, combina una interfaz personalizada con una arquitectura modular y un motor financiero centralizado.

### Mishi en cifras

| Requisitos funcionales | Requisitos no funcionales | Pruebas automatizadas |
| :---: | :---: | :---: |
| **14** | **06** | **58** |
| **10** | **12** | **15** |
| Modelos relacionales | Migraciones | Avatares personalizados |

<div align="center">

**Una plataforma. Todas tus finanzas.**

</div>

---

## 02 / Funcionalidades

Cada módulo responde a una necesidad real de la gestión financiera estudiantil.

### Control financiero

| Funcionalidad | Descripción |
| :--- | :--- |
| Ingresos | Registro de mesadas, ingresos adicionales y otros recursos económicos. |
| Gastos | Registro de movimientos con categorías base y personalizadas. |
| Saldo disponible | Cálculo centralizado del dinero disponible sin dobles descuentos. |
| Límite diario | Distribución del saldo disponible según el ciclo financiero, evitando divisiones por cero. |
| Historial | Consulta, filtrado, edición y eliminación de movimientos. |

### Planificación y ahorro

| Funcionalidad | Descripción |
| :--- | :--- |
| Metas de ahorro | Creación de objetivos personalizados con fechas límite. |
| Aportes | Seguimiento del progreso y cálculo real de cuotas de ahorro. |
| Presupuestos | Planificación mensual y seguimiento del gasto por categoría. |
| Gastos hormiga | Identificación de pequeños gastos mediante un umbral configurable. |
| Gastos compartidos | Gestión de préstamos y gastos compartidos sin doble contabilización. |

### Inteligencia financiera

| Funcionalidad | Descripción |
| :--- | :--- |
| Estadísticas | Visualización semanal, mensual y anual de los movimientos. |
| Comparación | Análisis del comportamiento financiero entre períodos. |
| Evolución del ahorro | Seguimiento del ahorro durante los últimos seis meses. |
| Recomendaciones | Sugerencias personalizadas basadas en datos financieros reales. |

### Alertas y notificaciones

| Tipo de alerta | Comportamiento |
| :--- | :--- |
| Preventiva | Se activa al alcanzar el 80 % del límite. |
| Límite superado | Se activa al superar el 100 % del límite. |
| Saldo insuficiente | Informa sobre situaciones de insuficiencia financiera. |
| Centro de notificaciones | Centraliza las alertas dentro de la aplicación. |
| Descarte persistente | Evita que las notificaciones descartadas reaparezcan. |

### Perfil y personalización

- Catálogo de 15 avatares Mishi.
- Gestión de información del usuario.
- Cambio de contraseña desde el perfil.
- Configuración personalizada de gastos hormiga.
- Política de privacidad con consentimiento versionado.

<details>
<summary><strong>Consultar trazabilidad de requisitos funcionales</strong></summary>

<br>

| ID | Requisito |
| :--- | :--- |
| RF-01 | Registro de ingresos y gastos. |
| RF-02 | Categorías base y personalizadas. |
| RF-03 | Cálculo del saldo disponible. |
| RF-04 | Cálculo del límite diario. |
| RF-05 | Alertas financieras preventivas. |
| RF-06 | Gestión del historial financiero. |
| RF-07 | Estadísticas financieras. |
| RF-08 | Comparación entre períodos. |
| RF-09 | Identificación de gastos hormiga. |
| RF-10 | Metas de ahorro. |
| RF-11 | Presupuestos por categoría. |
| RF-12 | Préstamos y gastos compartidos. |
| RF-13 | Recomendaciones personalizadas. |
| RF-14 | Gestión del perfil y seguridad. |

[Consultar matriz completa de cumplimiento](documentacion/MATRIZ_CUMPLIMIENTO_RF_RNF.md)

</details>

---

## 03 / Diseño y tecnología

### Diseñada alrededor del usuario.

Mishi incorpora un sistema de diseño propio que busca simplificar la interacción con información financiera compleja.

La experiencia se desarrolla bajo un enfoque **Mobile-First**, priorizando los dispositivos móviles sin comprometer la experiencia en escritorio.

| Experiencia | Implementación |
| :--- | :--- |
| Diseño responsivo | Verificado desde 360 px hasta 1440 px. |
| Identidad visual | Sistema de diseño personalizado. |
| Personalización | 15 avatares exclusivos de Mishi. |
| Visualización | Gráficos financieros interactivos. |
| Interacción | Bottom Sheets y componentes personalizados. |
| Navegación | Interfaz adaptada a diferentes tamaños de pantalla. |
| Formularios | Calendarios y selectores personalizados. |

[Explorar la identidad visual del proyecto](documentacion/IDENTIDAD_VISUAL.md)

### Stack tecnológico

<div align="center">

<img src="https://skillicons.dev/icons?i=python,django,html,css,js,mysql,sqlite&theme=light" alt="Stack tecnológico de Mishi">

</div>

<br>

| Tecnología | Implementación |
| :--- | :--- |
| Python 3.11+ | Lenguaje principal del sistema. |
| Django 5.2 | Framework backend y gestión de la aplicación. |
| HTML5 | Estructura de las interfaces. |
| CSS3 | Sistema de diseño y adaptabilidad. |
| JavaScript | Interacciones y comportamiento de la interfaz. |
| Chart.js | Visualización de información financiera. |
| Django Templates | Renderizado de interfaces dinámicas. |
| Django ORM | Gestión y persistencia de datos. |
| SQLite | Entorno local, pruebas y demostración. |
| MySQL 8+ | Motor de base de datos alternativo. |
| pytest | Pruebas automatizadas. |
| pytest-django | Integración de pruebas con Django. |

---

## 04 / Instalación

### Inicia Mishi en tu entorno local.

> [!TIP]
> Se recomienda utilizar SQLite para ejecutar, evaluar y demostrar el proyecto sin necesidad de configurar un servidor de base de datos externo.

### Requisitos previos

| Requisito | Versión |
| :--- | :--- |
| Python | 3.11 o superior |
| pip | Disponible en el entorno |
| venv | Entorno virtual de Python |
| MySQL | 8+ / Opcional |

Versión de Python utilizada durante la verificación: `3.11.9`.

### Paso 01 — Crear el entorno virtual

<details open>
<summary><strong>Windows — PowerShell</strong></summary>

<br>

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

</details>

<details>
<summary><strong>macOS / Linux</strong></summary>

<br>

```bash
python3 -m venv venv
source venv/bin/activate
```

</details>

### Paso 02 — Instalar las dependencias

```bash
pip install -r requirements.txt
```

### Paso 03 — Configurar el entorno local

Copia el archivo de configuración de ejemplo en la raíz del proyecto.

<details open>
<summary><strong>Windows — PowerShell</strong></summary>

<br>

```powershell
Copy-Item local_settings.example.py local_settings.py
```

</details>

<details>
<summary><strong>macOS / Linux</strong></summary>

<br>

```bash
cp local_settings.example.py local_settings.py
```

</details>

### Paso 04 — Aplicar las migraciones

```bash
python manage.py migrate --settings=local_settings
```

Se aplicarán las migraciones pendientes de la base de datos, correspondientes a las versiones `0001` a `0012`.

### Paso 05 — Ejecutar Mishi

```bash
python manage.py runserver --settings=local_settings
```

<div align="center">

<br>

**Mishi ya está listo para iniciar.**

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

<br>

</div>

### Configuración alternativa

<details>
<summary><strong>Ejecutar Mishi con MySQL 8+</strong></summary>

<br>

**1. Configurar las variables de entorno**

Copia `.env.example` como `.env` y completa las credenciales correspondientes.

| Variable | Descripción |
| :--- | :--- |
| DB_NAME | Nombre de la base de datos. |
| DB_USER | Usuario de MySQL. |
| DB_PASSWORD | Contraseña de conexión. |
| DB_HOST | Dirección del servidor. |
| DB_PORT | Puerto de conexión. |

**2. Crear la base de datos**

```sql
CREATE DATABASE mishi_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

**3. Aplicar las migraciones**

```bash
python manage.py migrate
```

**4. Iniciar el servidor**

```bash
python manage.py runserver
```

</details>

> [!IMPORTANT]
> Las migraciones `0005` a `0012` fueron verificadas en SQLite. Su ejecución sobre MySQL permanece pendiente hasta configurar un servidor y credenciales válidas.

> [!CAUTION]
> No publiques archivos `.env`, contraseñas ni credenciales reales dentro del repositorio.

---

## 05 / Arquitectura

### Modular por diseño.

Mishi implementa el patrón arquitectónico **Model-View-Template (MVT)** de Django, complementado con una capa de servicios especializada.

Esta separación permite mantener la lógica financiera independiente de los controladores HTTP y de la presentación visual, facilitando el mantenimiento, la reutilización y las pruebas del sistema.

### Capas del sistema

| Capa | Responsabilidad |
| :--- | :--- |
| 01 — Presentación | Interfaces responsivas, plantillas y experiencia de usuario. |
| 02 — Enrutamiento | Gestión de rutas públicas y privadas. |
| 03 — Controladores | Procesamiento de solicitudes HTTP y validaciones. |
| 04 — Servicios | Reglas de negocio y procesamiento financiero. |
| 05 — Modelos | Representación de entidades y relaciones. |
| 06 — Persistencia | Almacenamiento y recuperación de información. |

### Motor financiero

El núcleo de Mishi centraliza los cálculos financieros mediante reglas de negocio compartidas.

Sus principales responsabilidades son:

- Cálculo consistente del saldo disponible.
- Gestión de ciclos financieros.
- Cálculo del límite diario.
- Prevención de dobles descuentos.
- Prevención de divisiones por cero.
- Evaluación de alertas financieras.
- Identificación de gastos hormiga.

### Servicios especializados

| Servicio | Responsabilidad |
| :--- | :--- |
| `finanzas_service.py` | Motor financiero central. |
| `categorias_service.py` | Categorías base y personalizadas. |
| `metas_service.py` | Metas, aportes y cálculo de cuotas. |
| `presupuestos_service.py` | Presupuestos mensuales por categoría. |
| `compartidos_service.py` | Préstamos y gastos compartidos idempotentes. |
| `analitica_service.py` | Análisis comparativo y evolución del ahorro. |
| `recomendaciones_service.py` | Recomendaciones financieras personalizadas. |
| `notificaciones_service.py` | Alertas y descarte persistente. |
| `seguridad_service.py` | Contraseñas y consentimiento versionado. |
| `avatares.py` | Catálogo de avatares personalizables. |

[Consultar la arquitectura técnica completa](documentacion/ARQUITECTURA_Y_BASE_DE_DATOS_REAL.md)

---

## 06 / Estructura y persistencia

El repositorio mantiene una organización modular que facilita la identificación de responsabilidades y la evolución del proyecto.

<details>
<summary><strong>Explorar estructura del repositorio</strong></summary>

<br>

```text
Mishi-1/
|
├── manage.py
├── requirements.txt
├── pytest.ini
├── .env.example
├── local_settings.example.py
|
├── mishi_project/
|
├── finanzas/
|   ├── models.py
|   ├── views.py
|   ├── urls.py
|   ├── context_processors.py
|   ├── ui_helpers.py
|   |
|   ├── migrations/
|   |
|   ├── services/
|   |   ├── finanzas_service.py
|   |   ├── categorias_service.py
|   |   ├── metas_service.py
|   |   ├── presupuestos_service.py
|   |   ├── compartidos_service.py
|   |   ├── analitica_service.py
|   |   ├── recomendaciones_service.py
|   |   ├── notificaciones_service.py
|   |   ├── seguridad_service.py
|   |   └── avatares.py
|   |
|   ├── test_pytest.py
|   └── tests.py
|
├── templates/
|
├── static/
|   ├── css/
|   |   └── styles.css
|   ├── js/
|   └── img/
|
├── database/
|   └── schema.sql
|
└── documentacion/
    ├── MATRIZ_CUMPLIMIENTO_RF_RNF.md
    ├── ARQUITECTURA_Y_BASE_DE_DATOS_REAL.md
    ├── arquitectura-sistema-mishi.md
    ├── IDENTIDAD_VISUAL.md
    └── Reporte_Clase_4_Pruebas_y_Correcciones.md
```

</details>

### Directorios principales

| Directorio | Contenido |
| :--- | :--- |
| `mishi_project/` | Configuración global, seguridad y rutas principales. |
| `finanzas/` | Aplicación principal y modelos de negocio. |
| `finanzas/services/` | Lógica de negocio modular. |
| `finanzas/migrations/` | Versionado de la base de datos. |
| `templates/` | Interfaces y componentes HTML. |
| `static/` | Estilos, scripts, ilustraciones y avatares. |
| `database/` | Esquema SQL de referencia. |
| `documentacion/` | Documentación técnica y académica. |

### Base de datos

Mishi utiliza un modelo de datos relacional administrado mediante Django ORM.

| Característica | Implementación |
| :--- | :--- |
| Modelos relacionales | 10 |
| Migraciones | 0001 a 0012 |
| Motor local | SQLite |
| Motor alternativo | MySQL 8+ |
| Persistencia | Django ORM |
| Esquema de referencia | `database/schema.sql` |
| Aislamiento de datos | Información asociada a cada usuario. |

[Explorar el modelo relacional](documentacion/ARQUITECTURA_Y_BASE_DE_DATOS_REAL.md) · [Consultar esquema SQL](database/schema.sql)

---

## 07 / Seguridad y privacidad

### Tus finanzas. Tu información.

La protección de la información personal y financiera forma parte del diseño del sistema.

![Authentication](https://img.shields.io/badge/Authentication-Django-18181B?style=flat-square)
![Password Hashing](https://img.shields.io/badge/Password_Hashing-PBKDF2_SHA256-18181B?style=flat-square)
![CSRF](https://img.shields.io/badge/Protection-CSRF-18181B?style=flat-square)

| Mecanismo | Implementación |
| :--- | :--- |
| Autenticación | Sistema de autenticación de Django. |
| Contraseñas | Hash mediante PBKDF2-SHA256. |
| Validación | Comprobación de contraseñas del lado del servidor. |
| Formularios | Protección contra solicitudes CSRF. |
| Información financiera | Aislamiento de datos por usuario. |
| Gestión de cuenta | Cambio de contraseña desde el perfil. |
| Credenciales | Configuración mediante variables de entorno. |
| Privacidad | Consentimiento versionado. |

### Protección de datos personales

Mishi incorpora una política de privacidad que toma como referencia la Ley 1581 de 2012 de Colombia, relacionada con la protección de datos personales.

La aplicación contempla el registro versionado del consentimiento del usuario.

La referencia normativa no constituye por sí sola una certificación de cumplimiento legal.

---

## 08 / Calidad y pruebas

### La precisión también forma parte de la experiencia.

<div align="center">

![Tests](https://img.shields.io/badge/58-AUTOMATED_TESTS-18181B?style=for-the-badge)
![Framework](https://img.shields.io/badge/Framework-pytest-18181B?style=for-the-badge&logo=pytest&logoColor=white)

</div>

<br>

El proyecto cuenta con una suite de 58 pruebas automatizadas para evaluar funcionalidades, reglas de negocio, seguridad y consistencia financiera.

### Ejecutar las pruebas

```bash
pytest -v --ds=local_settings
```

### Verificar la integridad del sistema

```bash
python manage.py check --settings=local_settings
```

### Estado de validación

| Componente | Estado |
| :--- | :--- |
| Python 3.11.9 | ![Verificado](https://img.shields.io/badge/Verificado-22863A?style=flat-square) |
| Responsive 360–1440 px | ![Verificado](https://img.shields.io/badge/Verificado-22863A?style=flat-square) |
| Migraciones 0005–0012 en SQLite | ![Verificado](https://img.shields.io/badge/Verificado-22863A?style=flat-square) |
| Migraciones 0005–0012 en MySQL | ![Pendiente](https://img.shields.io/badge/Pendiente-D97706?style=flat-square) |
| Suite automatizada | ![58 pruebas](https://img.shields.io/badge/58_pruebas-18181B?style=flat-square) |
| Requisitos funcionales | Consultar matriz de cumplimiento. |
| Requisitos no funcionales | Consultar matriz de cumplimiento. |

El resultado actual de la suite se obtiene ejecutando las pruebas en el entorno correspondiente.

[Consultar matriz de cumplimiento](documentacion/MATRIZ_CUMPLIMIENTO_RF_RNF.md) · [Consultar reporte de pruebas](documentacion/Reporte_Clase_4_Pruebas_y_Correcciones.md)

---

## 09 / Documentación

### Conoce Mishi en profundidad.

La documentación reúne las decisiones de diseño, los requisitos del sistema, la arquitectura implementada y las evidencias de validación del proyecto.

| Documento | Contenido | Acceso |
| :--- | :--- | :---: |
| Matriz de cumplimiento | Trazabilidad de los 14 RF y 6 RNF. | [Explorar](documentacion/MATRIZ_CUMPLIMIENTO_RF_RNF.md) |
| Arquitectura y base de datos | Arquitectura modular y modelo relacional real. | [Explorar](documentacion/ARQUITECTURA_Y_BASE_DE_DATOS_REAL.md) |
| Arquitectura académica | Documento original correspondiente a Clase 4. | [Explorar](documentacion/arquitectura-sistema-mishi.md) |
| Identidad visual | Sistema de diseño e identidad gráfica. | [Explorar](documentacion/IDENTIDAD_VISUAL.md) |
| Pruebas y correcciones | Registro de pruebas y ajustes realizados. | [Explorar](documentacion/Reporte_Clase_4_Pruebas_y_Correcciones.md) |
| Esquema SQL | Estructura de referencia de la base de datos. | [Explorar](database/schema.sql) |

---

## 10 / El equipo detrás de Mishi

<div align="center">

### De una necesidad real a una solución digital.

Mishi es el resultado de un proyecto académico que integra diseño de software, desarrollo web y gestión financiera personal.

<br>

| EQUIPO DE DESARROLLO |
| :---: |
| Melvis Morales |
| Karla Amaranto |
| Isabel Álvarez |
| Harrinson Bonilla |

<br>

**Docente**

Maybelline Castro

<br>

**Corporación Universitaria Rafael Núñez**

Facultad de Ingeniería

Proyecto Integrador

Aplicaciones Web II / Diseño de Software

Cartagena, Colombia — 2026

</div>

---

<div align="center">

<br>

# M I S H I

### Pequeñas decisiones. Grandes cambios.

Una experiencia diseñada para transformar la manera en que los estudiantes se relacionan con su dinero.

<br>

**Diseñado con propósito. Desarrollado con precisión.**

<br>

![Python](https://img.shields.io/badge/Built_with-Python-18181B?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Powered_by-Django-18181B?style=flat-square&logo=django&logoColor=white)
![Colombia](https://img.shields.io/badge/Made_in-Colombia-18181B?style=flat-square)

<br>

[Volver al inicio](#m-i-s-h-i)

<br>

Mishi — Proyecto Integrador 2026

</div>
