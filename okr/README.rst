=================
capacitación-okr
=================

Aplicación para la gestión de OKRs (Objectives and Key Results) en Odoo. Permite definir objetivos jerárquicos con cadencia anual o trimestral, y asociar múltiples Key Results con valores de target, resultado y peso.

Características
===============
- Definición de objetivos con jerarquía (padre-hijo).
- Asignación de cadencia (anual o trimestral) a cada objetivo.
- Asociación de múltiples Key Results a cada objetivo, con campos para target, resultado y peso.
- Cálculo del progreso de cada objetivo basado en los resultados de sus Key Results.
- Interfaz intuitiva para la gestión de OKRs dentro de Odoo.

Detalles Técnicos
=================

- Modelos nuevos
  - `okr`: modelo principal para los okr, con campos para nombre, descripción, cadencia y relación padre-hijo.
  - `okr.objective`: modelo principal para los objetivos, con campos para nombre, descripción, cadencia y progreso calculado.
  - `okr.key_result`: modelo para los Key Results, con campos para nombre, descripción, target, resultado, peso y relación con el objetivo.
- Elementos técnicos adicionales
  - Seguridad: `security/ir.model.access.csv`, `security/res_group.xml`.

Autor
=====

ADHOC SA

Licencia
========

AGPL-3
