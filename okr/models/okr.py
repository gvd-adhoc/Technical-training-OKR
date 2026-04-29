from odoo.exceptions import ValidationError
from odoo.tools import date_utils

from odoo import api, fields, models


class Okr(models.Model):
    _name = "okr"
    _description = "OKR"

    name = fields.Char(string="Name", required=True)
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
    company_ids = fields.Many2many(
        "res.company",
        string="Company",
        default=lambda self: [(6, 0, [self.env.company.id])],
    )
    team_ids = fields.Many2many("hr.department", string="Teams")
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    cadence = fields.Selection(
        [
            ("q1", "Quarterly Q1"),
            ("q2", "Quarterly Q2"),
            ("q3", "Quarterly Q3"),
            ("q4", "Quarterly Q4"),
            ("yearly", "Yearly"),
        ],
        string="Cadence",
        default="yearly",
    )
    year = fields.Char(string="Year", default=fields.Date.today().year)
    in_charge_id = fields.Many2one("res.users", string="In Charge")
    start_date = fields.Date(
        string="Start Date", compute="_compute_period", store=True, recursive=True
    )
    end_date = fields.Date(
        string="End Date", compute="_compute_period", store=True, recursive=True
    )
    parent_id = fields.Many2one("okr", string="Parent OKR")
    child_ids = fields.One2many("okr", "parent_id", string="Child OKRs")
    child_count = fields.Integer(compute="_compute_child_count")

    @api.depends("child_ids")
    def _compute_child_count(self):
        """Compute the number of child OKRs for each OKR."""
        for okr in self:
            okr.child_count = len(okr.child_ids)

    @api.depends("cadence", "year", "parent_id.start_date", "parent_id.end_date")
    def _compute_period(self):
        """Compute the start and end dates based on the cadence."""
        today = fields.Date.today()
        current_month = today.month

        # Current quarter
        current_q = (current_month - 1) // 3
        cadence_map = {"q1": 0, "q2": 1, "q3": 2, "q4": 3}

        for okr in self:
            cadence = okr.parent_id.cadence if okr.parent_id else okr.cadence
            year = okr.parent_id.year if okr.parent_id else okr.year
            if cadence == "yearly":
                if year:
                    okr_date = today.replace(year=int(year))
                else:
                    okr_date = today.replace(year=today.year + 1)
                okr.start_date = date_utils.start_of(okr_date, "year")
                okr.end_date = date_utils.end_of(okr_date, "year")

            # If it's a parent OKR, it should be annual
            elif not okr.parent_id:
                raise ValidationError(
                    "An OKR without a parent cannot have a quarterly cadence."
                )
            else:
                quarter = cadence_map.get(cadence)

                # If the OKR has a parent with a defined year, use it to calculate the quarter dates
                if okr.parent_id.year:
                    parent_year = int(okr.parent_id.year)
                    base_date = date_utils.start_of(today, "year").replace(
                        year=parent_year
                    )
                    target = date_utils.add(base_date, months=quarter * 3)
                    okr.start_date = date_utils.start_of(target, "quarter")
                    okr.end_date = date_utils.end_of(target, "quarter")

                else:
                    # The quarter that corresponds to the current date is assigned
                    # Difference between quarters
                    diff = quarter - current_q

                    # If it has already passed or is currently ongoing, move to the next year
                    if diff <= 0:
                        diff += 4

                    # Date calculation
                    target = date_utils.add(today, months=diff * 3)
                    okr.start_date = date_utils.start_of(target, "quarter")
                    okr.end_date = date_utils.end_of(target, "quarter")
            okr.year = year

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

    @api.constrains("parent_id")
    def _check_no_recursive_relationship(self):
        """Check that there are no recursive relationships between parent and child OKRs.
        Raises:
            ValidationError: If a recursive relationship is detected.
        """
        for okr in self:
            parent = okr.parent_id
            while parent:
                if parent == okr:
                    raise ValidationError(
                        "Recursive OKR relationships are not allowed."
                    )
                parent = parent.parent_id or False
            # parent = okr.parent_id
            # if parent:
            #     if okr.start_date < parent.start_date:
            #         raise ValidationError(
            #             "Child OKRs cannot have a start date earlier than their parent OKR."
            #         )
            #     if okr.end_date > parent.end_date:
            #         raise ValidationError(
            #             "Child OKRs cannot have an end date later than their parent OKR."
            #         )

    @api.constrains("year")
    def _check_year(self):
        """Check that the year of the OKR is valid.
        Raises:
            ValidationError: If the year is not a number.
            ValidationError: If the year is not within the valid range.
        """
        actual_year = fields.Date.today().year
        for rec in self:
            if rec.year:
                if not rec.year.isdigit():
                    raise ValidationError("Year must be a number.")
            input_year = int(rec.year)
            if input_year < actual_year or input_year > (actual_year + 10):
                raise ValidationError("Year must be valid.")

    def action_view_child_okrs(self):
        """View child OKRs of the current OKR.
        Returns:
            dict: Action dictionary to open the child OKRs in a new window.
        """
        list_view_id = self.env.ref("okr.okr_list_view").id
        form_view_id = self.env.ref("okr.okr_form_view").id
        return {
            "name": ("Child OKRs"),
            "view_mode": "list, form",
            "type": "ir.actions.act_window",
            "res_model": "okr",
            "views": [(list_view_id, "list"), (form_view_id, "form")],
            "domain": [("parent_id", "=", self.id)],
        }

    @api.ondelete(at_uninstall=False)
    def _on_delete(self):
        """Handle the deletion of OKRs by unlinking related objectives and child OKRs."""
        for okr in self:
            if okr.objective_ids:
                for objective in okr.objective_ids:
                    objective.okr_id = False
            if okr.child_ids:
                for child in okr.child_ids:
                    child.parent_id = False
