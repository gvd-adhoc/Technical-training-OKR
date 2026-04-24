from odoo.exceptions import ValidationError
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
    start_date = fields.Date(string="Start Date", compute="_compute_period", store=True)
    end_date = fields.Date(string="End Date", compute="_compute_period", store=True)
    parent_id = fields.Many2one("okr", string="Parent OKR")
    child_ids = fields.One2many("okr", "parent_id", string="Child OKRs")

    @api.depends("cadence")
    def _compute_period(self):
        """
        Compute the start and end dates based on the cadence.
        """
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

    @api.constrains("cadence")
    def _check_cadence(self):
        """Check that the cadence of the OKR matches the cadence of its objectives, parent OKR, and child OKRs.
        Raises:
            ValidationError: If an OKR with quarterly cadence is linked to an objective with a different cadence.
            ValidationError: If an OKR with quarterly cadence is linked to a parent OKR with a different cadence.
            ValidationError: If an OKR with quarterly cadence is linked to a child OKR with a different cadence.
            ValidationError: If an OKR with yearly cadence is linked to a parent OKR with a different cadence.
        """
        for okr in self:
            if okr.cadence != "yearly":
                if okr.objective_ids and any(
                    okr.cadence != obj.cadence for obj in okr.objective_ids
                ):
                    raise ValidationError(
                        "An OKR with quarterly cadence cannot be linked to an objective with a different cadence."
                    )

                if (
                    okr.parent_id
                    and okr.parent_id.cadence != "yearly"
                    and okr.parent_id.cadence != okr.cadence
                ):
                    raise ValidationError(
                        "An OKR cannot have a different quarterly cadence than its parent OKR."
                    )

                if okr.child_ids and any(
                    okr.cadence != child.cadence for child in okr.child_ids
                ):
                    raise ValidationError(
                        "An OKR cannot have a different quarterly cadence than its child OKRs."
                    )
            else:
                if okr.parent_id and okr.parent_id.cadence != "yearly":
                    raise ValidationError(
                        "An OKR with yearly cadence cannot have a parent OKR with a different cadence."
                    )

    @api.constrains("child_ids")
    def _check_child_parent(self):
        """
        Check that there are no recursive relationships between parent and child OKRs and that child OKRs have valid start and end dates.
        Raises:
            ValidationError: If a recursive relationship is detected.
            ValidationError: If a child OKR has a start date earlier than its parent OKR.
            ValidationError: If a child OKR has an end date later than its parent OKR
        """
        for okr in self:
            parent = okr.parent_id
            while parent:
                if parent in okr.child_ids:
                    raise ValidationError(
                        "Recursive OKR relationships are not allowed."
                    )
                parent = parent.parent_id or False
            if any(child.start_date < okr.start_date for child in okr.child_ids):
                raise ValidationError(
                    "Child OKRs cannot have a start date earlier than their parent OKR."
                )
            if any(child.end_date > okr.end_date for child in okr.child_ids):
                raise ValidationError(
                    "Child OKRs cannot have an end date later than their parent OKR."
                )

    @api.ondelete(at_uninstall=False)
    def _on_delete(self):
        """
        Handle the deletion of OKRs by unlinking related objectives and child OKRs.
        """
        for okr in self:
            if okr.objective_ids:
                for objective in okr.objective_ids:
                    objective.okr_id = False
            if okr.child_ids:
                for child in okr.child_ids:
                    child.parent_id = False
