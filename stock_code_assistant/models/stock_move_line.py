from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    qty_picked = fields.Float(
        string="Quantity Picked",
        digits="Product Unit of Measure",
        default=0.0,
        help="Quantity picked for untracked products. This field tracks the progress "
        "of picking without using lot/serial numbers.",
    )

    @api.depends("qty_picked", "quantity", "lot_id", "lot_name", "quantity_product_uom")
    def _compute_picked(self):
        res = super()._compute_picked()
        for line in self:
            if not line.lot_id and not line.lot_name:
                line.picked = (line.qty_picked or 0.0) >= (line.quantity or 0.0)

        return res
