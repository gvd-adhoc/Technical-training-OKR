from odoo.tools import date_utils

from odoo import api, fields, models


class Okr(models.Model):
    _name = "okr"
    _description = "OKR"

    name = fields.Char(string="Name", required=True)
    title = fields.Char(string="Title", required=True)
    objective_ids = fields.One2many("okr.objective", "okr_id", string="Objectives")
    level = fields.Selection(
        [
            ("organization", "Organization"),
            ("team", "Team"),
            ("individual", "Individual"),
        ],
        string="Level",
        required=True,
    )
    cadence = fields.Selection(
        [
            ("q1", "Quaterly Q1"),
            ("q2", "Quaterly Q2"),
            ("q3", "Quaterly Q3"),
            ("q4", "Quaterly Q4"),
            ("yearly", "Yearly"),
        ],
        string="Cadence",
        default="yearly",
    )
    in_charge_id = fields.Many2one("res.users", string="In Charge")
    start_date = fields.Date(string="Start Date", compute="_compute_period")
    end_date = fields.Date(string="End Date", readonly=True, compute="_compute_period")
    parent_id = fields.Many2one("okr", string="Parent OKR")
    child_ids = fields.One2many("okr", "parent_id", string="Child OKRs")

    @api.depends("cadence")
    def _compute_period(self):
        today = fields.Date.today()
        current_month = today.month

        # Trimestre actual
        current_q = (current_month - 1) // 3
        cadence_map = {"q1": 0, "q2": 1, "q3": 2, "q4": 3}

        for okr in self:
            if okr.cadence == "yearly":
                next_year = today.replace(year=today.year + 1)
                okr.start_date = date_utils.start_of(next_year, "year")
                okr.end_date = date_utils.end_of(next_year, "year")

            else:
                quarter = cadence_map.get(okr.cadence)

                # Diferencia entre trimestres
                diff = quarter - current_q

                # Si ya pasó o se está transitando, se pasa al siguiente año
                if diff <= 0:
                    diff += 4

                # Cálculo de fechas
                target = date_utils.add(today, months=diff * 3)
                okr.start_date = date_utils.start_of(target, "quarter")
                okr.end_date = date_utils.end_of(target, "quarter")
