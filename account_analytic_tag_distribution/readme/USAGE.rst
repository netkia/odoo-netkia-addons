Caso 1: Distribución de alquiler mensual
=========================================

**Escenario:** Oficina compartida, reparto proporcional del alquiler.

**Configuración:**

Etiqueta: DIST-ALQUILER::

    OFICINA-MADRID: 50% (500m²)
    OFICINA-BARCELONA: 30% (300m²)
    OFICINA-VALENCIA: 20% (200m²)

**Factura mensual:**

.. code-block:: text

    Proveedor: Inmobiliaria XYZ
    Concepto: Alquiler Octubre 2025
    Importe: 10.000€
    Etiqueta: DIST-ALQUILER

**Sistema automáticamente:**

.. code-block:: text

    Apunte 1: OFICINA-MADRID → 5.000€ (50%)
    Apunte 2: OFICINA-BARCELONA → 3.000€ (30%)
    Apunte 3: OFICINA-VALENCIA → 2.000€ (20%)

**Informes por oficina:**

* Madrid: Coste alquiler 5.000€
* Barcelona: Coste alquiler 3.000€
* Valencia: Coste alquiler 2.000€

**Mensual y automático** → Sin cálculo manual cada mes.

Caso 2: Empleado multi-proyecto
================================

**Escenario:** Empleado trabaja en varios proyectos simultáneamente.

**Configuración:**

Etiqueta: DIST-MARIA-LOPEZ::

    PROYECTO-A: 60%
    PROYECTO-B: 30%
    PROYECTO-C: 10%

**Nómina mensual:**

.. code-block:: text

    Empleado: María López
    Salario bruto: 3.500€
    Seguridad Social: 1.050€
    Total coste: 4.550€
    
    Etiqueta: DIST-MARIA-LOPEZ

**Distribución automática:**

.. code-block:: text

    PROYECTO-A: 2.730€ (60%)
    PROYECTO-B: 1.365€ (30%)
    PROYECTO-C: 455€ (10%)

**Análisis de rentabilidad:**

* Proyecto A conoce coste real de María: 2.730€/mes
* Proyecto B conoce coste real de María: 1.365€/mes
* Proyecto C conoce coste real de María: 455€/mes

Caso 3: Servicios comunes por departamento
===========================================

**Escenario:** Electricidad compartida entre departamentos.

**Configuración:**

Etiqueta: DIST-ELECTRICIDAD::

    DPTO-PRODUCCION: 60% (mayor consumo)
    DPTO-OFICINAS: 25%
    DPTO-ALMACEN: 15%

**Factura eléctrica:**

.. code-block:: text

    Compañía: Iberdrola
    Período: Octubre 2025
    Importe: 8.500€
    Etiqueta: DIST-ELECTRICIDAD

**Reparto:**

.. code-block:: text

    Producción: 5.100€ (60%)
    Oficinas: 2.125€ (25%)
    Almacén: 1.275€ (15%)

**Dashboard departamental:**

* Producción ve su coste real de electricidad
* Comparativa mensual por departamento
* Base para facturación interna

Caso 4: Proyecto con subcontratación
=====================================

**Escenario:** Proyecto principal con sub-proyectos.

**Configuración:**

Etiqueta: DIST-PROYECTO-PRINCIPAL::

    SUB-PROYECTO-1: 40%
    SUB-PROYECTO-2: 35%
    SUB-PROYECTO-3: 25%

**Factura de coordinación:**

.. code-block:: text

    Concepto: Gestión proyecto principal
    Importe: 5.000€
    Etiqueta: DIST-PROYECTO-PRINCIPAL

**Reparto a sub-proyectos:**

.. code-block:: text

    SUB-PROYECTO-1: 2.000€ (40%)
    SUB-PROYECTO-2: 1.750€ (35%)
    SUB-PROYECTO-3: 1.250€ (25%)

**Ventaja:** Costes comunes distribuidos proporcionalmente.

Caso 5: Cambio mensual de distribución
=======================================

**Escenario:** Distribución varía según actividad mensual.

**Septiembre 2025:**

Etiqueta: DIST-SOPORTE-IT::

    OFICINA-A: 70% (proyecto grande)
    OFICINA-B: 30%

**Octubre 2025 (proyecto finalizado):**

Actualizar distribución::

    OFICINA-A: 40%
    OFICINA-B: 60% (nuevo proyecto)

**Aplicación:**

* Facturas septiembre: Distribución 70/30
* Facturas octubre: Distribución 40/60

**Flexibilidad:** Ajustar distribución según necesidad mensual.

Caso 6: Distribución compleja multi-nivel
==========================================

