# Clase 4 · Pruebas y Correcciones — Proyecto Mishi

**Corporación Universitaria Rafael Núñez**  
**Asignatura:** Aplicaciones Web II / Diseño de Software  
**Docente:** Maybelline Castro  
**Proyecto:** Mishi — Control de gastos personales para estudiantes universitarios  
**Fecha:** 2026-11-13  

---

## 1. Objetivo

Comprobar las funcionalidades del sistema Mishi mediante pruebas automatizadas con `pytest` y `pytest-django` sobre **modelos, formularios/validaciones, permisos y flujos críticos**, documentando el registro de incidencias encontradas y sus respectivas correcciones en el repositorio.

---

## 2. Registro de Incidencias y Errores Corregidos

| ID | Módulo / Archivo | Descripción de la incidencia detectada | Severidad | Commit de corrección | Estado |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **INC-01** | `requirements.txt` / `mishi_project/settings.py` | `settings.py` importaba `load_dotenv` de `python-dotenv`, pero la librería no estaba declarada en `requirements.txt`, provocando `ModuleNotFoundError` al instalar el proyecto en un entorno limpio. | Alta | `7a98bcb` | Resuelta |
| **INC-02** | `finanzas/views.py` (`dashboard_view`) | `gasto_hoy` sumaba los gastos de los últimos `dias` (15 o 30 días) en vez de la fecha actual (`hoy`) y los comparaba con el límite de 1 solo día. Además, `alerta_activa = True` y `total_hormiga = 0` estaban quemados, y "Últimos movimientos" mostraba el nombre de la categoría en lugar de la descripción. | Crítica | `4edd427` | Resuelta |
| **INC-03** | `finanzas/views.py` | Al inicializar una base de datos limpia, la tabla `Categoria` quedaba vacía e impedía registrar movimientos. Asimismo, faltaba pasar `'usuario': perfil` en las vistas internas (`movimiento_view`, `historial_view`, `editar_movimiento_view`, `metas_view`). | Alta | `eb0d0d6` | Resuelta |
| **INC-04** | `templates/` (`dashboard.html`, `base.html`, `registro.html`, `editar_movimiento.html`, `metas.html`) | Existían marcas residuales (```` ``` ````) en `dashboard.html`; `base.html` forzaba fondo verde (`!important`) incluso en `messages.error`; `step="100"` bloqueaba montos no múltiplos de 100; en `editar_movimiento.html` el monto perdía su valor en `<input type="number">` por formato regional; y `metas.html` tenía `colspan="5"` en lugar de `6`. | Media | `0a1fc0c` | Resuelta |
| **INC-05** | `database/schema.sql` | El script SQL estaba desactualizado frente a las migraciones `0002`–`0004` de Django (`cuenta_id`, `universidad`, `frecuencia`, `descripcion`, campos de `Meta_Ahorro` y `Prestamo`) y no incluía las categorías iniciales. | Media | `8e88062` | Resuelta |
| **INC-06** | `templates/registro_usuario.html` | Etiqueta `<label for="nombre">` duplicada con un `<div class="form-group">` sin cerrar y `step="1000"` en el campo de mesada. | Baja | `06c4974` | Resuelta |
| **INC-07** | `finanzas/tests.py` | Al incorporar `@login_required` en las vistas internas durante la Clase 3, 4 de las 7 pruebas iniciales fallaban con código HTTP `302` por ausencia de autenticación y datos de prueba. | Alta | `9702a10` | Resuelta |
| **INC-08** | `finanzas/views.py` (`historial_view`, `dashboard_view`, `registro_usuario_view`, `editar_movimiento_view`, `metas_view`) | El filtro `/app/historial/?categoria=abc` ejecutaba `Categoria.objects.filter(idCategoria=categoria_id)` fuera de `try/except`, generando error **HTTP 500** (`ValueError`). También faltaba validación de `saldo <= 0` con gasto hoy en `dashboard_view`, control de 2 decimales en `editar_movimiento_view`/`metas_view`, validación de `frecuencia` en registro y validación de `tipo` de préstamo. | Crítica | `e4e5b10` | Resuelta |
| **INC-09** | `static/css/styles.css` / `templates/base.html` | `dashboard.html` usaba la clase `.alert-danger` al superar el límite diario, pero no estaba definida en `styles.css`. Además, el botón "Cerrar sesión" usaba `class="nav-links"` y rompía la alineación visual de la barra superior. | Media | `f7f0a60` | Resuelta |

---

## 3. Suite de Pruebas Automatizadas (`pytest` + `pytest-django`)

Se configuró `pytest==9.2.0` y `pytest-django==4.14.0` mediante [pytest.ini](file:///c:/Users/Karla/Mishi/Mishi/pytest.ini) y se implementó la suite en [finanzas/test_pytest.py](file:///c:/Users/Karla/Mishi/Mishi/finanzas/test_pytest.py), complementada por [finanzas/tests.py](file:///c:/Users/Karla/Mishi/Mishi/finanzas/tests.py) (24 casos ejecutados en total):

### 3.1 Modelos (3 casos)
1. `test_modelo_usuario_y_valores_por_defecto`: Creación de `Usuario` ligado `OneToOne` a `User` y valores por defecto.
2. `test_modelo_transaccion_meta_y_prestamo`: Persistencia de `Transaccion`, `MetaAhorro` (`acumulado=0.00`) y `Prestamo` (`estado='Pendiente'`).
3. `test_modelo_borrado_en_cascada_usuario`: Integridad referencial (`ON DELETE CASCADE`) al eliminar un perfil `Usuario`.

### 3.2 Formularios y Validaciones (4 casos)
4. `test_formulario_registro_rechaza_correo_duplicado_y_frecuencia_invalida`: Rechazo de correos repetidos y frecuencias no permitidas.
5. `test_formulario_movimiento_rechaza_monto_minimo_decimales_y_fecha_futura`: Rechazo de montos `< $100`, más de 2 decimales y fechas futuras.
6. `test_formulario_editar_movimiento_rechaza_mas_de_dos_decimales`: Rechazo de montos con precisión inválida al editar movimientos.
7. `test_formulario_historial_categoria_no_numerica_no_genera_error_500`: Manejo seguro de `?categoria=abc` devolviendo HTTP `200` y mensaje controlado.

### 3.3 Permisos y Aislamiento entre Usuarios (6 casos)
8–11. `test_permisos_vistas_protegidas_redirigen_a_login` (`dashboard`, `movimiento`, `historial`, `metas`): Verificación de redirección a `/login/` sin sesión activa.
12. `test_permisos_usuario_no_puede_editar_ni_eliminar_movimiento_ajeno`: Aislamiento de transacciones entre usuarios distintos.
13. `test_permisos_usuario_no_puede_modificar_meta_ni_prestamo_ajeno`: Aislamiento de metas de ahorro y préstamos entre cuentas.

### 3.4 Flujos Críticos y Vistas (11 casos)
14. `test_flujo_critico_registro_usuario_y_categorias_por_defecto`: Registro de cuenta, login automático y carga de categorías iniciales.
15. `test_flujo_critico_calculo_saldo_gasto_hoy_hormiga_y_alerta_rf05`: Cálculo real de saldo, límite diario, `gasto_hoy` (excluyendo días previos), gastos hormiga (`<= $15.000`), alerta preventiva (`>= 75%`) y alerta de límite superado (`>= 100%`).
16. `test_flujo_critico_historial_filtros_edicion_y_eliminacion`: Ciclo completo CRUD y filtrado por categoría en historial.
17. `test_flujo_critico_metas_ahorro_y_prestamos`: Creación y abono a metas de ahorro; creación y pago de préstamos.
18–24. Casos de carga y operación en `finanzas/tests.py` (`MishiViewsTestCase`).

---

## 4. Reporte de Ejecución de Pruebas

**Comando ejecutado (entorno local SQLite con `local_settings.py`):**

```bash
..\venv\Scripts\pytest.exe -v --ds=local_settings
```

*(Nota: En entornos con MySQL configurado mediante `.env`, se ejecuta directamente `pytest -v` usando `mishi_project.settings` definido en `pytest.ini`.)*

**Resultado observado:**

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\Karla\Mishi\venv\Scripts\python.exe
cachedir: .pytest_cache
django: version: 5.2.18, settings: local_settings (from option)
rootdir: C:\Users\Karla\Mishi\Mishi
configfile: pytest.ini
plugins: django-4.14.0
collecting ... collected 24 items

finanzas/test_pytest.py::test_modelo_usuario_y_valores_por_defecto PASSED [  4%]
finanzas/test_pytest.py::test_modelo_transaccion_meta_y_prestamo PASSED  [  8%]
finanzas/test_pytest.py::test_modelo_borrado_en_cascada_usuario PASSED   [ 12%]
finanzas/test_pytest.py::test_formulario_registro_rechaza_correo_duplicado_y_frecuencia_invalida PASSED [ 16%]
finanzas/test_pytest.py::test_formulario_movimiento_rechaza_monto_minimo_decimales_y_fecha_futura PASSED [ 20%]
finanzas/test_pytest.py::test_formulario_editar_movimiento_rechaza_mas_de_dos_decimales PASSED [ 25%]
finanzas/test_pytest.py::test_formulario_historial_categoria_no_numerica_no_genera_error_500 PASSED [ 29%]
finanzas/test_pytest.py::test_permisos_vistas_protegidas_redirigen_a_login[dashboard] PASSED [ 33%]
finanzas/test_pytest.py::test_permisos_vistas_protegidas_redirigen_a_login[movimiento] PASSED [ 37%]
finanzas/test_pytest.py::test_permisos_vistas_protegidas_redirigen_a_login[historial] PASSED [ 41%]
finanzas/test_pytest.py::test_permisos_vistas_protegidas_redirigen_a_login[metas] PASSED [ 45%]
finanzas/test_pytest.py::test_permisos_usuario_no_puede_editar_ni_eliminar_movimiento_ajeno PASSED [ 50%]
finanzas/test_pytest.py::test_permisos_usuario_no_puede_modificar_meta_ni_prestamo_ajeno PASSED [ 54%]
finanzas/test_pytest.py::test_flujo_critico_registro_usuario_y_categorias_por_defecto PASSED [ 58%]
finanzas/test_pytest.py::test_flujo_critico_calculo_saldo_gasto_hoy_hormiga_y_alerta_rf05 PASSED [ 62%]
finanzas/test_pytest.py::test_flujo_critico_historial_filtros_edicion_y_eliminacion PASSED [ 66%]
finanzas/test_pytest.py::test_flujo_critico_metas_ahorro_y_prestamos PASSED [ 70%]
finanzas/tests.py::MishiViewsTestCase::test_dashboard_view PASSED        [ 75%]
finanzas/tests.py::MishiViewsTestCase::test_historial_view PASSED        [ 79%]
finanzas/tests.py::MishiViewsTestCase::test_landing_view PASSED          [ 83%]
finanzas/tests.py::MishiViewsTestCase::test_login_view PASSED            [ 87%]
finanzas/tests.py::MishiViewsTestCase::test_metas_view PASSED            [ 91%]
finanzas/tests.py::MishiViewsTestCase::test_movimiento_view PASSED       [ 95%]
finanzas/tests.py::MishiViewsTestCase::test_registro_usuario_view PASSED [100%]

============================= 24 passed in 20.11s =============================
```

**Resumen final:** **24/24 pruebas aprobadas (100% exitosas, 0 fallos)** y **9 incidencias registradas y corregidas**.
