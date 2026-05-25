{
    "name": "Reparto de Nómina",
    "summary": """
        Este módulo actualiza la etiqueta de reparto de nómina configurada
        para el proceso mediante la lectura de un
        Excel con los Costes de empresa de los empleados y en base al reparto
        analítico a cada centro de coste indicado en cada uno de ellos.\n
       """,
    "author": "Netkia",
    "license": "AGPL-3",
    "website": "https://gitlab.netkia.es/odoo/netkia",
    "category": "Generic Modules/Human Resources",
    "version": "18.0.1.0.0",
    "depends": [
        "hr",
        "account",
        "feature_toggle",
        "account_analytic_tag_distribution",
    ],
    "data": [
        "data/ir_config_parameter.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/hr_employee_views.xml",
        "wizard/payroll_distribution_process_wiz_views.xml",
    ],
    "installable": True,
}
