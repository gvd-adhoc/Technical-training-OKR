from odoo import api, fields, models
from odoo.exceptions import ValidationError


class OKRKeyResult(models.Model):
    _name = "okr.key_result"
    _description = "OKR Key Result"

    name = fields.Char(required=True)
    description = fields.Text(required=True)
    objective_id = fields.Many2one("okr.objective", default=False, string="Objective")
    result = fields.Float(default=0)
    target = fields.Float(default=1)
    weight = fields.Float(default=0)
    in_charge_id = fields.Many2one("res.users", string="In Charge")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("cancelled", "Cancelled"),
            ("done", "Done"),
        ],
        default="draft",
    )

    _check_target = models.Constraint(
        "CHECK(target > 0)",
        "Target must be positive.",
    )

    _check_valid_result = models.Constraint(
        "CHECK(result >= 0)",
        "Result must be positive.",
    )

    @api.constrains("weight")
    def _check_weight(self):
        """Check that the weight of the key result is within the valid range and that the total weight of key results for an objective does not exceed 100%.
        Raises:
            ValidationError: If the weight of the key result is not between 0 and 100.
            ValidationError: If the total weight of key results for an objective exceeds 100%.
        """
        for kr in self:
            if kr.weight < 0 or kr.weight > 1:
                raise ValidationError("Weight must be between 0 and 100.")
            total_weight = sum(
                self.env["okr.key_result"].search([("objective_id", "=", kr.objective_id.id)]).mapped("weight")
            )
            if total_weight > 1:
                raise ValidationError("Total weight of key results for an objective cannot exceed 100%.")

    @api.constrains("target")
    def _check_target_value(self):
        for kr in self:
            if kr.target <= 0:
                raise ValidationError("Target must be pookr.cadencesitive.")

    def set_active(self):
        for kr in self:
            kr.state = "active"

    def set_cancelled(self):
        for kr in self:
            kr.state = "cancelled"

    def set_draft(self):
        for kr in self:
            kr.state = "draft"
