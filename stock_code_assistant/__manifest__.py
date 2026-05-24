{
    "name": "Stock Code Assistant",
    "summary": "Stock Code Assistant",
    "author": "Netkia",
    "license": "AGPL-3",
    "category": "Delivery",
    "version": "18.0.1.2.0",
    "depends": [
        "delivery_package_number",
        "stock_barcodes_serial_wizard",
    ],
    "data": [
        "views/stock_code_assistant_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "stock_code_assistant/static/src/js/stock_code_assistant_view.js",
            "stock_code_assistant/static/src/scss/stock_code_assistant.scss",
            "stock_code_assistant/static/src/xml/stock_code_assistant_template.xml",
        ],
    },
    "application": False,
    "installable": True,
}
