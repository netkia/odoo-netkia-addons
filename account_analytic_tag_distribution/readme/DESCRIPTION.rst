Módulo que **añade distribución porcentual a etiquetas analíticas**.

Permite configurar porcentajes de distribución en etiquetas analíticas para repartir automáticamente importes entre múltiples cuentas analíticas.

**Funcionalidad principal:**

* Campo **"Distribución Analítica"** en etiquetas analíticas
* **Configuración de porcentajes** por cuenta analítica
* **Reparto automático** de importes según porcentajes
* Validación de que **suma = 100%**

**Modelos extendidos:**

``account.analytic.tag``:
  * ``distribution`` (Boolean) - Indica si etiqueta tiene distribución
  * ``analytic_distribution`` (JSON) - Diccionario de cuentas y porcentajes
  * Método de validación de suma 100%

**Flujo de trabajo:**

1. **Configurar etiqueta con distribución:**

   * Crear etiqueta "DIST-OFICINAS"
   * Marcar "Distribución Analítica": ✅
   * Configurar porcentajes::
   
       OFICINA-MADRID: 50%
       OFICINA-BARCELONA: 30%
       OFICINA-VALENCIA: 20%

2. **Aplicar en documento:**

   * Factura de alquiler: 6.000€
   * Seleccionar etiqueta: "DIST-OFICINAS"

3. **Sistema automáticamente:**

   * Crea 3 apuntes analíticos::
   
       OFICINA-MADRID: 3.000€ (50%)
       OFICINA-BARCELONA: 1.800€ (30%)
       OFICINA-VALENCIA: 1.200€ (20%)

**Ventajas:**

* ✅ Distribución automática sin cálculo manual
* ✅ Plantillas reutilizables de distribución
* ✅ Consistencia en reparto mensual
* ✅ Ahorro de tiempo significativo
* ✅ Sin errores de cálculo

**Casos de uso:**

* **Gastos compartidos:** Alquiler, electricidad, servicios comunes
* **Costes indirectos:** Distribución por oficinas/departamentos
* **Multi-proyecto:** Empleado trabaja en varios proyectos
* **Multi-departamento:** Recurso compartido entre áreas

**Ejemplo práctico:**

Factura electricidad 2.000€::

    Etiqueta: DIST-CONSUMO-ENERGIA
    Distribución:
    - Producción: 60% → 1.200€
    - Oficinas: 25% → 500€
    - Almacén: 15% → 300€

**Ventaja sobre cuenta analítica simple:**

* Cuenta analítica simple: Todo el importe a UNA cuenta
* Etiqueta con distribución: Reparto automático entre VARIAS cuentas

**Integración:**

* Extiende ``account_analytic_tag`` (OCA/Odoo estándar)
* Compatible con todos los módulos que usan etiquetas
* Base para módulos avanzados de distribución

**Origen:**

* Autor original: Tecnativa - Víctor Martínez
* Mantenedor: victoralmau
* Adaptado por: Netkia
