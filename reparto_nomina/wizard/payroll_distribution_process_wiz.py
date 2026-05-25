# Copyright 2020 Ingeos (<http://www.ingeos.es>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io

import xlrd
import xlwt

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import pycompat

from odoo.addons.feature_toggle import feature


def _str(cel):
    value = cel.value
    if isinstance(value, float):
        value = int(value)
    if isinstance(value, int):
        value = str(value)
    if isinstance(value, pycompat.string_types):
        value.strip()
    return value


class PayrollDistributionProcessWizMod(models.TransientModel):
    _name = "payroll.distribution.process.wiz"
    _description = "Payroll Distribution Process MOD"

    upload_file = fields.Binary(required=True)
    file_name = fields.Char()

    @feature()
    def check_data(self):
        HrEmployeeObj = self.env["hr.employee"]
        AccountAnalyticTag = self.env["account.analytic.tag"]

        if not self.upload_file:
            raise ValidationError(_("You must upload a file"))

        workbook = xlrd.open_workbook(
            filename="", file_contents=base64.b64decode(self.upload_file)
        )
        sheet_name = workbook.sheet_names()[0]
        worksheet = workbook.sheet_by_name(sheet_name)

        worksheet = workbook.sheet_by_index(0)

        # Get first row values
        first_row = []  # The row where we stock the name of the column
        for col in range(worksheet.ncols):
            first_row.append(worksheet.cell_value(3, col))

        # Transform the workbook to a list of dictionaries
        archive_lines = []
        for row in range(4, worksheet.nrows):
            elm = {}
            for col in range(worksheet.ncols):
                elm[first_row[col]] = worksheet.cell_value(row, col)

            archive_lines.append(elm)

        # Get employee_account_analytic_tag from config
        config_tag = self.env["ir.config_parameter"].sudo().get_param(
            "reparto_nomina.employee_account_analytic_tag_id"
        )
        if config_tag:
            config_tag = int(config_tag)
        config_account_analytic_tag = False
        if config_tag:
            config_account_analytic_tag = AccountAnalyticTag.browse(config_tag)

        analytic_account_ids = []

        for line in archive_lines:
            if all(key not in line for key in ["", "TRABAJADOR", "COSTE EMPRESA"]):
                raise ValidationError(_("You must upload a file with correct format"))

        if (
            not config_tag
            or not config_account_analytic_tag.active_analytic_distribution
        ):
            raise ValidationError(
                _("The payroll distribution label is missing in Configuration")
            )

        # if not config_account_analytic_tag.company_id:
        #     raise ValidationError(
        #           _('Missing to assign the company in the '
        #              'Configuration Payroll Distribution Label')
        #     )

        config_analytic_account_ids = (
            list(config_account_analytic_tag.analytic_distribution.keys())
            if config_account_analytic_tag.analytic_distribution
            else []
        )

        for line in archive_lines:
            for key in line:
                if key == "":
                    if line[key] != "":
                        employee = HrEmployeeObj.search(
                            [("payroll_code", "=", line[key])]
                        )
                        if not employee:
                            raise ValidationError(
                                _("There is no employee for code " + str(line[key]))
                            )
                        else:
                            if not employee.account_analytic_tag_id:
                                raise ValidationError(
                                    _(
                                        "The employee "
                                        + employee.name
                                        + " does not have a payroll tag indicated"
                                    )
                                )

                            for (
                                account_id
                            ) in (
                                employee.account_analytic_tag_id.analytic_distribution or {}
                            ).keys():
                                if account_id not in analytic_account_ids:
                                    analytic_account_ids.append(account_id)
                                if account_id not in config_analytic_account_ids:
                                    raise ValidationError(
                                        _(
                                            "The analytical accounts of the employees "
                                            "do not coincide with those indicated in "
                                            "the Distribution Label of the payroll"
                                        )
                                    )

        if "no_para" not in self.env.context:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Validación correcta"),
                    "message": _("El fichero es correcto"),
                    "type": "success",
                    "sticky": False,
                },
            }

    @feature()
    def update_distribution(self):
        self.with_context(no_para=True).check_data()
        HrEmployeeObj = self.env["hr.employee"]
        AccountAnalyticTagObj = self.env["account.analytic.tag"]
        first_row = []
        workbook = xlrd.open_workbook(
            filename="", file_contents=base64.b64decode(self.upload_file)
        )
        sheet_name = workbook.sheet_names()[0]
        worksheet = workbook.sheet_by_name(sheet_name)
        config_tag = self.env["ir.config_parameter"].sudo().get_param(
            "reparto_nomina.employee_account_analytic_tag_id"
        )
        if config_tag:
            config_tag = int(config_tag)
        config_account_analytic_tag = False
        if config_tag:
            config_account_analytic_tag = AccountAnalyticTagObj.browse(config_tag)

        analytic_account_ids = []

        list(
            config_account_analytic_tag.analytic_distribution.keys()
        ) if config_account_analytic_tag.analytic_distribution else []

        total_amount = 0
        distribution_values_with_percentages = {}

        for col in range(worksheet.ncols):
            first_row.append(worksheet.cell_value(3, col))
        # transform the workbook to a list of dictionaries
        archive_lines = []
        for row in range(4, worksheet.nrows):
            elm = {}
            for col in range(worksheet.ncols):
                elm[first_row[col]] = worksheet.cell_value(row, col)

            archive_lines.append(elm)

        for line in archive_lines:
            employee = HrEmployeeObj.search([("payroll_code", "=", line[""])])

            # employee.timesheet_cost = line['Coste Hora Devengada (*)']

            employee_cost_empresa = line["COSTE EMPRESA"]

            for (
                account_id,
                percentage,
            ) in (employee.account_analytic_tag_id.analytic_distribution or {}).items():
                if account_id not in analytic_account_ids:
                    analytic_account_ids.append(account_id)

                percentage_amount = 0

                # Verificamos si la cuenta está en distribution_values_with_percentages
                if account_id in distribution_values_with_percentages:
                    percentage_amount = distribution_values_with_percentages.get(
                        account_id
                    )

                # Calculamos el nuevo porcentaje basado en employee_cost_empresa
                if percentage != 0 and employee_cost_empresa != 0:
                    if employee_cost_empresa == "":
                        employee_cost_empresa = 0.00
                    percentage_amount += (employee_cost_empresa * percentage) / 100

                # Actualizamos el diccionario con el nuevo valor
                distribution_values_with_percentages.update(
                    {account_id: percentage_amount}
                )

            total_amount += employee_cost_empresa

        percentage_sum = 0

        # Hacemos una copia del diccionario para modificarlo
        new_distribution = (config_account_analytic_tag.analytic_distribution or {}).copy()

        for account_id, _current_percentage in new_distribution.items():
            percentage = 0
            if account_id in distribution_values_with_percentages:
                percentage_amount = distribution_values_with_percentages.get(account_id)
                if percentage_amount != 0 and total_amount != 0:
                    percentage = (percentage_amount * 100) / total_amount

            # Actualizamos el valor de `percentage` en la copia del diccionario
            new_distribution[account_id] = round(percentage, 2)

            percentage_sum += round(percentage, 2)

        # Ajustamos los porcentajes si la suma es mayor a 100
        if percentage_sum > 100:
            rest = percentage_sum - 100
            # Filtramos las distribuciones con porcentaje > 0
            distributions = {
                account_id: percentage
                for account_id, percentage in new_distribution.items()
                if percentage > 0
            }

            # Encontrar el registro con el porcentaje más alto
            max_record_id = max(distributions, key=distributions.get)
            new_distribution[max_record_id] -= rest  # Restamos el exceso de porcentaje

        # Ajustamos los porcentajes si la suma es menor a 100
        if percentage_sum < 100:
            rest = 100 - percentage_sum
            # Filtramos las distribuciones con porcentaje > 0
            distributions = {
                account_id: percentage
                for account_id, percentage in new_distribution.items()
                if percentage > 0
            }

            # Encontrar el registro con el porcentaje más bajo
            min_record_id = min(distributions, key=distributions.get)
            new_distribution[min_record_id] += rest  # Sumamos el porcentaje faltante

        # Escribimos el nuevo diccionario de vuelta en el campo `analytic_distribution`
        config_account_analytic_tag.write({"analytic_distribution": new_distribution})

        if "detail" in self.env.context:
            return archive_lines

        return {
            "name": _("Account Analytic Tag"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.analytic.tag",
            "res_id": config_account_analytic_tag.id,
            "domain": [("id", "=", config_account_analytic_tag.id)],
            "target": "current",
        }

    def update_distribution_detail(self):
        # Actualiza la distribución con detalle
        res = self.with_context(detail=True).update_distribution()
        HrEmployeeObj = self.env["hr.employee"]

        # Creación del libro de Excel en memoria
        workbookexport = xlwt.Workbook({"in_memory": True})
        # Creación de la hoja de Excel
        sheetreport = workbookexport.add_sheet(
            "Detalle de reparto", cell_overwrite_ok=True
        )
        # Apertura del libro de Excel a partir del archivo subido
        workbook = xlrd.open_workbook(
            filename="", file_contents=base64.b64decode(self.upload_file)
        )
        # Obtención del nombre de la primera hoja
        sheet_name = workbook.sheet_names()[0]
        # Obtención de la hoja por nombre
        workbook.sheet_by_name(sheet_name)

        fila = 3

        # Escritura del título del informe
        sheetreport.write_merge(0, 1, 0, 5, "Informe reparto de nomina")

        # Escritura de los encabezados de las columnas
        sheetreport.write(fila, 0, "Etiqueta")
        sheetreport.write(fila, 1, "Codigo")
        sheetreport.write(fila, 2, "Nombre")
        sheetreport.write(fila, 3, "DNI")
        sheetreport.write(fila, 4, "Importe")
        sheetreport.write(fila, 5, "Porcentaje")
        fila += 1
        index = -1
        total_amount = 0
        # Iteración sobre los resultados de la actualización de la distribución
        for index, linea in enumerate(res):
            employee = HrEmployeeObj.search([("payroll_code", "=", linea[""])])

            fila, index = self.pinta_data_empleado(
                fila, index, sheetreport, employee, linea
            )
            total_amount += linea["COSTE EMPRESA"]
        sheetreport.write_merge(
            fila + 2,
            fila + 2,
            3,
            5,
            "Total Coste empresa " + str(round(total_amount, 2)),
        )
        # Creación del fichero en memoria
        fp = io.BytesIO()
        # Guardado del libro de Excel en el fichero
        workbookexport.save(fp)
        fp.seek(0)
        # Lectura de los datos del fichero
        data = fp.read()
        fp.close()

        # Codificación de los datos en base64
        result = base64.b64encode(data)
        # Obtención de la URL base
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        # Objeto de adjunto
        attachment_obj = self.env["ir.attachment"]
        # Creación del adjunto
        attachment_id = attachment_obj.create(
            {"name": "resumen_reparto.xls", "datas": result}
        )
        # Preparación de la URL de descarga
        download_url = "/web/content/" + str(attachment_id.id) + "?download=true"
        # Descarga
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "current",
        }

    def pinta_data_empleado(self, fila, index, sheetreport, employee, linea):
        index += 1
        # Redondeo del costo de la empresa
        importes_total_empleado = round(linea["COSTE EMPRESA"], 3)
        # Asignación del total del costo de la empresa
        total_amount = linea["COSTE EMPRESA"]
        # Comprobación de si el empleado tiene etiquetas analíticas de distribución
        _analytic_dist = employee.account_analytic_tag_id.analytic_distribution or {}
        if _analytic_dist.keys():
            # Comprobación de si el empleado tiene más de una etiqueta analítica de distribución
            if len(_analytic_dist.keys()) > 1:
                # Iteración sobre las cuentas de reparto del empleado
                for (
                    cid,
                    percentage,
                ) in _analytic_dist.items():
                    cuenta_reparto = self.env["account.analytic.account"].browse(
                        int(cid)
                    )
                    fila += 1
                    # Escritura de los datos del empleado y
                    # de la cuenta de reparto en la hoja de Excel
                    sheetreport.write(fila, 0, str(cuenta_reparto.display_name or ""))
                    sheetreport.write(fila, 1, linea[""])
                    sheetreport.write(fila, 2, employee.name or "")
                    sheetreport.write(fila, 3, employee.identification_id or "")
                    importe_distribuido = round(
                        (importes_total_empleado / 100) * percentage, 2
                    )
                    sheetreport.write(fila, 4, importe_distribuido)
                    sheetreport.write(
                        fila,
                        5,
                        round((importe_distribuido * 100) / total_amount, 3) or 0,
                    )
            else:
                fila += 1
                # Escritura de los datos del empleado y
                # de la cuenta de reparto en la hoja de Excel
                # Obtenemos la primera clave
                # (ID de la cuenta analítica) del diccionario
                first_account_id = (
                    list(employee.account_analytic_tag_id.analytic_distribution.keys())[
                        0
                    ]
                    if employee.account_analytic_tag_id.analytic_distribution
                    else False
                )
                display_name = ""
                if first_account_id:
                    account = self.env["account.analytic.account"].browse(
                        int(first_account_id)
                    )
                    display_name = account.display_name or ""

                sheetreport.write(fila, 0, display_name)
                sheetreport.write(fila, 1, linea[""])
                sheetreport.write(fila, 2, employee.name or "")
                sheetreport.write(fila, 3, employee.identification_id or "")
                sheetreport.write(fila, 4, importes_total_empleado)
                sheetreport.write(
                    fila,
                    5,
                    round((importes_total_empleado * 100) / total_amount, 3) or 0,
                )

        return fila, index
