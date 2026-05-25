Instalación
===========

1. Instalar módulo **account_analytic_tag_distribution**

2. **Dependencias automáticas:**
   
   * ``account_analytic_tag`` - Sistema de etiquetas analíticas
   * ``feature_toggle`` - Sistema de control de funcionalidades

3. Actualizar lista de aplicaciones

Parámetro del sistema
=====================

Este módulo utiliza un parámetro del sistema para controlar su funcionalidad:

**Parámetro:** ``analytic.tag_distribution``

* **Valor:** ``1`` (activado) o ``0`` (desactivado)
* **Ubicación:** Ajustes → Técnico → Parámetros del Sistema
* **Efecto:** 
  - ``1``: Las etiquetas analíticas pueden tener distribución analítica y controlar apuntes analíticos
  - ``0``: Comportamiento estándar de Odoo (etiquetas sin distribución)

**Activar la funcionalidad:**

1. Ir a **Ajustes → Técnico → Parámetros del Sistema**
2. Crear/editar parámetro ``analytic.tag_distribution``
3. Establecer valor a ``1``
4. Refrescar el navegador si es necesario
5. El campo "Distribución Analítica" aparecerá en las etiquetas analíticas

Crear etiqueta con distribución
================================

**Paso 1: Crear etiqueta analítica**

1. Ir a **Contabilidad → Configuración → Analítica → Etiquetas Analíticas**

2. Crear nueva etiqueta::

    Nombre: DIST-OFICINAS
    Color: Azul

3. Marcar checkbox **"Distribución Analítica"**: ✅

**Paso 2: Configurar distribución**

1. Campo **"Distribución Analítica"** aparece

2. Añadir cuentas y porcentajes::

    OFICINA-MADRID: 50%
    OFICINA-BARCELONA: 30%
    OFICINA-VALENCIA: 20%

3. **Sistema valida automáticamente:**

   * Suma debe ser 100%
   * Si suma ≠ 100% → Error al guardar

4. Guardar

Verificación post-instalación
==============================

**Test 1: Crear etiqueta con distribución**

1. Crear etiqueta "TEST-DIST"

2. Marcar "Distribución Analítica"

3. Configurar::

    CUENTA-A: 60%
    CUENTA-B: 40%

4. Guardar

5. ✅ Debe guardarse correctamente (suma = 100%)

**Test 2: Validación de suma**

1. Crear etiqueta "TEST-ERROR"

2. Marcar "Distribución Analítica"

3. Configurar::

    CUENTA-A: 60%
    CUENTA-B: 30%

4. Intentar guardar

5. ❌ Error: "La distribución debe sumar 100%. Suma actual: 90%"

**Test 3: Aplicar en factura**

1. Crear factura proveedor

2. Línea::

    Cuenta: 621000 - Alquileres
    Importe: 1.000€
    Etiqueta Analítica: TEST-DIST

3. Validar factura

4. **Verificar apuntes analíticos:**

   * Contabilidad → Analítica → Apuntes
   * Buscar factura
   * ✅ Deben existir 2 apuntes:
     - CUENTA-A: 600€ (60%)
     - CUENTA-B: 400€ (40%)

Plantillas de distribución comunes
===================================

**Ejemplo 1: Distribución por oficinas**

::

    Nombre: DIST-ALQUILER-OFICINAS
    
    OFICINA-MADRID: 45%
    OFICINA-BARCELONA: 35%
    OFICINA-VALENCIA: 20%

**Ejemplo 2: Distribución por departamentos**

::

    Nombre: DIST-SERVICIOS-COMUNES
    
    DPTO-VENTAS: 30%
    DPTO-PRODUCCION: 40%
    DPTO-ADMINISTRACION: 20%
    DPTO-IT: 10%

**Ejemplo 3: Distribución por proyectos**

::

    Nombre: DIST-EMPLEADO-MARIA
    
    PROYECTO-A: 60%
    PROYECTO-B: 30%
    PROYECTO-C: 10%

**Ejemplo 4: Distribución temporal**

::

    Nombre: DIST-Q1-2025
    
    ENERO: 35%
    FEBRERO: 33%
    MARZO: 32%

Modificar distribución existente
=================================

**Cambiar porcentajes:**

1. Abrir etiqueta con distribución

2. Modificar porcentajes::

    Antes:
    - MADRID: 50%
    - BARCELONA: 30%
    - VALENCIA: 20%
    
    Ahora:
    - MADRID: 40%
    - BARCELONA: 40%
    - VALENCIA: 20%

3. Validar suma = 100%

4. Guardar

**Añadir nueva cuenta:**

1. Añadir línea::

    OFICINA-SEVILLA: 10%

2. Ajustar otras para que sumen 100%::

    MADRID: 35%
    BARCELONA: 30%
    VALENCIA: 15%
    SEVILLA: 10%
    (Debe sumar 90% todavía... error!)

3. Corregir::

    MADRID: 35%
    BARCELONA: 30%
    VALENCIA: 20%
    SEVILLA: 15%
    = 100% ✅

Desactivar distribución
========================

**Para convertir etiqueta normal en distribución:**

1. Marcar "Distribución Analítica": ✅

2. Configurar porcentajes

**Para convertir distribución en etiqueta normal:**

1. Desmarcar "Distribución Analítica": ❌

2. Campo de distribución desaparece

3. Guardar

**Comportamiento anterior se mantiene** en apuntes ya creados.
