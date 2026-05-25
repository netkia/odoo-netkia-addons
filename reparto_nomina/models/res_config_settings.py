# Copyright 2020 Ingeos (<http://www.ingeos.es>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.feature_toggle import feature


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    employee_account_analytic_tag_id = fields.Many2one("account.analytic.tag")

    @api.model
    @feature(fallback=lambda self: super(ResConfigSettings, self).get_values())
    def get_values(self):
        res = super().get_values()
        tag = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("reparto_nomina.employee_account_analytic_tag_id")
        )
        if tag:
            res.update(
                {"employee_account_analytic_tag_id": int(tag)},
            )
        return res

    @feature(fallback=lambda self: super(ResConfigSettings, self).set_values())
    def set_values(self):
        res = super().set_values()
        param = self.env["ir.config_parameter"].sudo()
        employee_analytic_tag = (
            self.employee_account_analytic_tag_id
            and self.employee_account_analytic_tag_id.id
            or False
        )
        self.env["ir.default"].sudo().set(
            "res.config.settings",
            "employee_account_analytic_tag_id",
            employee_analytic_tag,
        )
        param.set_param(
            "reparto_nomina.employee_account_analytic_tag_id", employee_analytic_tag
        )
        return res
