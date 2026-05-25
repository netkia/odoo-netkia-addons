Mejoras planificadas v18.0.2.0.0
=================================

* **Distribución dinámica:**
  
  * Actualización automática de porcentajes según uso real
  * Integración con medidores (electricidad, m², horas)
  * Recálculo mensual automático
  * Histórico de evolución de porcentajes

* **Validaciones avanzadas:**
  
  * Warning si porcentaje cambia >20% respecto anterior
  * Bloqueo de distribuciones con cuenta inactiva
  * Validación cruzada con presupuestos
  * Aprobación workflow para cambios significativos

* **Plantillas y copias:**
  
  * Biblioteca de plantillas predefinidas
  * Copiar distribución de otra etiqueta
  * Aplicar plantilla a múltiples etiquetas
  * Importar/exportar distribuciones

* **Distribución anidada:**
  
  * Múltiples niveles de distribución automáticos
  * Cascada de distribuciones
  * Ejemplo: Región → Ciudad → Oficina
  * Sin necesidad de pasos manuales

* **Dashboard de análisis:**
  
  * Vista de todas las distribuciones activas
  * Gráfico de evolución de porcentajes
  * Comparativa presupuesto vs. real por etiqueta
  * Alertas de desviaciones

* **Automatización temporal:**
  
  * Cambio programado de distribución
  * Distribuciones por temporada
  * Calendario de cambios
  * Notificaciones de cambios próximos

* **Integración con reportes:**
  
  * Informe de costes distribuidos
  * Detalle de origen de cada distribución
  * Trazabilidad completa
  * Exportación a Excel con desglose

* **Validación de coherencia:**
  
  * Detectar cuentas sin uso en distribución
  * Sugerencias de optimización
  * Análisis de distribuciones redundantes
  * Limpieza automática de obsoletas

* **Distribución por período:**
  
  * Porcentajes diferentes por mes/trimestre
  * Distribución estacional
  * Cambios automáticos según calendario
  * Histórico de distribuciones anteriores

* **Multi-moneda:**
  
  * Soporte para distribuciones en diferentes monedas
  * Conversión automática
  * Redondeo configurable por moneda

* **API y webhooks:**
  
  * API para actualizar distribuciones externamente
  * Webhooks de cambios de distribución
  * Integración con sistemas externos
  * Sincronización bidireccional

Limitaciones actuales
======================

* Porcentajes estáticos (no dinámicos según uso)
* Sin distribución anidada automática
* No guarda histórico de cambios de porcentajes
* Sin validación de variaciones significativas
* No permite distribuciones temporales/estacionales
* Sin plantillas predefinidas
* No detecta distribuciones obsoletas
* Sin workflow de aprobación para cambios
* No integra con medidores reales (kWh, m², etc.)
* Redondeo puede causar diferencias de céntimos
