from odoo import models
from odoo.tools.safe_eval import safe_eval


class Picking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()

        if (
            isinstance(res, dict)
            and res.get("type") == "ir.actions.client"
            and res.get("tag") == "do_multi_print"
        ):
            if self.picking_type_id and not res.get("params", {}).get("anotherAction"):
                action = self.env.ref("stock.action_picking_tree_late").read()[0].copy()
                ctx = action.get("context", {})
                if isinstance(ctx, str):
                    ctx = safe_eval(ctx)
                ctx["search_default_picking_type_id"] = self.picking_type_id.id
                action["context"] = ctx
                action["view_mode"] = "kanban,list,form,calendar"
                res["params"]["anotherAction"] = action
        return res
