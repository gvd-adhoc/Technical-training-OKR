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

    @api.model
    def create(self, vals_list):
        key_results = self.env["okr.key_result"].search(
            [("objective_id", "=", vals_list[0].get("objective_id"))]
        )
        total_weight = sum(kr.weight for kr in key_results)
        for vals in vals_list:
            if vals.get("target") < 0 or vals.get("target") > 1:
                raise ValidationError("Key result target must be between 0 and 100.")
            total_weight += vals.get("weight")
            if total_weight > 1:
                raise ValidationError(
                    "Total weight of key results for an objective cannot exceed 100%."
                )
        return super().create(vals_list)
