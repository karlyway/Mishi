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
```
