/** @odoo-module **/

import {Component, markup, onMounted, useRef, useState} from "@odoo/owl";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class LotManager extends Component {
    static template = "stock_code_assistant.LotManagerTemplate";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        this.state = useState({
            pickingId: null,
            lotIds: {},
            isValidated: false,
            pickingName: "",
            numPackages: 0,
            carrier: "",
            allLines: [],
            completedLines: [],
            notrackingPending: [],
            notrackingCompleted: [],
            currentBatch: [],
            pendingBatches: [],
            batchTimeout: null,
            isProcessingBatch: false,
            batchCounter: 0,
            accumulatedResults: {
                tracked: {processed: 0, errors: {}},
                untracked: {processed: 0, errors: {}},
            },
        });

        this.barcodeInputRef = useRef("barcodeInput");
        this.barcodeUntrackedInputRef = useRef("barcodeUntrackedInput");
        this.validateButtonRef = useRef("validateButton");

        onMounted(() => {
            this._initialize();
        });
    }

    async _initialize() {
        let pickingId = null;

        if (this.props?.action?.context?.active_id) {
            pickingId = this.props.action.context.active_id;
        } else if (this.props?.action?.context?.picking_id) {
            pickingId = this.props.action.context.picking_id;
        } else if (this.props?.context?.picking_id) {
            pickingId = this.props.context.picking_id;
        } else if (typeof odoo !== "undefined" && odoo?.context?.active_id) {
            pickingId = odoo.context.active_id;
        } else {
            const hash = window.location.hash;
            const match = hash.match(/active_id=(\d+)/);
            if (match) {
                pickingId = parseInt(match[1], 10);
            }
        }

        this.state.pickingId = pickingId;

        if (!pickingId) {
            return;
        }

        await this._loadPickingInfo();
        await this._initializeWizardsAndLines();

        setTimeout(() => {
            this.barcodeInputRef.el?.focus();
        }, 100);
    }

    async _loadPickingInfo() {
        const pickings = await this.orm.searchRead(
            "stock.picking",
            [["id", "=", this.state.pickingId]],
            ["name", "number_of_packages", "carrier_id", "state"]
        );

        if (pickings.length) {
            const picking = pickings[0];
            this.state.isValidated = picking.state === "done";
            this.state.pickingName = picking.name || "";
            this.state.numPackages = picking.number_of_packages || 0;
            this.state.carrier =
                picking.carrier_id && Array.isArray(picking.carrier_id)
                    ? picking.carrier_id[1]
                    : _t("Not specified");
        } else {
            this.state.pickingName = "";
            this.state.carrier = _t("Not specified");
        }
    }

    async _initializeWizardsAndLines() {
        const moveLines = await this.orm.searchRead(
            "stock.move.line",
            [["picking_id", "=", this.state.pickingId]],
            ["product_id", "lot_id", "lot_name", "quantity", "picked", "id", "move_id"]
        );

        const productIds = [
            ...new Set(
                moveLines
                    .map((ml) =>
                        ml.product_id && Array.isArray(ml.product_id)
                            ? ml.product_id[0]
                            : null
                    )
                    .filter(Boolean)
            ),
        ];

        const existingLots = await this.orm.searchRead(
            "stock_barcode.lot",
            [["picking_id", "=", this.state.pickingId]],
            ["id", "product_id"]
        );

        const lotIds = {};
        existingLots.forEach((lot) => {
            if (lot.product_id) {
                const pid = Array.isArray(lot.product_id)
                    ? lot.product_id[0]
                    : lot.product_id;
                lotIds[pid] = lot.id;
            }
        });

        const toCreate = productIds.filter((pid) => !lotIds[pid]);
        for (const pid of toCreate) {
            const newLot = await this.orm.create("stock_barcode.lot", [
                {
                    picking_id: this.state.pickingId,
                    product_id: pid,
                },
            ]);
            lotIds[pid] = Array.isArray(newLot) ? newLot[0] : newLot;
        }

        this.state.lotIds = lotIds;

        const lotLineCreates = moveLines.map((ml) => {
            const pid =
                ml.product_id && Array.isArray(ml.product_id) ? ml.product_id[0] : null;
            const lotId = lotIds[pid];
            const lotName = ml.lot_id ? ml.lot_id[1] : ml.lot_name;

            const qtyDone = ml.picked ? 1 : 0;

            return {
                lot_name: lotName,
                qty_reserved: ml.quantity,
                qty_done: qtyDone,
                move_line_id: ml.id,
                stock_barcode_lot_id: lotId,
            };
        });

        const existingLotLines = await this.orm.searchRead(
            "stock_barcode.lot.line",
            [["stock_barcode_lot_id", "in", Object.values(lotIds)]],
            ["id", "move_line_id", "stock_barcode_lot_id", "qty_done"]
        );

        const existingKeys = new Set(
            existingLotLines.map((l) => {
                const mlid = Array.isArray(l.move_line_id)
                    ? l.move_line_id[0]
                    : l.move_line_id;
                const lid = l.stock_barcode_lot_id;
                return `${mlid}:${lid}`;
            })
        );

        const linesToUpdate = [];
        for (const lotLineData of lotLineCreates) {
            const key = `${lotLineData.move_line_id}:${lotLineData.stock_barcode_lot_id}`;
            if (existingKeys.has(key)) {
                const existingLine = existingLotLines.find((l) => {
                    const mlid = Array.isArray(l.move_line_id)
                        ? l.move_line_id[0]
                        : l.move_line_id;
                    const lid = l.stock_barcode_lot_id;
                    return `${mlid}:${lid}` === key;
                });

                if (existingLine && existingLine.qty_done !== lotLineData.qty_done) {
                    linesToUpdate.push({
                        id: existingLine.id,
                        qty_done: lotLineData.qty_done,
                    });
                }
            }
        }

        if (linesToUpdate.length) {
            for (const update of linesToUpdate) {
                await this.orm.write("stock_barcode.lot.line", [update.id], {
                    qty_done: update.qty_done,
                });
            }
        }

        const toCreateLines = lotLineCreates.filter(
            (l) => !existingKeys.has(`${l.move_line_id}:${l.stock_barcode_lot_id}`)
        );

        if (toCreateLines.length) {
            await this.orm.create("stock_barcode.lot.line", toCreateLines);
        }

        await this._fetchAndDisplayLots();
    }

    async _fetchAndDisplayLots() {
        await this.orm.call("stock.picking", "clean_obsolete_lines", [
            this.state.pickingId,
        ]);

        const createdLotIds = await this.orm.call(
            "stock.picking",
            "create_missing_barcode_lines",
            [this.state.pickingId]
        );

        const lotIds =
            Array.isArray(createdLotIds) && createdLotIds.length
                ? createdLotIds
                : Object.values(this.state.lotIds || {});

        const lotLines = await this.orm.searchRead(
            "stock_barcode.lot.line",
            [["stock_barcode_lot_id", "in", lotIds]],
            [
                "id",
                "move_line_id",
                "lot_name",
                "qty_reserved",
                "qty_done",
                "stock_barcode_lot_id",
            ]
        );

        const moveLines = await this.orm.searchRead(
            "stock.move.line",
            [["picking_id", "=", this.state.pickingId]],
            [
                "lot_id",
                "lot_name",
                "quantity",
                "picked",
                "id",
                "move_id",
                "state",
                "product_id",
                "qty_picked",
            ]
        );

        const productIds = [
            ...new Set(
                moveLines
                    .map((ml) =>
                        ml.product_id && Array.isArray(ml.product_id)
                            ? ml.product_id[0]
                            : null
                    )
                    .filter(Boolean)
            ),
        ];

        const products = await this.orm.searchRead(
            "product.product",
            [["id", "in", productIds]],
            ["id", "tracking"]
        );

        const trackingMap = {};
        products.forEach((p) => {
            trackingMap[p.id] = p.tracking;
        });

        const moveLineMap = {};
        moveLines.forEach((ml) => {
            moveLineMap[ml.id] = ml;
        });

        const productMap = {};
        const seen = new Set();

        lotLines.forEach((line) => {
            const moveLineId = Array.isArray(line.move_line_id)
                ? line.move_line_id[0]
                : line.move_line_id;
            const moveLine = moveLineMap[moveLineId] || {};
            const pid =
                moveLine.product_id && Array.isArray(moveLine.product_id)
                    ? moveLine.product_id[0]
                    : null;

            if (!pid || trackingMap[pid] === "none") {
                return;
            }

            const uniqueKey = `${moveLineId}:${line.stock_barcode_lot_id}`;
            if (seen.has(uniqueKey)) return;
            seen.add(uniqueKey);

            if (!productMap[pid]) {
                productMap[pid] = {
                    name: moveLine.product_id[1] || "",
                    lot_lines: [],
                };
            }

            productMap[pid].lot_lines.push({
                line: line,
                move_line: moveLine,
            });
        });

        const result = await this.orm.call("stock.picking", "reorder_objects", [
            productMap,
        ]);
        const reordered = result && result.reordered ? result.reordered : [];

        const allLines = [];
        const completedLines = [];

        Object.values(reordered).forEach((prod) => {
            prod.lot_lines.forEach((obj) => {
                const line = obj.line;
                const moveLine = obj.move_line;
                const qtyDone = line.qty_done || 0;
                const qtyReserved = line.qty_reserved || 0;
                const productId =
                    moveLine.product_id && Array.isArray(moveLine.product_id)
                        ? moveLine.product_id[0]
                        : null;

                const lineData = {
                    producto: prod.name,
                    line: line,
                    move_line: moveLine,
                    qty_done: qtyDone,
                    qty_reserved: qtyReserved,
                    product_id: productId,
                    incomplete: qtyDone < 1,
                };

                console.log(
                    "DEBUG _fetchAndDisplayLots - tracked product classification:",
                    {
                        producto: prod.name,
                        lotName: line.lot_name,
                        qtyDone: qtyDone,
                        qtyReserved: qtyReserved,
                        picked: moveLine.picked,
                        incomplete: lineData.incomplete,
                        lineId: line.id,
                        moveLineId: moveLine.id,
                    }
                );

                if (lineData.incomplete) {
                    allLines.push(lineData);
                } else {
                    completedLines.push(lineData);
                }
            });
        });

        const notrackingPending = [];
        const notrackingCompleted = [];
        const notrackingMoveLines = moveLines.filter(
            (ml) => !ml.lot_id || ml.lot_id === false
        );

        if (notrackingMoveLines.length) {
            const moveLineIds = notrackingMoveLines
                .map((ml) => (Array.isArray(ml.id) ? ml.id[0] : ml.id))
                .filter(Boolean);

            const notrackingLotLines = moveLineIds.length
                ? await this.orm.searchRead(
                      "stock_barcode.lot.line",
                      [["move_line_id", "in", moveLineIds]],
                      ["move_line_id", "qty_done", "qty_reserved"]
                  )
                : [];

            const lotLinesByMove = {};
            notrackingLotLines.forEach((l) => {
                const mlid = Array.isArray(l.move_line_id)
                    ? l.move_line_id[0]
                    : l.move_line_id;
                if (!lotLinesByMove[mlid]) lotLinesByMove[mlid] = [];
                lotLinesByMove[mlid].push(l);
            });
            notrackingMoveLines.forEach((ml) => {
                const qtyDemand = ml.quantity || 0;
                if (qtyDemand === 0) return;

                const qtyDone = ml.qty_picked || 0;
                ml.qty_done = qtyDone;

                const shouldBeCompleted = qtyDone >= qtyDemand;

                console.log("DEBUG _fetchAndDisplayLots - classifying move line:", {
                    moveLineId: ml.id,
                    productId: ml.product_id,
                    qtyDone: qtyDone,
                    qtyDemand: qtyDemand,
                    picked: ml.picked,
                    shouldBeCompleted: shouldBeCompleted,
                    comparison: `${qtyDone} >= ${qtyDemand} = ${qtyDone >= qtyDemand}`,
                });

                if (shouldBeCompleted) {
                    notrackingCompleted.push(ml);
                } else {
                    notrackingPending.push(ml);
                }
            });
        }

        this.state.allLines = allLines;
        this.state.completedLines = completedLines;
        this.state.notrackingPending = notrackingPending;
        this.state.notrackingCompleted = notrackingCompleted;

        const hasTrackedDone = completedLines.length > 0;
        const hasUntrackedDone =
            notrackingCompleted.length > 0 || notrackingPending.some((ml) => ml.picked);
        const canValidate = hasTrackedDone || hasUntrackedDone;

        if (this.validateButtonRef.el) {
            this.validateButtonRef.el.disabled = !canValidate;
        }
    }

    _finalizeBatch() {
        if (!this.state.currentBatch.length) return;

        this.state.batchCounter += 1;
        const batchObj = {
            id: this.state.batchCounter,
            codes: this.state.currentBatch.slice(),
        };
        this.state.pendingBatches.push(batchObj);
        this.state.currentBatch = [];

        this._processNextBatch();
    }

    _processNextBatch() {
        if (this.state.isProcessingBatch) return;
        if (!this.state.pendingBatches.length) return;

        const batchObj = this.state.pendingBatches.shift();
        this.state.isProcessingBatch = true;

        this._processBatchCodes(batchObj.codes);
    }

    async _processBatchCodes(codes) {
        if (!codes.length) {
            this.state.isProcessingBatch = false;
            return;
        }

        try {
            const separated = await this._separateBarcodesTypesBatch(codes);

            const results = {
                tracked: {processed: 0, errors: {}},
                untracked: {processed: 0, errors: {}},
                total_codes: codes.length,
            };

            const jobs = [];

            if (separated.untracked.length) {
                jobs.push(
                    this.orm
                        .call("stock.picking", "batch_process_untracked_barcodes", [
                            this.state.pickingId,
                            separated.untracked,
                        ])
                        .then((r) => {
                            results.untracked.processed = r?.processed || 0;
                            results.untracked.errors = r?.errors || {};
                        })
                        .catch((e) => {
                            const msg =
                                e?.data?.message ||
                                e?.message ||
                                e?.data?.debug ||
                                JSON.stringify(e);
                            const errors = {};
                            for (const b of separated.tracked) errors[b] = msg;
                            results.tracked.errors = errors;
                        })
                );
            }

            if (separated.tracked.length) {
                jobs.push(
                    this.orm
                        .call("stock.picking", "batch_process_barcodes", [
                            this.state.pickingId,
                            separated.tracked,
                        ])
                        .then((r) => {
                            results.tracked.processed = r?.processed || 0;
                            results.tracked.errors = r?.errors || {};
                        })
                        .catch((e) => {
                            const msg =
                                e?.data?.message ||
                                e?.message ||
                                e?.data?.debug ||
                                JSON.stringify(e);
                            const errors = {};
                            for (const b of separated.tracked) errors[b] = msg;
                            results.tracked.errors = errors;
                        })
                );
            }

            await Promise.all(jobs);
            await this._onBatchProcessed(results);
        } catch (err) {
            this._onBatchError(err, codes.length);
        }
    }

    async _separateBarcodesTypesBatch(barcodes) {
        const products = await this.orm.searchRead(
            "product.product",
            [["barcode", "in", barcodes]],
            ["barcode"]
        );
        const productBarcodeSet = new Set(
            products.map((p) => p.barcode).filter(Boolean)
        );

        const untracked = [];
        const tracked = [];

        for (const b of barcodes) {
            if (productBarcodeSet.has(b)) untracked.push(b);
            else tracked.push(b);
        }

        return {untracked, tracked};
    }

    async _onBatchProcessed(results) {
        await this._fetchAndDisplayLots();

        this.state.accumulatedResults.tracked.processed +=
            results.tracked.processed || 0;
        this.state.accumulatedResults.untracked.processed +=
            results.untracked.processed || 0;

        Object.assign(
            this.state.accumulatedResults.tracked.errors,
            results.tracked.errors || {}
        );
        Object.assign(
            this.state.accumulatedResults.untracked.errors,
            results.untracked.errors || {}
        );

        this.state.isProcessingBatch = false;

        if (this.state.pendingBatches.length) {
            setTimeout(() => this._processNextBatch(), 50);
        } else {
            setTimeout(() => this._showFinalAccumulatedResults(), 50);
        }

        setTimeout(() => this.barcodeInputRef.el?.focus(), 80);
    }

    _onBatchError(error, totalCodes) {
        this.notification.add(
            _t("Error processing ") +
                totalCodes +
                _t(" codes: ") +
                (error?.message || error),
            {title: _t("Batch error"), type: "danger", sticky: true}
        );

        this.state.isProcessingBatch = false;

        setTimeout(() => this._processNextBatch(), 50);
        setTimeout(() => this.barcodeInputRef.el?.focus(), 80);
    }

    _showFinalAccumulatedResults() {
        const acc = this.state.accumulatedResults;
        const totalProcessed =
            (acc.tracked.processed || 0) + (acc.untracked.processed || 0);
        const hasTrackedErrors = Object.keys(acc.tracked.errors || {}).length > 0;
        const hasUntrackedErrors = Object.keys(acc.untracked.errors || {}).length > 0;

        if (!totalProcessed && !hasTrackedErrors && !hasUntrackedErrors) {
            this._resetAccumulatedResults();
            return;
        }

        const parts = [];

        if (totalProcessed) {
            const ok = [];
            if (acc.tracked.processed)
                ok.push(_t("Lots/Serials: ") + acc.tracked.processed);
            if (acc.untracked.processed)
                ok.push(_t("Untracked: ") + acc.untracked.processed);
            parts.push("✅ " + _t("PROCESSED: ") + ok.join(" | "));
        }

        const renderErrors = (errs) =>
            Object.entries(errs)
                .map(([b, m]) => `• ${b}: ${m}`)
                .join("<br/>");

        if (hasTrackedErrors) {
            parts.push("❌ " + _t("ERRORS:"));
            parts.push(renderErrors(acc.tracked.errors));
        }

        if (hasUntrackedErrors) {
            parts.push("<br/>━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            parts.push("<b>❌ " + _t("ERRORS:") + "</b>");
            parts.push(renderErrors(acc.untracked.errors));
        }

    //     this.notification.add(parts.join("<br/>"), {
    //         title:
    //             hasTrackedErrors || hasUntrackedErrors
    //                 ? _t("Completed with errors")
    //                 : _t("Completed"),
    //         type: hasTrackedErrors || hasUntrackedErrors ? "warning" : "success",
    //         sticky: hasTrackedErrors || hasUntrackedErrors,
    //     });
    const message = markup(parts.join("<br/>"));
        const title =
            hasTrackedErrors || hasUntrackedErrors
                ? _t("Completed with errors")
                : _t("Completed");

        if (hasTrackedErrors || hasUntrackedErrors) {
            // Modal bloqueante para errores
            this.dialog.add(ConfirmationDialog, {
                body: message,
                title: title,
                confirmLabel: _t("Accept"),
                cancel: () => {}, // Oculta botón cancelar
            });
        } else {
            // Notificación toast para éxito
            this.notification.add(message, {
                title: title,
                type: "success",
            });
        }
        this._resetAccumulatedResults();
    }

    _resetAccumulatedResults() {
        this.state.accumulatedResults = {
            tracked: {processed: 0, errors: {}},
            untracked: {processed: 0, errors: {}},
        };
    }

    async onBarcodeScanned(ev) {
        if (ev.key !== "Enter") return;

        const barcode = ev.target.value.trim();
        ev.target.value = "";

        if (!this.state.pickingId) return;

        if (!barcode) {
            if (this.state.batchTimeout) {
                clearTimeout(this.state.batchTimeout);
                this.state.batchTimeout = null;
            }
            this._finalizeBatch();
            return;
        }

        this.state.currentBatch.push(barcode);

        if (this.state.batchTimeout) clearTimeout(this.state.batchTimeout);
        this.state.batchTimeout = setTimeout(() => {
            this._finalizeBatch();
        }, 500);
    }

    async _processTrackedBarcode(barcode) {
        await this.orm.call("stock.picking", "clean_obsolete_lines", [
            this.state.pickingId,
        ]);

        const updateResult = await this.orm.call(
            "stock.picking",
            "update_wizard_lines",
            [this.state.pickingId, barcode]
        );

        if (updateResult === "already_processed") {
            this.notification.add(
                _t("The code ") +
                    barcode +
                    _t(" has already been scanned and processed completely."),
                {title: _t("Code already processed"), type: "warning"}
            );
            setTimeout(() => this.barcodeInputRef.el?.focus(), 100);
            return;
        }

        if (updateResult === true) {
            this.notification.add(_t("✓ Code processed correctly: ") + barcode, {
                title: _t("Code registered"),
                type: "success",
            });
            await this._fetchAndDisplayLots();
            setTimeout(() => this.barcodeInputRef.el?.focus(), 100);
            return;
        }

        if (updateResult === false) {
            this.notification.add(
                _t("No lot/serial found with the code: ") +
                    barcode +
                    _t(". Please verify the code is correct."),
                {title: _t("Code not found"), type: "warning"}
            );
            setTimeout(() => this.barcodeInputRef.el?.focus(), 100);
            return;
        }

        await this._manualBarcodeProcessing(barcode);
    }

    async _manualBarcodeProcessing(barcode) {
        

        const moveLines = await this.orm.searchRead(
            "stock.move.line",
            [["picking_id", "=", this.state.pickingId]],
            ["id", "lot_id", "lot_name", "picked", "quantity", "state", "product_id"]
        );

        let targetMoveLines = [];
        targetMoveLines = moveLines.filter((ml) => {
        const lotMatch =
            (ml.lot_id &&
                Array.isArray(ml.lot_id) &&
                ml.lot_id[1] === barcode) ||
            (ml.lot_name && ml.lot_name === barcode);
            return ml.state !== "done" && ml.state !== "cancel" && lotMatch;
        });
        

        if (!targetMoveLines.length) {
            const alreadyProcessed = moveLines.filter((ml) => {
                const lotMatch =
                    (ml.lot_id &&
                        Array.isArray(ml.lot_id) &&
                        ml.lot_id[1] === barcode) ||
                    (ml.lot_name && ml.lot_name === barcode);
                return lotMatch && ml.picked;
            });

            if (alreadyProcessed.length > 0) {
                this.notification.add(
                    _t("The code ") +
                        barcode +
                        _t(" has already been scanned and processed completely."),
                    {title: _t("Code already processed"), type: "warning"}
                );
            } else {
                this.notification.add(
                    _t("No lot/serial found with the code: ") +
                        barcode +
                        _t(". Please verify the code is correct."),
                    {title: _t("Code not found"), type: "warning"}
                );
            }
            return;
        }

        for (const ml of targetMoveLines) {
            await this._processMoveLine(ml, barcode);
        }

        this.notification.add(_t("✓ Code processed correctly: ") + barcode, {
            title: _t("Code registered"),
            type: "success",
        });

        await this._fetchAndDisplayLots();
        setTimeout(() => this.barcodeInputRef.el?.focus(), 100);
    }

    async _processMoveLine(ml, barcode) {
        const productId =
            ml.product_id && Array.isArray(ml.product_id) ? ml.product_id[0] : null;
        const lotId =
            this.state.lotIds && productId ? this.state.lotIds[productId] : null;

        if (!lotId) return;

        const lotLines = await this.orm.searchRead(
            "stock_barcode.lot.line",
            [
                ["stock_barcode_lot_id", "=", lotId],
                ["move_line_id", "=", ml.id],
            ],
            ["id", "lot_name", "qty_done", "qty_reserved", "move_line_id"]
        );

        const matchingLine = lotLines.find((x) => x.lot_name === barcode);
        const productInfo = await this.orm.read(
            "product.product",
            [productId],
            ["tracking"]
        );
        const isSerial = productInfo.length && productInfo[0].tracking === "serial";

        if (isSerial && matchingLine) {
            const serialLines = await this.orm.searchRead(
                "stock_barcode.lot.line",
                [
                    ["stock_barcode_lot_id", "=", lotId],
                    ["lot_name", "=", barcode],
                ],
                ["qty_done", "move_line_id"]
            );

            const moveLineIds = serialLines
                .map((x) =>
                    Array.isArray(x.move_line_id) ? x.move_line_id[0] : x.move_line_id
                )
                .filter(Boolean);

            if (moveLineIds.length > 0) {
                const moveLineDatas = await this.orm.read(
                    "stock.move.line",
                    moveLineIds,
                    ["picked", "quantity"]
                );
                const allDone =
                    moveLineDatas.length > 0 &&
                    moveLineDatas.every((ml2) => ml2.picked);

                if (allDone) {
                    this.notification.add(
                        _t("Cannot scan the same serial number twice."),
                        {title: _t("Duplicate number"), type: "danger"}
                    );
                    return;
                }
            }
        }

        if (matchingLine) {
            const latestLines = await this.orm.read(
                "stock_barcode.lot.line",
                [matchingLine.id],
                ["qty_done"]
            );
            const currentDone =
                (latestLines && latestLines[0] && latestLines[0].qty_done) || 0;
            const maxQty =
                matchingLine.qty_reserved || matchingLine.quantity || ml.quantity || 1;

            if (currentDone < maxQty) {
                await this.orm.write("stock_barcode.lot.line", [matchingLine.id], {
                    qty_done: currentDone + 1,
                    lot_name: barcode,
                });
                await this._updateMoveLineQtyDone(ml.id);
            }
        } else {
            await this.orm.create("stock_barcode.lot.line", [
                {
                    lot_name: barcode,
                    qty_done: 1,
                    qty_reserved: ml.quantity,
                    move_line_id: ml.id,
                    stock_barcode_lot_id: lotId,
                },
            ]);
            await this._updateMoveLineQtyDone(ml.id);
        }
    }

    async _updateMoveLineQtyDone(moveLineId) {
        const lotLinesInner = await this.orm.searchRead(
            "stock_barcode.lot.line",
            [["move_line_id", "=", moveLineId]],
            ["qty_done", "qty_reserved"]
        );

        const totalDone = lotLinesInner.reduce((sum, l) => sum + (l.qty_done || 0), 0);
        const totalReserved =
            lotLinesInner.length > 0 ? lotLinesInner[0].qty_reserved || 0 : 0;

        const picked = totalReserved > 0 && totalDone >= totalReserved;
        await this.orm.write("stock.move.line", [moveLineId], {
            picked: picked,
            qty_picked: totalDone,
        });
    }

    async _processUntrackedBarcode(barcode, products) {
        if (products.length > 1) {
            const productNames = products.map((p) => p.name).join(", ");
            this.notification.add(
                _t("Multiple products have the same barcode ") +
                    barcode +
                    ": " +
                    productNames +
                    _t(". Contact the administrator to fix this duplication."),
                {title: _t("Configuration error"), type: "danger"}
            );
            return;
        }

        const product = products[0];
        const moveLines = await this.orm.searchRead(
            "stock.move.line",
            [
                ["picking_id", "=", this.state.pickingId],
                ["product_id", "=", product.id],
                ["lot_id", "=", false],
            ],
            ["id", "quantity", "picked", "qty_picked"]
        );

        if (moveLines.length === 0) {
            this.notification.add(
                _t("The product ") +
                    product.name +
                    _t(" is not available in this picking to process."),
                {title: _t("Product not available"), type: "warning"}
            );
            return;
        }

        const moveLine = moveLines[0];

        const newQtyPicked = (moveLine.qty_picked || 0) + 1;

        if (newQtyPicked > moveLine.quantity) {
            this.notification.add(
                _t("⚠️ This product has already been fully picked: ") +
                    product.name +
                    _t(" (") +
                    moveLine.quantity +
                    _t(" of ") +
                    moveLine.quantity +
                    _t(")"),
                {title: _t("Already picked"), type: "warning"}
            );
            return;
        }

        console.log("DEBUG _processUntrackedBarcode:", {
            productName: product.name,
            moveLineId: moveLine.id,
            currentQtyPicked: moveLine.qty_picked,
            newQtyPicked: newQtyPicked,
            quantity: moveLine.quantity,
            comparison: `${newQtyPicked} >= ${moveLine.quantity}`,
        });

        await this.orm.write("stock.move.line", [moveLine.id], {
            qty_picked: newQtyPicked,
        });

        await this._fetchAndDisplayLots();

        this.notification.add(_t("✓ Product picked: ") + product.name, {
            title: _t("Unit added"),
            type: "success",
        });

        setTimeout(() => this.barcodeInputRef.el?.focus(), 100);
    }

    async onBarcodeScannedUntracked(ev) {
        if (ev.key !== "Enter") return;

        const barcode = ev.target.value.trim();
        ev.target.value = "";

        if (!barcode) {
            return;
        }

        const products = await this.orm.searchRead(
            "product.product",
            [["barcode", "=", barcode]],
            ["id", "name", "barcode"]
        );

        if (products.length === 0) {
            this.notification.add(
                _t("⚠️ No product found with barcode: ") +
                    barcode +
                    _t(". Please verify the code."),
                {title: _t("Barcode not found"), type: "warning"}
            );
            return;
        }

        await this._processUntrackedBarcode(barcode, products);
        setTimeout(() => this.barcodeUntrackedInputRef.el?.focus(), 100);
    }

    onTabLotesClick() {
        setTimeout(() => this.barcodeInputRef.el?.focus(), 300);
    }

    onTabUntrackedClick() {
        console.log("Tab Done clicked");
        console.log("completedLines:", this.state.completedLines);
        console.log("notrackingCompleted:", this.state.notrackingCompleted);
        setTimeout(() => this.barcodeUntrackedInputRef.el?.focus(), 300);
    }

    async onValidatePicking() {
        if (!this.state.pickingId) {
            this.notification.add(_t("Picking ID not found."), {
                title: _t("Error"),
                type: "danger",
            });
            return;
        }

        const action = await this.orm.call("stock.picking", "button_validate", [
            [this.state.pickingId],
        ]);

        if (action === true) {
            this.notification.add(_t("Picking validated successfully!"), {
                title: _t("Success"),
                type: "success",
            });
            await this._loadPickingInfo();
            return;
        }

        if (action && typeof action === "object") {
            this.action.doAction(action);
        }
    }

    async onNumPackagesChange(ev) {
        let newVal = parseInt(ev.target.value, 10);
        if (isNaN(newVal) || newVal < 0) newVal = 0;
        ev.target.value = newVal;
        this.state.numPackages = newVal;

        await this.orm.write("stock.picking", [this.state.pickingId], {
            number_of_packages: newVal,
        });
    }

    onPickingRefClick() {
        const pickingUrl = `/web#id=${this.state.pickingId}&model=stock.picking&view_type=form`;
        window.location.href = pickingUrl;
    }

    get trackedPendingLines() {
        return this.state.allLines.map((item) => ({
            producto: item.producto,
            lotName: "",
            cantidad: 1,
            hecho: item.line?.qty_done || 0,
        }));
    }

    get untrackedPendingLines() {
        return this.state.notrackingPending;
    }

    get completedTrackedLines() {
        return this.state.completedLines
            .map((item) => {
                if (!item || !item.move_line) {
                    return null;
                }

                let lotName = "";
                if (item.move_line.lot_id && Array.isArray(item.move_line.lot_id)) {
                    lotName = item.move_line.lot_id[1] || "";
                } else if (item.move_line.lot_name) {
                    lotName = item.move_line.lot_name;
                } else {
                    lotName = item.line?.lot_name || "";
                }

                const hecho = item.line?.qty_done || 0;

                return {
                    producto: item.producto || "",
                    lotName: lotName,
                    cantidad: 1,
                    hecho: hecho,
                };
            })
            .filter(Boolean);
    }

    get completedUntrackedLines() {
        console.log("Getting completedUntrackedLines:", this.state.notrackingCompleted);
        return this.state.notrackingCompleted || [];
    }
}

registry.category("actions").add("lot_manager", LotManager);
