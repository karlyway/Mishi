# Mishi - Control de Gastos Personales

Proyecto Integrador - Aplicaciones Web II
Corporacion Universitaria Rafael Nunez
Facultad de Ingenieria - Cartagena, Colombia
Docente: Maybelline Castro
Equipo: Grupo de Desarrollo Mishi

---

## Descripcion del Proyecto
Mishi es una aplicacion para el control y administracion de gastos personales de estudiantes universitarios. Permite registrar ingresos y gastos, calcular el limite diario recomendado segun los dias restantes para el proximo ingreso, alertar sobre gastos excesivos y llevar control de metas de ahorro y cuentas compartidas.

---

## Entregable: Clase 1 - Entorno y Frontend

- Entorno virtual (venv) y dependencias (Django 5.2).
- Configuracion del proyecto (mishi_project) y aplicacion (finanzas).
- Configuracion de URLs, archivos estaticos (static/css/styles.css) y plantillas (templates/).
- Plantilla base (base.html) y pantallas navegables:
  1. Inicio / Dashboard (/)
  2. Registrar movimiento (/registro/)
  3. Historial (/historial/)
  4. Metas y prestamos (/metas/)
- Pruebas unitarias configuradas y aprobadas.

---

## Ejecucion Local

1. Activar el entorno virtual:
```bash
.\venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Aplicar migraciones:
```bash
python manage.py migrate
```

4. Iniciar el servidor:
```bash
python manage.py runserver
```

Abrir en el navegador: http://127.0.0.1:8000/

---

## Pruebas
```bash
python manage.py test
pytest -v
```
*(Si ejecutas localmente con SQLite mediante `local_settings.py`: `pytest -v --ds=local_settings`)*
---

---

## 🚀 Avance - Clase 2: Backend y MySQL

En esta segunda fase del desarrollo del proyecto **Mishi**, nos enfocamos en la implementación práctica de la capa de persistencia de datos, estructurando la base de datos relacional y validando las operaciones fundamentales del sistema.

### 📌 ¿Qué se implementó y documentó?

* **Diseño e Implementación de la Base de Datos (`database/`):**
  * Creación del esquema relacional optimizado en MySQL para la gestión financiera de los estudiantes.
  * Definición de tablas normalizadas clave, tales como `usuario` (con control de mesadas y perfiles) y `categoria` (clasificación de movimientos).
  * Establecimiento de llaves primarias y tipos de datos adecuados para garantizar la integridad referencial.

* **Validación de Operaciones CRUD (`evidencias/`):**
  * Se ejecutaron y documentaron con éxito las cuatro operaciones esenciales de manipulación de datos sobre el servidor local de MySQL Workbench:
    1. **Create (`INSERT`):** Registro exitoso de nuevos usuarios y categorías de prueba.
    2. **Read (`SELECT`):** Consultas estructuradas para la recuperación y visualización de la información almacenada.
    3. **Update (`UPDATE`):** Modificación de registros específicos (como la actualización de montos de mesadas).
    4. **Delete (`DELETE`):** Depuración y eliminación controlada de registros de prueba en las tablas.

* **Evidencias Gráficas:**
  * Se incorporaron capturas de pantalla detalladas en la carpeta `/evidencias` que comprueban la ejecución correcta de cada instrucción SQL y los resultados devueltos por el sistema de gestión de bases de datos.

---

## ✅ Avance - Clase 4: Pruebas y Correcciones

* **Pruebas automatizadas (`pytest` y `pytest-django`):**
  * Configuración en `pytest.ini` y suite completa en `finanzas/test_pytest.py` + `finanzas/tests.py` (**24 pruebas exitosas** cubriendo modelos, formularios, permisos/aislamiento de usuarios y flujos críticos).
* **Registro de incidencias y reporte de ejecución:**
  * Documentado en `documentacion/Reporte_Clase_4_Pruebas_y_Correcciones.md` con las **9 incidencias** corregidas y la evidencia de ejecución.