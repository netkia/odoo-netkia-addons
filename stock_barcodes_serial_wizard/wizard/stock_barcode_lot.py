# Copyright Odoo
# Copyright 2019 Qubiq - Xavier Piernas
# Copyright 2023 Tecnativa
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockBarcodeLot(models.TransientModel):
    _name = "stock_barcode.lot"
    _inherit = ["barcodes.barcode_events_mixin"]
    _description = "Wizard to scan SN/LN for specific product"

    picking_id = fields.Many2one("stock.picking")
    product_id = fields.Many2one("product.product")
    qty_reserved = fields.Float()
    qty_done = fields.Float()
    default_move_id = fields.Many2one("stock.move")
    stock_barcode_lot_line_ids = fields.One2many(
        "stock_barcode.lot.line", "stock_barcode_lot_id"
    )

    barcode_scanned_manual = fields.Char("Barcode Scanned")

    @api.onchange("stock_barcode_lot_line_ids")
    def _onchange_stock_barcode_lot_line_ids(self):
        self._update_quantity_done()

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        qty_reserved = 0.0
        qty_done = 0.0
        if "stock_barcode_lot_line_ids" in fields and self.env.context.get(
            "candidates"
        ):
            candidates = self.env["stock.move.line"].browse(
                self.env.context["candidates"]
            )
            lines = []
            res["default_move_id"] = candidates[0].move_id.id
            for ml in candidates:
                if ml.lot_id:
                    lot_name = ml.lot_id.name
                else:
                    lot_name = ml.lot_name
                lines.append(
                    {
                        "lot_name": lot_name,
                        "qty_reserved": ml.quantity,
                        "qty_done": ml.quantity,
                        "move_line_id": ml.id,
                    }
                )
                qty_reserved += ml.quantity
                qty_done += ml.quantity
            res["stock_barcode_lot_line_ids"] = [(0, 0, x) for x in lines]
        if "qty_reserved" in fields:
            res["qty_reserved"] = qty_reserved
        if "qty_done" in fields:
            res["qty_done"] = qty_done

        return res

    def _update_quantity_done(self):
        self.qty_done = sum(self.stock_barcode_lot_line_ids.mapped("qty_done"))

    def on_barcode_scanned(self, barcode):
        vals = {}
        

        suitable_line = self.stock_barcode_lot_line_ids.filtered(
            lambda x: x.lot_name == barcode or not x.lot_name
        )
        if suitable_line:
            if (
                suitable_line[0].lot_name
                and self.product_id.tracking == "serial"
                and suitable_line[0].qty_done > 0
            ):
                raise UserError(_("You cannot scan two times the same serial number"))
            else:
                vals["lot_name"] = barcode
            if self.product_id.tracking == "serial" and suitable_line[0].qty_done >= 1:
                vals["qty_done"] = 1
            else:
                vals["qty_done"] = suitable_line[0].qty_done + 1
            suitable_line[0].update(vals)
            increment = 1 if vals["qty_done"] > suitable_line[0].qty_done else 0
        else:
            vals["lot_name"] = barcode
            vals["qty_done"] = 1
            vals["stock_barcode_lot_id"] = self.id
            self.env["stock_barcode.lot.line"].new(vals)
            increment = 1
        self.update({"qty_done": self.qty_done + increment})
        return

    def cancel_lot(self):
        if self.env.context.get("lot_mode") == "inline":
            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "res_id": self.picking_id.id,
                "view_mode": "form",
                "target": "current",
            }

    def validate_lot(self):
        for line in self.stock_barcode_lot_line_ids:
            vals = {}
            vals["quantity"] = line.qty_done
            if (
                self.picking_id.picking_type_id.use_create_lots
                and not self.picking_id.picking_type_id.use_existing_lots
            ):
                vals["lot_name"] = line.lot_name
            else:
                vals["lot_id"] = self.get_lot_or_create(line.lot_name).id
            if line.move_line_id:
                line.move_line_id.write(vals)
            elif self.default_move_id:
                vals.update(
                    {
                        "picking_id": self.picking_id.id,
                        "move_id": self.default_move_id.id,
                        "product_id": self.product_id.id,
                        "product_uom_id": self.default_move_id.product_uom.id,
                        "location_id": self.default_move_id.location_id.id,
                        "location_dest_id": self.default_move_id.location_dest_id.id,
                    }
                )
                self.env["stock.move.line"].create(vals)
            else:
                vals.update(
                    {
                        "picking_id": self.picking_id.id,
                        "product_id": self.product_id.id,
                        "product_uom_id": self.product_id.uom_id.id,
                        "location_id": self.picking_id.location_id.id,
                        "location_dest_id": self.picking_id.location_dest_id.id,
                    }
                )
                new_move = self.env["stock.move"].create(
                    {
                        "name": self.picking_id.name,
                        "picking_id": self.picking_id.id,
                        "picking_type_id": self.picking_id.picking_type_id.id,
                        "location_id": self.picking_id.location_id.id,
                        "location_dest_id": self.picking_id.location_dest_id.id,
                        "product_id": self.product_id.id,
                        "product_uom": self.product_id.uom_id.id,
                        "move_line_ids": [(0, 0, vals)],
                    }
                )
                self.default_move_id = new_move
        # Extended from original: We want to link the new lines with the existing moves.
        # Clean up empty moves (moves without quantity or reserved)
        for move in self.picking_id.move_ids.filtered(
            lambda x: not x.product_uom_qty and not x.move_line_ids
        ):
            for move_line in move.move_line_ids:
                move_id = self.picking_id.move_ids.filtered(
                    lambda x, move_line=move_line: x.product_id
                    == move_line.move_id.product_id
                    and x.id != move_line.move_id.id
                )
                if self.env.context.get("origin_move_id"):
                    move_line.move_id = move_id.filtered(
                        lambda x: x.id == self.env.context.get("origin_move_id")
                    )
                # The wizard could be launched without this context, so we maybe
                # we don't have a sure move to put the lines into
                else:
                    move_line.move_id = move_id[:1]
            line.unlink()

        if self.env.context.get("lot_mode") == "inline":
            # return self.env.ref('stock.action_picking_tree_late').read()[0]
            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "res_id": self.picking_id.id,
                "view_mode": "form",
                "target": "current",
            }

    def get_lot_or_create(self, barcode):
        lot = self.env["stock.lot"].search(
            [("name", "=", barcode), ("product_id", "=", self.product_id.id)]
        )
        if not lot:
            if self.picking_id.picking_type_id.use_create_lots:
                lot = self.env["stock.lot"].create(
                    {"name": barcode, "product_id": self.product_id.id}
                )
            else:
                raise UserError(_("Serie no encontrada: %s") % barcode)
        return lot


