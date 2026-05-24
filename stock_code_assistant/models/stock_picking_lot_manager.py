from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def open_lot_manager(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "lot_manager",
            "name": "Lot Manager",
            "context": dict(self.env.context, picking_id=self.id),
        }

    def open_lot_manager_window(self):
        self.ensure_one()
        action = self.env.ref("stock_code_assistant.action_lot_manager")
        url = "/web#action=%d&active_id=%d" % (action.id, self.id)
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    def update_wizard_lines(self, barcode=False):
        self.ensure_one()

        existing = self.env["stock_barcode.lot.line"].search(
            [
                ("stock_barcode_lot_id.picking_id", "=", self.id),
                ("lot_name", "=", barcode),
                ("qty_done", "=", 1),
            ],
            limit=1,
        )
        if existing:
            return "already_processed"

        reserved = self._is_barcode_reserved_elsewhere(barcode)

        return self._process_normal_lot_barcode(barcode, reserved)



    def _get_wizards_for_lots(self, sn_lots):
        lot_products = sn_lots.mapped("product_id")
        return self.env["stock_barcode.lot"].search(
            [("picking_id", "=", self.id), ("product_id", "in", lot_products.ids)]
        )

    def _analyze_and_filter_lots(self, sn_lots, barcode):
        lots_by_product = {}
        already_processed = []

        for lot in sn_lots:
            if lot.product_qty <= 0:
                continue

            if self._is_lot_already_processed_in_picking(lot.name):
                already_processed.append(lot.name)
                continue

            lots_by_product.setdefault(lot.product_id.id, []).append(lot)

        if already_processed:
            raise ValidationError(
                _(
                    "El código de proveedor '%s' agrupa lotes que ya están "
                    "procesados en este albarán:\n%s"
                )
                % (barcode, ", ".join(already_processed))
            )

        if not lots_by_product:
            raise UserError(
                _(
                    "El código de proveedor '%s' agrupa lotes que ya han "
                    "sido procesados o enviados."
                )
                % barcode
            )

        return lots_by_product

    def _is_lot_already_processed_in_picking(self, lot_name):
        return bool(
            self.env["stock_barcode.lot.line"].search(
                [
                    ("stock_barcode_lot_id.picking_id", "=", self.id),
                    ("lot_name", "=", lot_name),
                    ("qty_done", "=", 1),
                ],
                limit=1,
            )
        )

    def _validate_capacity_and_prepare_lots(self, lots_by_product, wizards, barcode):
        lots_to_process = []

        for product_id, product_lots in lots_by_product.items():
            product = self.env["product.product"].browse(product_id)

            wizard = wizards.filtered(lambda w, pid=product_id: w.product_id.id == pid)
            if not wizard:
                raise UserError(
                    _(
                        "El código de proveedor '%s' agrupa %d lotes "
                        "del producto '%s', pero este producto no está en el albarán."
                    )
                    % (barcode, len(product_lots), product.display_name)
                )

            available_lines = wizard.stock_barcode_lot_line_ids.filtered(
                lambda line: (line.qty_done or 0) == 0
            )
            if len(available_lines) < len(product_lots):
                raise UserError(
                    _(
                        "El código de proveedor '%s' agrupa %d lotes del producto "
                        "'%s', pero solo hay %d líneas disponibles en el albarán."
                    )
                    % (
                        barcode,
                        len(product_lots),
                        product.display_name,
                        len(available_lines),
                    )
                )

            for lot in product_lots:
                lots_to_process.append((wizard, lot))

        return lots_to_process

    def _process_all_lots(self, lots_to_process, reserved=False):
        processed_any = False
        for wizard, lot in lots_to_process:
            result = self._process_wizard_lot(wizard, lot, reserved=reserved)
            if result == "already_processed":
                return result
            if result is None:
                processed_any = True
        return processed_any

    def _process_normal_lot_barcode(self, barcode, reserved):
        lot = self.env["stock.lot"].search(
            [("name", "=", barcode)],
            limit=1,
        )
        if not lot:
            return False

        wizard = self.env["stock_barcode.lot"].search(
            [("picking_id", "=", self.id), ("product_id", "=", lot.product_id.id)],
            limit=1,
        )
        if not wizard:
            raise UserError(
                _(
                    "El lote/serie '%s' del producto '%s' "
                    "no está incluido en este albarán."
                )
                % (barcode, lot.product_id.display_name)
            )

        if lot.product_id.tracking == "serial":
            return self._process_serial_wizard_line(wizard, lot, reserved)
        return self._process_non_serial_wizard_line(wizard, lot)

    def _process_wizard_lot(self, wizard, lot, reserved):
        wizard_line = wizard.stock_barcode_lot_line_ids.filtered(
            lambda line: (line.qty_done or 0) == 0
        )
        if not wizard_line:
            processed_line = wizard.stock_barcode_lot_line_ids.filtered(
                lambda y, lot=lot: (
                    y.move_line_id.lot_id == lot and (y.qty_done or 0) > 0
                )
            )
            if processed_line:
                return "already_processed"
            return None

        wizard_lot_done = wizard.stock_barcode_lot_line_ids.filtered(
            lambda y, lot=lot: (y.move_line_id.lot_id == lot and y.move_line_id.picked)
        )
        if wizard_lot_done:
            return "already_processed"

        wizard_line = (
            wizard_line.filtered(lambda y, lot=lot: y.move_line_id.lot_id == lot)
            or wizard_line[:1]
        )
        self._update_wizard_and_move_line(wizard_line, lot, reserved)
        return None

    def _process_serial_wizard_line(self, wizard, lot, reserved):
        wizard_line = wizard.stock_barcode_lot_line_ids.filtered(
            lambda line: (line.qty_done or 0) == 0
        )
        if not wizard_line:
            processed_line = wizard.stock_barcode_lot_line_ids.filtered(
                lambda y, lot=lot: (
                    y.move_line_id.lot_id == lot and (y.qty_done or 0) > 0
                )
            )
            if processed_line:
                return "already_processed"
            raise UserError(
                _(
                    "No hay líneas disponibles para el producto '%s'. "
                    "Ya se procesó la cantidad completa del albarán."
                )
                % lot.product_id.display_name
            )

        wizard_lot_done = wizard.stock_barcode_lot_line_ids.filtered(
            lambda y, lot=lot: (y.move_line_id.lot_id == lot and y.move_line_id.picked)
        )
        if wizard_lot_done:
            return "already_processed"

        wizard_line = (
            wizard_line.filtered(lambda y, lot=lot: y.move_line_id.lot_id == lot)
            or wizard_line[:1]
        )
        self._update_wizard_and_move_line(wizard_line, lot, reserved)
        return True

    def _process_non_serial_wizard_line(self, wizard, lot):
        wizard_line = wizard.stock_barcode_lot_line_ids.filtered(
            lambda line, p=lot.product_id: line.stock_barcode_lot_id.product_id.id
            == p.id
        )[:1]
        move_line = wizard_line.move_line_id
        if not move_line:
            return False

        if move_line.picked or (move_line.qty_picked and move_line.qty_picked > 0):
            return "already_processed"

        wizard_line.sudo().write({"lot_name": lot.name, "product_barcode": lot.name})
        move_line.sudo().write({"lot_id": lot.id, "lot_name": lot.name})

        self._sync_move_line_from_lot_lines(move_line)
        return True

    def _update_wizard_and_move_line(self, wizard_line, lot, reserved):
        self.ensure_one()

        wizard_data = {
            "lot_name": lot.name,
            "product_barcode": lot.name,
            "qty_reserved": int(not reserved),
            "qty_done": 1,
        }
        wizard_line.sudo().write(wizard_data)

        move_line = wizard_line.move_line_id.sudo()
        move_line.write({"lot_id": lot.id, "lot_name": lot.name})

        self._sync_move_line_from_lot_lines(move_line)

    def _sync_move_line_from_lot_lines(self, move_line):
        lot_lines = self.env["stock_barcode.lot.line"].search(
            [("move_line_id", "=", move_line.id)]
        )
        total_done = sum(lot_lines.mapped("qty_done") or [0])

        demand = move_line.quantity or 0
        picked = bool(demand and total_done >= demand)

        move_line.write({"qty_picked": total_done, "picked": picked})

    def create_missing_barcode_lines(self):
        self.ensure_one()
        all_wizards = self.env["stock_barcode.lot"].search(
            [("picking_id", "=", self.id)]
        )
        return [wiz.id for wiz in all_wizards]

    @api.model
    def reorder_objects(self, objects):
        all_empty = True
        reordered_list = []
        for obj in objects.values():
            reordered_list.append(obj)
            for lot_line in obj.get("lot_lines", []):
                if (lot_line.get("line", {}) or {}).get("qty_done", 0) > 0:
                    all_empty = False
                    break
        return {"reordered": reordered_list, "all_empty": all_empty}

    def clean_obsolete_lines(self):
        self.ensure_one()
        all_wizards = self.env["stock_barcode.lot"].search(
            [("picking_id", "=", self.id)]
        )

        wizards_without_move = all_wizards.filtered(lambda w: not w.default_move_id)
        for wizard in wizards_without_move:
            move = self.move_ids.filtered(
                lambda m, wiz=wizard: m.product_id == wiz.product_id
            )[:1]
            if move:
                wizard.sudo().write({"default_move_id": move.id})
            else:
                wizard.sudo().unlink()

        all_wizards = self.env["stock_barcode.lot"].search(
            [("picking_id", "=", self.id)]
        )

        wizards_by_product = {}
        for wizard in all_wizards:
            pid = wizard.product_id.id
            if pid not in wizards_by_product or wizard.id > wizards_by_product[pid].id:
                wizards_by_product[pid] = wizard

        wizards_to_keep = self.env["stock_barcode.lot"].browse(
            [w.id for w in wizards_by_product.values()]
        )
        wizards_to_delete = all_wizards - wizards_to_keep
        if wizards_to_delete:
            wizards_to_delete.sudo().unlink()

        for wizard in wizards_to_keep:
            product = wizard.product_id
            is_serial = product.tracking == "serial"
            lines = wizard.stock_barcode_lot_line_ids.sorted("create_date")

            lines_without_move = lines.filtered(lambda line: not line.move_line_id)
            if lines_without_move:
                lines_without_move.sudo().unlink()
                lines = wizard.stock_barcode_lot_line_ids.sorted("create_date")

            if is_serial:
                move_lines = wizard.stock_barcode_lot_line_ids.mapped("move_line_id")
                lines_to_keep = []
                for ml in move_lines:
                    lines_ml = lines.filtered(
                        lambda line, ml=ml: line.move_line_id.id == ml.id
                    )
                    if lines_ml:
                        lines_to_keep.append(
                            sorted(lines_ml, key=lambda line: line.id)[-1]
                        )
                lines_to_unlink = [line for line in lines if line not in lines_to_keep]
                if lines_to_unlink:
                    self.env["stock_barcode.lot.line"].sudo().browse(
                        [line.id for line in lines_to_unlink]
                    ).unlink()
            else:
                if len(lines) > 1:
                    lines[:-1].sudo().unlink()
        return True

    def _is_barcode_reserved_elsewhere(self, barcode):
        self.ensure_one()
        if not barcode:
            return False

        lots_by_name = self.env["stock.lot"].search([("name", "=", barcode)])
        all_lots = lots_by_name
        if not all_lots:
            return False

        other = self.env["stock.move.line"].search(
            [
                ("picking_id", "!=", self.id),
                (
                    "picking_id.state",
                    "in",
                    ["assigned", "partially_available", "waiting", "confirmed"],
                ),
                ("picking_id.picking_type_id.code", "=", "outgoing"),
                ("state", "not in", ["done", "cancel"]),
                ("picked", "=", False),
                "|",
                ("lot_id", "in", all_lots.ids),
                ("lot_name", "=", barcode),
            ],
            limit=1,
        )
        return bool(other)

    def _is_serial_already_shipped_out(self, barcode):
        self.ensure_one()
        if not barcode:
            return False

        lots_by_name = self.env["stock.lot"].search([("name", "=", barcode)])
        all_lots = lots_by_name
        if not all_lots:
            return False

        shipped = self.env["stock.move.line"].search(
            [
                ("picking_id", "!=", self.id),
                ("picking_id.state", "=", "done"),
                ("picking_id.picking_type_id.code", "=", "outgoing"),
                "|",
                ("lot_id", "in", all_lots.ids),
                ("lot_name", "=", barcode),
            ],
            limit=1,
        )

        current_stock = sum(all_lots.mapped("product_qty") or [0])
        return bool(shipped) or current_stock <= 0

    def batch_process_barcodes(self, barcode_list):
        self.ensure_one()
        processed_count = 0
        error_dict = {}

        for barcode in barcode_list or []:
            try:
                result = self.update_wizard_lines(barcode)
                if result == "already_processed":
                    error_dict[barcode] = _("Ya procesado")
                elif result is True or result is None:
                    processed_count += 1
                elif result is False:
                    error_dict[barcode] = _("No encontrado")
                else:
                    error_dict[barcode] = _("Resultado inesperado: %s") % result
            except Exception as e:
                error_dict[barcode] = _("Error: %s") % str(e)

        return {"processed": processed_count, "errors": error_dict}

    def batch_process_untracked_barcodes(self, barcode_list):
        self.ensure_one()
        processed_count = 0
        error_dict = {}

        if not barcode_list:
            return {"processed": 0, "errors": {}}

        barcode_counts = {}
        for b in barcode_list:
            barcode_counts[b] = barcode_counts.get(b, 0) + 1

        Product = self.env["product.product"]
        MoveLine = self.env["stock.move.line"]

        for barcode, count in barcode_counts.items():
            try:
                product = Product.search([("barcode", "=", barcode)], limit=1)
                if not product:
                    error_dict[barcode] = _("Producto no encontrado")
                    continue

                move_line = MoveLine.search(
                    [
                        ("picking_id", "=", self.id),
                        ("product_id", "=", product.id),
                        ("lot_id", "=", False),
                        ("state", "not in", ["done", "cancel"]),
                    ],
                    limit=1,
                )
                if not move_line:
                    error_dict[barcode] = _("Producto no disponible en picking")
                    continue

                demand = move_line.quantity or 0
                current = move_line.qty_picked or 0
                new_qty = current + count

                if demand and new_qty > demand:
                    available = int(demand - current)
                    if available > 0:
                        move_line.write({"qty_picked": current + available})
                        processed_count += available
                        if count > available:
                            error_dict[barcode] = _(
                                "Procesados %s/%s - cantidad máxima alcanzada"
                            ) % (
                                available,
                                count,
                            )
                    else:
                        error_dict[barcode] = _("Cantidad máxima alcanzada")
                    move_line.write(
                        {
                            "picked": bool(
                                demand and (move_line.qty_picked or 0) >= demand
                            )
                        }
                    )
                    continue

                move_line.write(
                    {
                        "qty_picked": new_qty,
                        "picked": bool(demand and new_qty >= demand),
                    }
                )
                processed_count += count

            except Exception as e:
                error_dict[barcode] = _("Error: %s") % str(e)

        return {"processed": processed_count, "errors": error_dict}
