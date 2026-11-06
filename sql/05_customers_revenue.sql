-- =====================================================================
-- 05_customers_revenue.sql  |  PROBLEM 5 - Retention, RFM & revenue mix
-- Note: customer_id is generated per order; customer_unique_id is the
-- real person. All customer metrics below use customer_unique_id.
-- =====================================================================

-- name: customer_orders
-- One row per delivered order with its customer sequence number.
SELECT c.customer_unique_id,
       o.order_id,
       o.order_purchase_timestamp,
       SUBSTR(o.order_purchase_timestamp, 1, 7) AS purchase_month,
       ROUND(op.paid_value, 2) AS paid_value,
       c.customer_state,
       CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late,
       r.review_score,
       ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id
                          ORDER BY o.order_purchase_timestamp) AS order_seq
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN v_order_payment op ON op.order_id = o.order_id
LEFT JOIN v_order_review r ON r.order_id = o.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL;

-- name: repeat_distribution
WITH f AS (
    SELECT c.customer_unique_id, COUNT(*) AS n_orders
    FROM orders o JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
)
SELECT CASE WHEN n_orders >= 4 THEN '4+' ELSE CAST(n_orders AS TEXT) END AS orders_per_customer,
       COUNT(*) AS customers,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM f), 2) AS pct_customers
FROM f
GROUP BY 1
ORDER BY 1;

-- name: first_order_experience_vs_repeat
-- Does a bad first delivery kill the second purchase?
-- First orders before 2018-03 only, so every customer had >= 6 months
-- to come back before the data ends.
WITH seq AS (
    SELECT c.customer_unique_id,
           o.order_purchase_timestamp,
           CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late,
           ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp) AS rn,
           COUNT(*) OVER (PARTITION BY c.customer_unique_id) AS n_orders
    FROM orders o JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
)
SELECT CASE WHEN is_late = 1 THEN 'first order late' ELSE 'first order on time' END AS first_experience,
       COUNT(*) AS customers,
       SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) AS came_back,
       ROUND(100.0 * AVG(CASE WHEN n_orders > 1 THEN 1.0 ELSE 0 END), 2) AS repeat_rate_pct
FROM seq
WHERE rn = 1 AND order_purchase_timestamp < '2018-03-01'
GROUP BY is_late;

-- name: revenue_by_category
SELECT COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
       COUNT(DISTINCT i.order_id) AS orders,
       ROUND(SUM(i.price), 2) AS gmv_brl,
       ROUND(SUM(i.freight_value), 2) AS freight_brl,
       ROUND(100.0 * SUM(i.freight_value) / SUM(i.price), 1) AS freight_pct_of_price,
       ROUND(AVG(i.price), 2) AS avg_item_price
FROM order_items i
JOIN products p ON p.product_id = i.product_id
LEFT JOIN category_translation t ON t.product_category_name = p.product_category_name
GROUP BY 1
ORDER BY gmv_brl DESC;

-- name: payment_mix
SELECT payment_type,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(payment_value), 2) AS value_brl,
       ROUND(100.0 * SUM(payment_value) / (SELECT SUM(payment_value) FROM payments), 2) AS pct_of_value,
       ROUND(AVG(payment_installments), 2) AS avg_installments
FROM payments
GROUP BY payment_type
ORDER BY value_brl DESC;
