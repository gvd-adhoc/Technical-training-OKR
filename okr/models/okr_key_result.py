from odoo import fields, models


class OKRKeyResult(models.Model):
    _name = "okr.key_result"
    _description = "OKR Key Result"

    description = fields.Text(string="Description", required=True)
    objective_id = fields.Many2one("okr.objective", string="Objective", required=True)
    result = fields.Float(
        string="Result",
        digits=(16, 2),
        readonly=True,
    )
    target = fields.Float(string="Target", digits=(16, 2), default=100.0)
    weight = fields.Float(string="Weight", digits=(16, 2), default=0.0)
    in_charge_id = fields.Many2one("res.users", string="In Charge")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("cancelled", "Cancelled"),
            ("done", "Done"),
        ],
        string="State",
        default="draft",
    )
