from odoo.exceptions import ValidationError

from odoo import api, fields, models


class OKRKeyResult(models.Model):
    _name = "okr.key_result"
    _description = "OKR Key Result"

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description", required=True)
    objective_id = fields.Many2one("okr.objective", string="Objective", required=True)
    result = fields.Float(string="Result", default=0)
    target = fields.Float(string="Target", default=1)
    weight = fields.Float(string="Weight", default=0)
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

    _check_target = models.Constraint(
        "CHECK(target >= 0 and target <= 1)",
        "Target must be between 0 and 100.",
    )

    _check_result = models.Constraint(
        "CHECK(result >= 0 and result <= 1)",
        "Result must be between 0 and 100.",
    )

    @api.constrains("weight")
    def _check_weight(self):
        for kr in self:
            if kr.weight < 0 or kr.weight > 1:
                raise ValidationError("Weight must be between 0 and 100.")
            total_weight = sum(
                self.env["okr.key_result"]
                .search([("objective_id", "=", kr.objective_id.id)])
                .mapped("weight")
            )
            if total_weight > 1:
                raise ValidationError(
                    "Total weight of key results for an objective cannot exceed 100%."
                )
