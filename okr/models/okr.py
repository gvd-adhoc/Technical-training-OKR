from odoo import fields, models


class Okr(models.Model):
    _name = "okr"
    _description = "OKR"

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
    start_date = fields.Date(string="Start Date", readonly=True)
    end_date = fields.Date(string="End Date", readonly=True)
    parent_id = fields.Many2one("okr", string="Parent OKR")
    child_ids = fields.One2many("okr", "parent_id", string="Child OKRs")
