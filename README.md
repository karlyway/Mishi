# 🐱 Mishi - "Tu plata, bajo control"

> **Proyecto Integrador · Aplicaciones Web II**  
> **Corporación Universitaria Rafael Núñez**  
> **Facultad de Ingeniería · Cartagena, Colombia**  
> **Docente:** Maybelline Castro  
> **Integrantes:** Karla Amaranto, Melvis Morales, Isabel Álvarez, Harrinson Bonilla  

---

## 📌 Descripción del Proyecto
**Mishi** es una aplicación orientada al control y administración de los gastos personales de los estudiantes universitarios. Permite llevar un registro ágil de ingresos y gastos, calcular en tiempo real el límite diario recomendado ($\text{Saldo} / \text{Días restantes}$), alertar preventivamente sobre gastos hormiga y compras impulsivas, y gestionar metas de ahorro y cuentas compartidas entre compañeros.

---

## 🚀 Entregable: Clase 1 · Entorno y Frontend

Este repositorio contiene la entrega de la **Clase 1**, cumpliendo con:
- [x] Configuración de entorno virtual (`venv`) y dependencias (`Django 5.2`).
- [x] Estructura base del proyecto (`mishi_project`) y aplicación (`finanzas`).
- [x] Configuración de rutas (`urls.py`), archivos estáticos (`static/css/`) y plantillas (`templates/`).
- [x] Plantilla principal compartida (`base.html`) con diseño responsivo (móvil y escritorio $\ge 360\text{px}$).
- [x] Primeras pantallas navegables e interactivas:
  1. **Inicio / Dashboard (`/`):** Métricas de saldo, límite diario, barra de progreso del gasto de hoy, alerta preventiva y últimos movimientos.
  2. **Registrar Movimiento (`/registro/`):** Formulario rápido (<4 pasos) con pestañas de gasto/ingreso, categorías con iconos, selector de gasto compartido y cálculo en vivo del impacto presupuestario.
  3. **Historial (`/historial/`):** Listado detallado, badges de categoría, filtro de gastos hormiga y balance general.
  4. **Metas & Préstamos (`/metas/`):** Módulo de metas de ahorro estudiantil y módulo social para control de deudas entre compañeros.
- [x] Pruebas automatizadas aprobadas (`python manage.py test`).

---

## 🛠️ Guía de Ejecución Local

### 1. Clonar el repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd Mishi
```

### 2. Activar el entorno virtual
En Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```
*(O en Command Prompt: `.\venv\Scripts\activate.bat`)*

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar migraciones
```bash
python manage.py migrate
```

### 5. Iniciar el servidor de desarrollo
```bash
python manage.py runserver
```

Abre en tu navegador: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 🧪 Ejecutar Pruebas
```bash
python manage.py test
```
Verifica que las rutas y vistas retornen código HTTP `200 OK` y utilicen las plantillas correctas.

---

## 📂 Estructura del Proyecto
```text
Mishi/
├── finanzas/                # App de gestión financiera y vistas de Mishi
│   ├── migrations/
│   ├── tests.py             # Pruebas unitarias de las pantallas
│   ├── urls.py              # Rutas de la app
│   └── views.py             # Controladores y datos de presentación
├── mishi_project/           # Configuración principal de Django
│   ├── settings.py          # Ajustes (STATIC, TEMPLATES, APPS)
│   ├── urls.py              # Enrutador principal
│   ├── wsgi.py
│   └── asgi.py
├── static/
│   └── css/
│       └── styles.css       # Estilos personalizados, responsive y paleta Mishi
├── templates/
│   ├── base.html            # Layout maestro con navegación y branding
│   ├── dashboard.html       # Pantalla de inicio y métricas
│   ├── registro.html        # Pantalla de registro de movimientos
│   ├── historial.html       # Pantalla de historial y gastos hormiga
│   └── metas.html           # Metas de ahorro y préstamos entre amigos
├── requirements.txt         # Lista de dependencias
├── manage.py                # Script de administración de Django
└── .gitignore               # Configuración de exclusiones Git
```
