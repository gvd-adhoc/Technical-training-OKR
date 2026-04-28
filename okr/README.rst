=================
okr-training
=================

Application for OKR (Objectives and Key Results) management in Odoo. It allows defining hierarchical objectives with annual or quarterly cadence, and associating multiple Key Results with target, result, and weight values.

Features
===============
- Definition of objectives with hierarchy (parent-child).
- Assignment of cadence (yearly or quarterly) to each objective.
- Association of multiple Key Results to each objective, with fields for target, result, and weight.
- Calculation of each objective’s progress based on the results of its Key Results.
- Intuitive interface for managing OKRs within Odoo.

Technical Details
=================

- New models
  - `okr`: main model for OKRs, with fields for name, description, cadence, and parent-child relationship.
  - `okr.objective`: main model for objectives, with fields for name, description, cadence, and calculated progress.
  - `okr.key_result`: model for Key Results, with fields for name, description, target, result, weight, and relationship to the objective.
- Included views
  - OKRs: `views/okr_views.xml` for OKR management.
  - Objectives: `views/okr_objective_views.xml` for objective management.
  - Key Results: `views/okr_key_result_views.xml` for Key Result management.
- Additional technical elements
  - Cron: `data/cron.xml` for periodic objective progress updates.
  - Security: `security/ir.model.access.csv`, `security/res_group.xml`, and `security/ir_rule.xml` for access permission management.

Usage
===
1. Install the OKR module in Odoo.
2. Access the OKR menu to create and manage objectives and Key Results.
3. Define the OKR hierarchy.
4. Assign Key Results with their respective target, result, and weight values.
5. Monitor each objective’s progress based on the results of its Key Results.

Architecture
============
- `models/`: new models (`okr.*`).
- `views/`: views for managing OKRs, objectives, and Key Results.
- `data/` + `security/`: cron for progress updates and security files for access permissions.

Dependencies
============
- base
- hr

Author
=====

ADHOC SA

License
========

AGPL-3
