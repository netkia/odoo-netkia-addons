# Copyright 2023 Tecnativa - David Vidal
{
    "name": "Stock barcodes serial wizard",
    "summary": "Stock barcodes serial wizard",
    "version": "18.0.1.0.0",
    "license": "OEEL-1",
    "category": "Inventory",
    "author": "Tecnativa, IBD Global",
    "installable": True,
    "depends": ["stock", "barcodes"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter_data.xml",
        "wizard/stock_barcode_lot_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "stock_barcodes_serial_wizard/static/src/**/*",
        ],
    },
}
