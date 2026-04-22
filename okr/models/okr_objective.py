from odoo import api, fields, models


class OKRObjective(models.Model):
    _name = "okr.objective"
    _description = "OKR Objective"

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description", required=True)
    okr_id = fields.Many2one("okr", string="OKR", required=True)
    key_result_ids = fields.One2many(
        "okr.key_result", "objective_id", string="Key Results"
    )
    cadence = fields.Selection(
        [
            ("q1", "Quarterly Q1"),
            ("q2", "Quarterly Q2"),
            ("q3", "Quarterly Q3"),
            ("q4", "Quarterly Q4"),
            ("yearly", "Yearly"),
        ],
        string="Cadence",
        default="q1",
    )
    in_charge_id = fields.Many2one("res.users", string="In Charge")
    start_date = fields.Date(string="Start Date", readonly=True)
    end_date = fields.Date(string="End Date", readonly=True)
    type = fields.Selection(
        [
            ("committed", "Committed"),
            ("aspirational", "Aspirational"),
        ],
        string="Type",
        required=True,
    )
    result = fields.Float(
        string="Result",
        compute="_compute_result",
        digits=(16, 2),
    )

    @api.depends("key_result_ids.result")
    def _compute_result(self):
        for objective in self:
            if objective.key_result_ids:
                # Se calcula la media ponderada de los resultados de los key results respecto al peso que representan sobre el total de peso de los key results del objetivo
                total_result = sum(
                    (key_result.result / key_result.target) * key_result.weight
                    for key_result in objective.key_result_ids
                )
                objective.result = (
                    total_result
                    / sum(key_result.weight for key_result in objective.key_result_ids)
                ) * 100
            else:
                objective.result = 0.0
