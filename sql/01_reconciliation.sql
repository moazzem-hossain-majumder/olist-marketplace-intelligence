-- =====================================================================
-- 01_reconciliation.sql  |  PROBLEM 1 - Order-to-Cash reconciliation
-- Do the four systems of record (orders, items, payments, reviews)
-- agree with each other? Every failed check is an exception that
-- either leaks money or breaks a downstream report.
-- =====================================================================

-- name: create_recon_view
-- Row-level exception view: one row per (order, failed check).
DROP VIEW IF EXISTS v_recon_exceptions;
CREATE VIEW v_recon_exceptions AS
WITH base AS (
    SELECT o.order_id, o.order_status, o.order_purchase_timestamp,
           o.order_approved_at, o.order_delivered_carrier_date,
           o.order_delivered_customer_date,
           ov.basket_value, op.paid_value, op.max_installments, op.payment_types
    FROM orders o
    LEFT JOIN v_order_value  ov ON ov.order_id = o.order_id
    LEFT JOIN v_order_payment op ON op.order_id = o.order_id
)
SELECT order_id, order_status, 'C1_order_without_items' AS check_id,
       paid_value AS amount_at_stake, payment_types, max_installments,
       'Payment recorded but no line items: cannot be fulfilled or invoiced' AS description
FROM base WHERE basket_value IS NULL
UNION ALL
SELECT order_id, order_status, 'C2_order_without_payment',
       basket_value, payment_types, max_installments,
       'Line items exist but no payment record'
FROM base WHERE paid_value IS NULL AND basket_value IS NOT NULL
UNION ALL
SELECT order_id, order_status, 'C3_overpaid_vs_basket',
       ROUND(paid_value - basket_value, 2), payment_types, max_installments,
       'Collected more than items + freight'
FROM base WHERE paid_value - basket_value > 0.01
UNION ALL
SELECT order_id, order_status, 'C4_underpaid_vs_basket',
       ROUND(basket_value - paid_value, 2), payment_types, max_installments,
       'Collected less than items + freight'
FROM base WHERE basket_value - paid_value > 0.01
UNION ALL
SELECT order_id, order_status, 'C5_delivered_without_delivery_date',
       basket_value, payment_types, max_installments,
       'Status = delivered but no customer delivery timestamp'
FROM base WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL
UNION ALL
SELECT order_id, order_status, 'C6_delivered_without_approval',
       basket_value, payment_types, max_installments,
       'Status = delivered but payment approval timestamp missing'
FROM base WHERE order_status = 'delivered' AND order_approved_at IS NULL
UNION ALL
SELECT order_id, order_status, 'C7_carrier_before_purchase',
       basket_value, payment_types, max_installments,
       'Carrier pickup timestamp earlier than purchase'
FROM base WHERE order_delivered_carrier_date < order_purchase_timestamp
UNION ALL
SELECT order_id, order_status, 'C8_customer_before_carrier',
       basket_value, payment_types, max_installments,
       'Customer delivery earlier than carrier pickup'
FROM base WHERE order_delivered_customer_date < order_delivered_carrier_date
UNION ALL
SELECT order_id, order_status, 'C9_canceled_but_delivered',
       basket_value, payment_types, max_installments,
       'Status = canceled but a customer delivery date exists'
FROM base WHERE order_status = 'canceled' AND order_delivered_customer_date IS NOT NULL;

-- name: recon_exceptions
-- Exported exception list for the ops team (one row per order x check).
SELECT * FROM v_recon_exceptions ORDER BY check_id, amount_at_stake DESC;

-- name: recon_summary
-- One row per check: how many orders fail and how much money is involved.
SELECT check_id,
       COUNT(*)                                            AS orders_failing,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders), 3) AS pct_of_orders,
       ROUND(SUM(COALESCE(amount_at_stake, 0)), 2)          AS amount_at_stake_brl,
       MIN(description)                                    AS description
FROM v_recon_exceptions
GROUP BY check_id
ORDER BY check_id;

-- name: recon_no_items_by_status
-- Pattern: where do the item-less orders sit in the order lifecycle?
SELECT o.order_status,
       COUNT(*)                                          AS orders,
       SUM(CASE WHEN ov.order_id IS NULL THEN 1 ELSE 0 END) AS orders_without_items,
       ROUND(100.0 * SUM(CASE WHEN ov.order_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_without_items
FROM orders o
LEFT JOIN v_order_value ov ON ov.order_id = o.order_id
GROUP BY o.order_status
ORDER BY orders_without_items DESC;

-- name: recon_mismatch_by_installments
-- Pattern: does the payment-vs-basket gap scale with installments?
-- (Brazilian card instalments above ~6 often carry interest.)
SELECT CASE WHEN op.max_installments <= 1 THEN '01 (single)'
            WHEN op.max_installments <= 3 THEN '02-03'
            WHEN op.max_installments <= 6 THEN '04-06'
            ELSE '07+' END                                   AS installment_band,
       COUNT(*)                                              AS orders,
       SUM(CASE WHEN op.paid_value - ov.basket_value > 0.01 THEN 1 ELSE 0 END) AS overpaid,
       SUM(CASE WHEN ov.basket_value - op.paid_value > 0.01 THEN 1 ELSE 0 END) AS underpaid,
       ROUND(100.0 * SUM(CASE WHEN op.paid_value - ov.basket_value > 0.01 THEN 1 ELSE 0 END) / COUNT(*), 2) AS overpaid_pct,
       ROUND(AVG(CASE WHEN op.paid_value - ov.basket_value > 0.01
                      THEN 100.0 * (op.paid_value - ov.basket_value) / ov.basket_value END), 2) AS avg_overpay_pct_of_basket
FROM v_order_value ov
JOIN v_order_payment op ON op.order_id = ov.order_id
GROUP BY installment_band
ORDER BY installment_band;

-- name: recon_mismatch_by_month
-- Pattern: is the mismatch a one-off migration issue or ongoing?
SELECT SUBSTR(o.order_purchase_timestamp, 1, 7) AS purchase_month,
       COUNT(*) AS orders,
       SUM(CASE WHEN ABS(op.paid_value - ov.basket_value) > 0.01 THEN 1 ELSE 0 END) AS mismatched,
       ROUND(100.0 * SUM(CASE WHEN ABS(op.paid_value - ov.basket_value) > 0.01 THEN 1 ELSE 0 END) / COUNT(*), 2) AS mismatch_pct
FROM orders o
JOIN v_order_value ov ON ov.order_id = o.order_id
JOIN v_order_payment op ON op.order_id = o.order_id
GROUP BY purchase_month
ORDER BY purchase_month;
