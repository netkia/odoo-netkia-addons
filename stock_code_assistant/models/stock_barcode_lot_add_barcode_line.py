from odoo import api, models


class StockBarcodeLot(models.TransientModel):
    _inherit = "stock_barcode.lot"

    @api.model
    def add_barcode_line(self, picking_id, lot_id, barcode):
        wizard = self.search([("picking_id", "=", picking_id)], limit=1)
        if not wizard:
            return False
        existing_line = wizard.stock_barcode_lot_line_ids.filtered(
            lambda x: x.lot_name == barcode
        )
        if existing_line:
            return existing_line.id
        line = self.env["stock_barcode.lot.line"].create(
            {
                "stock_barcode_lot_id": wizard.id,
                "lot_name": barcode,
                "qty_done": 1,
            }
        )
        return line.id
