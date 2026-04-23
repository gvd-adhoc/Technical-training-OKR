from odoo.exceptions import ValidationError
from odoo.tools import date_utils

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
    start_date = fields.Date(string="Start Date", compute="_compute_period")
    end_date = fields.Date(string="End Date", compute="_compute_period")
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
                objective.result = total_result / sum(
                    key_result.weight for key_result in objective.key_result_ids
                )
            else:
                objective.result = 0.0

    @api.depends("cadence")
    def _compute_period(self):
        today = fields.Date.today()
        current_month = today.month
        next_year = today.replace(year=today.year + 1)

        # Trimestre actual
        current_q = (current_month - 1) // 3
        cadence_map = {"q1": 0, "q2": 1, "q3": 2, "q4": 3}

        for objective in self:
            if objective.cadence == "yearly":
                objective.start_date = date_utils.start_of(next_year, "year")
                objective.end_date = date_utils.end_of(next_year, "year")

            elif objective.okr_id.cadence == "yearly":
                base_date = date_utils.start_of(next_year, "year")
                quarter_date = date_utils.add(
                    base_date, months=3 * cadence_map.get(objective.cadence)
                )
                objective.start_date = date_utils.start_of(quarter_date, "quarter")
                objective.end_date = date_utils.end_of(quarter_date, "quarter")

            else:
                quarter = cadence_map.get(objective.cadence)
                # Diferencia entre trimestres
                diff = quarter - current_q

                # Si ya pasó o se está transitando, se pasa al siguiente año
                if diff <= 0:
                    diff += 4

                # Cálculo de fechas
                target = date_utils.add(today, months=diff * 3)
                objective.start_date = date_utils.start_of(target, "quarter")
                objective.end_date = date_utils.end_of(target, "quarter")

    @api.constrains("cadence")
    def _check_cadence(self):
        for objective in self:
            okr_cadence = objective.okr_id.cadence
            if objective.cadence == "yearly" and okr_cadence != "yearly":
                raise ValidationError(
                    "An objective with yearly cadence cannot be linked to an OKR with a different cadence."
                )
            if (
                objective.cadence != "yearly"
                and okr_cadence != "yearly"
                and okr_cadence != objective.cadence
            ):
                raise ValidationError(
                    "An objective with quarterly cadence cannot be linked to an OKR with a different cadence."
                )