**Escenario:** Coste se distribuye a regiones, y luego a oficinas.

**Nivel 1 - Etiqueta: DIST-REGION-SUR**

::

    REGION-VALENCIA: 60%
    REGION-MURCIA: 40%

**Nivel 2 - Etiqueta: DIST-OFICINAS-VALENCIA**

::

    OFICINA-VALENCIA-CENTRO: 70%
    OFICINA-VALENCIA-SUR: 30%

**Aplicación manual:**

1. Factura: 10.000€

2. Primera distribución (DIST-REGION-SUR)::

    VALENCIA: 6.000€
    MURCIA: 4.000€

3. Crear asiento manual para VALENCIA

4. Segunda distribución (DIST-OFICINAS-VALENCIA)::

    VALENCIA-CENTRO: 4.200€ (70% de 6.000€)
    VALENCIA-SUR: 1.800€ (30% de 6.000€)

**Nota:** Distribución anidada requiere pasos manuales.

Caso 7: Comparativa presupuesto vs. real
=========================================

**Escenario:** Presupuesto distribuido, comparar con real.

**Presupuesto anual alquiler:** 120.000€

Distribución presupuestada::

    MADRID: 60.000€ (50%)
    BARCELONA: 36.000€ (30%)
    VALENCIA: 24.000€ (20%)

**Real ejecutado (usando DIST-ALQUILER):**

Acumulado 10 meses::

    MADRID: 52.000€ (52%)
    BARCELONA: 28.000€ (28%)
    VALENCIA: 20.000€ (20%)

**Análisis:**

* Madrid: +3,3% sobre presupuesto
* Barcelona: -6,7% bajo presupuesto
* Valencia: En presupuesto

**Ajuste:** Renegociar distribución para Q4.

Caso 8: Validación de suma incorrecta
======================================

**Escenario:** Error al configurar distribución.

**Intento de configuración:**

Etiqueta: DIST-ERROR::

    CUENTA-A: 50%
    CUENTA-B: 30%
    CUENTA-C: 15%

**Al guardar:**

❌ **Error de Validación:**

.. code-block:: text

    La distribución debe sumar 100%.
    Suma actual: 95%
    
    Por favor, revise los porcentajes.

**Corrección:**

::

    CUENTA-A: 50%
    CUENTA-B: 30%
    CUENTA-C: 20%
    Total: 100% ✅

**Validación automática** previene errores.

Caso 9: Reporte de distribuciones activas
==========================================

**Consultar todas las distribuciones configuradas:**

1. Ir a **Etiquetas Analíticas**

2. Filtrar::

    Distribución Analítica: Sí

3. **Resultado:**

.. code-block:: text

    Etiquetas con distribución:
    
    DIST-ALQUILER (3 cuentas)
    DIST-ELECTRICIDAD (3 cuentas)
    DIST-MARIA-LOPEZ (3 cuentas)
    DIST-SOPORTE-IT (2 cuentas)
    DIST-PROYECTO-A (4 cuentas)

**Revisar periódicamente:**

* Actualizar porcentajes si necesario
* Eliminar distribuciones obsoletas
* Crear nuevas según necesidad

Caso 10: Facturación interna con distribución
==============================================

**Escenario:** Facturación interna entre departamentos.

**Configuración:**

Departamento IT factura servicios internos::

    Etiqueta: DIST-SERVICIOS-IT
    
    DPTO-VENTAS: 40%
    DPTO-PRODUCCION: 35%
    DPTO-ADMINISTRACION: 25%

**Factura interna mensual:**

.. code-block:: text

    Concepto: Servicios IT Octubre
    Importe: 5.000€
    Etiqueta: DIST-SERVICIOS-IT

**Cada departamento ve su coste:**

.. code-block:: text

    Ventas: 2.000€ (40%)
    Producción: 1.750€ (35%)
    Administración: 1.250€ (25%)

**Ventaja:** Transparencia en costes de servicios compartidos.

Caso 11: Distribución por actividad real
=========================================

**Escenario:** Ajustar distribución según uso real.

**Análisis de consumo eléctrico real (medidores):**

.. code-block:: text

    Producción: 6.200 kWh (63%)
    Oficinas: 2.400 kWh (24%)
    Almacén: 1.300 kWh (13%)
    Total: 9.900 kWh

**Actualizar etiqueta DIST-ELECTRICIDAD:**

Antes (estimado)::

    Producción: 60%
    Oficinas: 25%
    Almacén: 15%

Ahora (real)::

    Producción: 63%
    Oficinas: 24%
    Almacén: 13%

**Resultado:** Distribución ajustada a consumo real medido.
