# Identidad Visual y Manual de Marca · Mishi

**Subtítulo de marca:** Finanzas personales para estudiantes  
**Tagline principal:** *Tu plata, bajo control.*  
**Tagline secundario:** *Pequeñas monedas. Grandes metas.*  

> Documento de referencia visual del proyecto **Mishi** para mantener coherencia en logotipo, paleta cromática, tipografía, expresiones de la mascota, iconografía y experiencia de usuario web/móvil.

---

## 1. Paleta de Colores

| Nombre | Hex | Uso principal y atributos |
| :--- | :---: | :--- |
| **Naranja gato** | `#FF8C3A` | Color primario de marca, tarjeta principal de saldo, botones primarios, botón `+`, barras de progreso e íconos activos. (*Confianza, energía, amigabilidad*) |
| **Amarillo moneda** | `#FFD028` | Moneda de la mascota, acentos de logro, progreso y gráficas. (*Motivación, logros, optimismo*) |
| **Crema** | `#F7F4EE` | Fondo base general de la aplicación y superficies limpias. (*Limpieza, minimalismo, equilibrio*) |
| **Carbón** | `#292929` | Wordmark `mishi`, encabezados, textos principales y cifras financieras. (*Contraste, estructura, claridad*) |

* **Superficies de apoyo:** Blanco puro `#FFFFFF` para tarjetas elevadas sobre el fondo crema `#F7F4EE`, con bordes sutiles y radios amplios.

---

## 2. Tipografía

* **Familia tipográfica principal y secundaria:** `Plus Jakarta Sans`
* **Jerarquía de pesos:**
  * **Títulos / Logotipo (`mishi`):** `SemiBold` (600) / estilo redondeado
  * **Botones e interfaz (UI):** `Medium` (500)
  * **Cuerpos de texto:** `Regular` (400)
  * **Cifras monetarias:** Números tabulares (`font-variant-numeric: tabular-nums`) para correcta alineación en montos e historiales.

---

## 3. Logotipo y Versiones

1. **Logo principal (horizontal):** Mascota del gato naranja sosteniendo una moneda amarilla `$` a la izquierda + wordmark **`mishi`** en minúsculas (`#292929`) a la derecha.
2. **Versión ícono / app:** Contenedor cuadrado con esquinas muy redondeadas en naranja `#FF8C3A` con la ilustración de Mishi sosteniendo la moneda `$`. Uso para favicon, ícono PWA y avatar de aplicación.
3. **Versión reducida (vertical):** Mascota arriba y wordmark **`mishi`** centrado debajo (ideal para pantalla de bienvenida / login).

---

## 4. Personaje: El Gato Mishi

> *"Un compañero en tu camino financiero. Mishi es un gato curioso y decidido que traga monedas para ayudarte a ahorrar, organizar tus gastos y alcanzar tus metas. Porque tus sueños también se construyen con pequeñas decisiones."*

### Expresiones del personaje y contexto de uso en la app

| Expresión | Cuándo usarla en la interfaz |
| :--- | :--- |
| **Feliz** | Al ahorrar, registrar ingresos o celebrar avances positivos. |
| **Sorprendido** | Cuando aparece un gasto inesperado o se supera el límite diario (alertas RF-05). |
| **Pensativo (`?`)** | Al planificar presupuesto, registrar un movimiento o analizar filtros. |
| **Dormido (`Zzz`)** | Al completar una meta de ahorro al 100% o en estados de reposo. |

---

## 5. Iconografía

* **Estilo:** Íconos lineales minimalistas con terminaciones redondeadas en **Naranja gato (`#FF8C3A`)** (o carbón neutro en estado inactivo).
* **Secciones cubiertas:**
  * `Inicio` · `Gastos` · `Ahorro` · `Metas` · `Estadísticas` · `Educación` · `Perfil` · `Ajustes`

---

## 6. Lineamientos de Experiencia de Usuario (UI / App)

### Versión Móvil
* **Bienvenida:** Wordmark `mishi` + *"Tu plata, bajo control."*, mascota protagonista en el centro, botón píldora naranja *"Comenzar"* y enlace secundario *"¿Ya tienes cuenta? Inicia sesión"*.
* **Panel App:**
  * Saludo personalizado (*"Hola, [Nombre]"*).
  * Tarjeta principal destacada en **Naranja gato (`#FF8C3A`)** para el **Saldo disponible** (con botón de ocultar/mostrar monto).
  * Barra de progreso de consumo en naranja sobre fondo crema.
  * Lista de movimientos por categoría con ícono en contenedor suave y monto alineado a la derecha.
  * Barra de navegación inferior con botón central circular naranja **`+`** para registrar movimientos al instante.

### Versión Escritorio (Dashboard)
* **Navegación lateral (sidebar)** sobre fondo crema `#F7F4EE` con estado activo suave en naranja claro y logo arriba.
* **Fila superior de KPIs:** `Saldo disponible`, `Gastos de este mes` y `Meta de ahorro` (con barra de progreso en `#FF8C3A`).
* **Bloque inferior:** Gráfica tipo dona de *Tus gastos por categoría* (con total central y desglose porcentual) junto a la tarjeta *Tu próxima meta* con botón *Ver detalles*.
