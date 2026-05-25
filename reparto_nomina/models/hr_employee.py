# Copyright 2020 Ingeos (<http://www.ingeos.es>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    account_analytic_tag_id = fields.Many2one("account.analytic.tag")
    payroll_code = fields.Char(size=9)

    _sql_constraints = [
        (
            "payroll_code_unique",
            "unique(payroll_code)",
            "Payroll code already exists!",
        )
    ]
