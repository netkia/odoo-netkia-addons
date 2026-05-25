# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account Analytic Tag Distribution",
    "version": "18.0.1.0.0",
    "author": "Netkia, Tecnativa, Odoo Community Association (OCA)",
    "category": "Account",
    "website": "https://www.netkia.es",
    "depends": [
        "account_analytic_tag",
        "feature_toggle",
    ],
    "license": "AGPL-3",
    "data": [
        "data/ir_config_parameter.xml",
        "views/account_analytic_tag_views.xml",
    ],
    "installable": True,
    "maintainers": ["victoralmau"],
}
