# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def action_barcode_wizard(self):
        self.ensure_one()
        view_id = self.env.ref("stock_barcodes_serial_wizard.view_barcode_lot_form_qr").id if self.env.context.get('lot_mode') == 'inline' else self.env.ref("stock_barcodes_serial_wizard.view_barcode_lot_form_barcode").id
        # view_id = self.env.ref("stock_barcodes_serial_wizard.view_barcode_lot_form").id
        action_ctx = dict(
            self.env.context,
            default_picking_id=self.picking_id.id,
            serial=self.product_id.tracking == "serial",
            default_product_id=self.product_id.id,
            candidates=self.move_line_ids.ids,
            origin_move_id=self.id,
        )
        return {
            "name": _("Lot/Serial Number Details"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "stock_barcode.lot",
            "views": [(view_id, "form")],
            "view_id": view_id,
            "target": self.env.context.get('lot_mode', 'inline'),
            "context": action_ctx,
        }
