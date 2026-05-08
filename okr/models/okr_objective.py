from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import date_utils


class OKRObjective(models.Model):
    _name = "okr.objective"
    _description = "OKR Objective"

    name = fields.Char(required=True)
    description = fields.Text(required=True)
    okr_id = fields.Many2one("okr", default=False, string="OKR")
    key_result_ids = fields.One2many("okr.key_result", "objective_id", string="Key Results")
    cadence = fields.Selection(
        [
            ("q1", "Quarterly Q1"),
            ("q2", "Quarterly Q2"),
            ("q3", "Quarterly Q3"),
            ("q4", "Quarterly Q4"),
            ("yearly", "Yearly"),
        ],
        default="q1",
    )
    in_charge_id = fields.Many2one("res.users", string="In Charge")
    start_date = fields.Date(compute="_compute_period", store=True, recursive=True)
    end_date = fields.Date(compute="_compute_period", store=True, recursive=True)
    type = fields.Selection(
        [
            ("committed", "Committed"),
            ("aspirational", "Aspirational"),
        ],
        required=True,
    )
    result = fields.Float(
        compute="_compute_result",
    )

    @api.depends("key_result_ids.result", "key_result_ids.state", "key_result_ids.target", "key_result_ids.weight")
    def _compute_result(self):
        """Compute the result of the objective based on its key results.
        The result is calculated as the weighted average of the results of the active key results.
        """
        for objective in self:
            if objective.key_result_ids:
                # The weighted average of the key results is calculated with respect to the weight they represent on the total weight of the key results of the objective.
                active_kr = objective.key_result_ids.filtered(lambda kr: kr.state == "active")
                if active_kr:
                    total_result = sum((kr.result / kr.target) * kr.weight for kr in active_kr)
                    objective.result = total_result / sum(kr.weight for kr in active_kr)
                else:
                    objective.result = 0.0
            else:
                objective.result = 0.0

    @api.depends("cadence", "okr_id.start_date", "okr_id.end_date")
    def _compute_period(self):
        """Compute the start and end dates based on the cadence."""
        today = fields.Date.today()
        current_month = today.month

        # Current quarter
        current_q = (current_month - 1) // 3
        cadence_map = {"q1": 0, "q2": 1, "q3": 2, "q4": 3}

        for objective in self:
            okr_year = (
                int(objective.okr_id.start_date.year)
                if objective.okr_id and objective.okr_id.start_date
                else today.year + 1
            )
            okr_date = today.replace(year=okr_year)
            # If the objective has a yearly cadence, its period is the year of the OKR it belongs to.
            if objective.cadence == "yearly":
                objective.start_date = date_utils.start_of(okr_date, "year")
                objective.end_date = date_utils.end_of(okr_date, "year")
            # If the objective has a quarterly cadence, its period is the quarter of the OKR it belongs to that corresponds to its cadence.
            elif objective.okr_id:
                base_date = date_utils.start_of(okr_date, "year")
                quarter_date = date_utils.add(base_date, months=3 * cadence_map.get(objective.cadence))
                objective.start_date = date_utils.start_of(quarter_date, "quarter")
                objective.end_date = date_utils.end_of(quarter_date, "quarter")
            # If the objective does not belong to any OKR, the quarter that corresponds according to the current date is assigned.
            else:
                quarter = cadence_map.get(objective.cadence)
                # Difference between quarters
                diff = quarter - current_q

                # If it has already passed or is currently ongoing, move to the next year
                if diff <= 0:
                    diff += 4

                # Date calculation
                target = date_utils.add(today, months=diff * 3)
                objective.start_date = date_utils.start_of(target, "quarter")
                objective.end_date = date_utils.end_of(target, "quarter")

    @api.constrains("cadence")
    def _check_cadence(self):
        """Check that the cadence of the objective matches the cadence of its OKR.
        Raises:
            ValidationError: If an objective with yearly cadence is linked to an OKR with a different cadence.
            ValidationError: If an objective with quarterly cadence is linked to an OKR with a different cadence.
        """
        for objective in self:
            if not objective.okr_id:
                continue
            okr_cadence = objective.okr_id.cadence
            if objective.cadence == "yearly" and okr_cadence != "yearly":
                raise ValidationError(
                    "An objective with yearly cadence cannot be linked to an OKR with a different cadence."
                )
            if objective.cadence != "yearly" and okr_cadence != "yearly" and okr_cadence != objective.cadence:
                raise ValidationError(
                    "An objective with quarterly cadence cannot be linked to an OKR with a different cadence."
                )

    def _cron_close_finished_objectives(self):
        """Close finished objectives based on their end date."""
        today = fields.Date.today()
        objectives = self.search([("end_date", "<", today)])

        for obj in objectives:
            obj.key_result_ids.write({"state": "done"})

    @api.ondelete(at_uninstall=False)
    def _on_delete(self):
        """Handle the deletion of objectives by unlinking related key results."""
        for objective in self:
            if objective.key_result_ids:
                for kr in objective.key_result_ids:
                    kr.objective_id = False
                    kr.state = "cancelled"
