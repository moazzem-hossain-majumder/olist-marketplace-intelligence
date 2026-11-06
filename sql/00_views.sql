-- =====================================================================
-- 00_views.sql  |  Reusable analytical views (SQLite dialect)
-- Every later SQL file and notebook builds on these views.
-- =====================================================================

-- name: params
-- As-of date for the snapshot = last purchase timestamp in the data.
DROP VIEW IF EXISTS v_params;
CREATE VIEW v_params AS
SELECT MAX(order_purchase_timestamp) AS as_of_ts,
       DATE(MAX(order_purchase_timestamp)) AS as_of_date
FROM orders;

-- name: order_value
-- One row per order: what the basket says the customer owes.
DROP VIEW IF EXISTS v_order_value;
CREATE VIEW v_order_value AS
SELECT order_id,
       COUNT(*)                         AS n_items,
       COUNT(DISTINCT seller_id)        AS n_sellers,
       COUNT(DISTINCT product_id)       AS n_products,
       ROUND(SUM(price), 2)             AS items_value,
       ROUND(SUM(freight_value), 2)     AS freight_value,
       ROUND(SUM(price + freight_value), 2) AS basket_value,
       MAX(shipping_limit_date)         AS shipping_limit_date
FROM order_items
GROUP BY order_id;

-- name: order_payment
-- One row per order: what the payment ledger says was collected.
DROP VIEW IF EXISTS v_order_payment;
CREATE VIEW v_order_payment AS
SELECT order_id,
       COUNT(*)                         AS n_payment_rows,
       ROUND(SUM(payment_value), 2)     AS paid_value,
       MAX(payment_installments)        AS max_installments,
       GROUP_CONCAT(DISTINCT payment_type) AS payment_types,
       MAX(CASE WHEN payment_type = 'voucher' THEN 1 ELSE 0 END) AS used_voucher
FROM payments
GROUP BY order_id;

-- name: primary_seller
-- Order -> seller with the highest item value in that order (98.7% of
-- orders have a single seller; this resolves the remaining ones).
DROP VIEW IF EXISTS v_primary_seller;
CREATE VIEW v_primary_seller AS
SELECT order_id, seller_id, product_id
FROM (
    SELECT order_id, seller_id, product_id,
           ROW_NUMBER() OVER (PARTITION BY order_id
                              ORDER BY price DESC, order_item_id) AS rn
    FROM order_items
)
WHERE rn = 1;

-- name: order_review
-- Some orders have more than one review: keep the latest answer.
DROP VIEW IF EXISTS v_order_review;
CREATE VIEW v_order_review AS
SELECT order_id, review_score
FROM (
    SELECT order_id, review_score,
           ROW_NUMBER() OVER (PARTITION BY order_id
                              ORDER BY review_answer_timestamp DESC) AS rn
    FROM reviews
)
WHERE rn = 1;

-- name: delivered
-- Delivered orders with the fulfilment timeline split into stages:
--   purchase -> approval -> carrier handoff (seller) -> customer (carrier)
DROP VIEW IF EXISTS v_delivered;
CREATE VIEW v_delivered AS
SELECT o.order_id,
       o.customer_id,
       c.customer_unique_id,
       c.customer_state,
       c.customer_zip_code_prefix,
       ps.seller_id,
       s.seller_state,
       s.seller_zip_code_prefix,
       COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
       p.product_weight_g,
       ov.n_items, ov.n_sellers, ov.items_value, ov.freight_value, ov.basket_value,
       o.order_purchase_timestamp,
       SUBSTR(o.order_purchase_timestamp, 1, 7) AS purchase_month,
       ROUND((JULIANDAY(o.order_approved_at) - JULIANDAY(o.order_purchase_timestamp)) * 24, 2) AS approval_hours,
       ROUND(JULIANDAY(o.order_delivered_carrier_date) - JULIANDAY(o.order_approved_at), 2)    AS seller_handling_days,
       ROUND(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_delivered_carrier_date), 2) AS carrier_transit_days,
       ROUND(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp), 2) AS total_days,
       ROUND(JULIANDAY(o.order_estimated_delivery_date) - JULIANDAY(o.order_purchase_timestamp), 2) AS promised_days,
       ROUND(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date), 2) AS days_vs_promise,
       CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late,
       CASE WHEN o.order_delivered_carrier_date > ov.shipping_limit_date THEN 1 ELSE 0 END      AS seller_late_handoff,
       CASE WHEN c.customer_state = s.seller_state THEN 1 ELSE 0 END AS same_state,
       r.review_score
FROM orders o
JOIN customers c          ON c.customer_id = o.customer_id
JOIN v_order_value ov     ON ov.order_id = o.order_id
JOIN v_primary_seller ps  ON ps.order_id = o.order_id
JOIN sellers s            ON s.seller_id = ps.seller_id
LEFT JOIN products p      ON p.product_id = ps.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
LEFT JOIN v_order_review r ON r.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_delivered_carrier_date IS NOT NULL
  AND o.order_approved_at IS NOT NULL;
