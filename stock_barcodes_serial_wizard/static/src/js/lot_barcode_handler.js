/** @odoo-module **/

import {Component, onMounted, xml} from "@odoo/owl";
import {FormController} from "@web/views/form/form_controller";
import {formView} from "@web/views/form/form_view";
import {registry} from "@web/core/registry";
// Load config parameter on module initialization
import {rpc} from "@web/core/network/rpc";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

let configParameterValue = 0;

rpc("/web/dataset/call_kw/ir.config_parameter/get_param", {
    model: "ir.config_parameter",
    method: "get_param",
    args: ["stock_barcodes_serial_wizard.ibd_lot_barcode_refocus_delay"],
    kwargs: {default: "0"},
}).then((value) => {
    configParameterValue = parseInt(value, 10) || 0;
    console.log("Loaded config parameter:", configParameterValue);
});

export class LotBarcodeWizFormController extends FormController {
    setup() {
        super.setup();
        onMounted(() => {
            this.focusBarcodeField();
            this.setupBarcodeHandling();
        });
    }

    focusBarcodeField() {
        const barcodeField = this.rootRef.el?.querySelector(
            "[name='_barcode_scanned'] input"
        );
        if (barcodeField) {
            barcodeField.focus();
        }
    }

    setupBarcodeHandling() {
        const barcodeField = this.rootRef.el?.querySelector(
            "[name='_barcode_scanned'] input"
        );
        if (barcodeField) {
            barcodeField.addEventListener("keydown", (ev) => {
                if (ev.key === "Enter") {
                    ev.preventDefault();

                    const tabEvent = new KeyboardEvent("keydown", {
                        key: "Tab",
                        keyCode: 9,
                        which: 9,
                        bubbles: true,
                    });
                    ev.currentTarget.dispatchEvent(tabEvent);

                    setTimeout(() => {
                        const updatedBarcodeField = this.rootRef.el?.querySelector(
                            "[name='_barcode_scanned'] input"
                        );
                        if (updatedBarcodeField) {
                            updatedBarcodeField.focus();
                        }
                    }, configParameterValue);
                }
            });
        }
    }
}

export class LotBarcodeHandler extends Component {
    static template = xml`<div/>`;
    static props = {
        ...standardFieldProps,
    };

    setup() {
        onMounted(() => {
            // Trigger barcode activation through the bus
            this.env.bus.trigger("active-barcode-handler", {
                name: this.props.name,
                fieldName: "stock_barcode_lot_line_ids",
                quantity: "qty_done",
                setQuantityWithKeypress: false,
                commands: {barcode: "_barcodeAddX2MQuantity"},
            });
        });
    }
}

registry.category("fields").add("lot_barcode_handler", {
    component: LotBarcodeHandler,
});

registry.category("views").add("lot_barcode_wizard_form", {
    ...formView,
    Controller: LotBarcodeWizFormController,
});