class StockBarcodeLotLine(models.TransientModel):
    _name = "stock_barcode.lot.line"
    _description = "LN/SN Product Lines"

    lot_name = fields.Char("Lot")
    qty_reserved = fields.Float("Quantity Reserved")
    qty_done = fields.Float("Quantity Done")
    stock_barcode_lot_id = fields.Many2one("stock_barcode.lot")
    move_line_id = fields.Many2one("stock.move.line")
    product_barcode = fields.Char("Barcode", compute="_compute_product_barcode")

    # @api.model_create_multi
    # def create(self, values):
    #     res = super(StockBarcodeLotLine, self).create(values)
    #     if (
    #         res.stock_barcode_lot_id.product_id.tracking == "serial"
    #         # and res.qty_done > 1
    #     ):
    #         raise UserError(_("You cannot scan two times the same serial number"))
    #     return res

    @api.onchange("qty_done")
    def onchange_qty_done(self):
        if (
            self.stock_barcode_lot_id.product_id.tracking == "serial"
            and self.qty_done > 1
        ):
            raise UserError(_("You cannot scan two times the same serial number"))
        self.stock_barcode_lot_id._update_quantity_done()

    @api.depends("lot_name")
    def _compute_product_barcode(self):
        for line in self:
            line.product_barcode = line.lot_name
