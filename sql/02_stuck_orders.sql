-- =====================================================================
-- 02_stuck_orders.sql  |  PROBLEM 2 - The "stuck order" backlog
-- Orders still in a non-terminal status (created / approved / invoiced /
-- processing / shipped) at the data snapshot. Almost all are far past
-- their promised delivery date: money has been taken, nothing arrived.
-- =====================================================================

-- name: create_stuck_view
DROP VIEW IF EXISTS v_stuck_orders;
CREATE VIEW v_stuck_orders AS
SELECT o.order_id,
       o.order_status,
       o.order_purchase_timestamp,
       SUBSTR(o.order_purchase_timestamp, 1, 7)                         AS purchase_month,
       c.customer_state,
       ps.seller_id,
       COALESCE(ov.basket_value, op.paid_value, 0)                       AS order_value,
       op.paid_value,
       CASE WHEN o.order_delivered_carrier_date IS NOT NULL THEN 1 ELSE 0 END AS handed_to_carrier,
       CAST(JULIANDAY(p.as_of_date) - JULIANDAY(o.order_purchase_timestamp) AS INT)     AS age_days,
       CAST(JULIANDAY(p.as_of_date) - JULIANDAY(o.order_estimated_delivery_date) AS INT) AS days_past_promise,
       -- Bucket = the action owner, decided by where the order stopped.
       CASE
         WHEN o.order_status IN ('created', 'approved')        THEN 'B3_never_released_to_seller'
         WHEN o.order_status IN ('invoiced', 'processing')     THEN 'B2_seller_never_shipped'
         WHEN o.order_status = 'shipped'                       THEN 'B1_lost_in_carrier_network'
       END AS bucket
FROM orders o
CROSS JOIN v_params p
JOIN customers c             ON c.customer_id = o.customer_id
LEFT JOIN v_order_value ov   ON ov.order_id = o.order_id
LEFT JOIN v_order_payment op ON op.order_id = o.order_id
LEFT JOIN v_primary_seller ps ON ps.order_id = o.order_id
WHERE o.order_status IN ('created', 'approved', 'invoiced', 'processing', 'shipped');

-- name: stuck_orders
SELECT * FROM v_stuck_orders ORDER BY bucket, order_value DESC;

-- name: stuck_summary
SELECT bucket,
       COUNT(*)                                   AS orders,
       ROUND(SUM(order_value), 2)                 AS value_brl,
       ROUND(AVG(order_value), 2)                 AS avg_value_brl,
       ROUND(AVG(age_days), 0)                    AS avg_age_days,
       SUM(CASE WHEN days_past_promise > 0 THEN 1 ELSE 0 END) AS past_promise,
       COUNT(DISTINCT seller_id)                  AS sellers_involved
FROM v_stuck_orders
GROUP BY bucket
ORDER BY bucket;

-- name: stuck_by_month
SELECT purchase_month, bucket, COUNT(*) AS orders, ROUND(SUM(order_value), 2) AS value_brl
FROM v_stuck_orders
GROUP BY purchase_month, bucket
ORDER BY purchase_month, bucket;

-- name: stuck_seller_concentration
-- If a few sellers own most of the backlog, one call clears many orders.
WITH s AS (
    SELECT seller_id, COUNT(*) AS stuck_orders, ROUND(SUM(order_value), 2) AS stuck_value
    FROM v_stuck_orders
    WHERE seller_id IS NOT NULL
    GROUP BY seller_id
),
r AS (
    SELECT s.*,
           ROW_NUMBER() OVER (ORDER BY stuck_orders DESC, stuck_value DESC) AS seller_rank,
           SUM(stuck_orders) OVER (ORDER BY stuck_orders DESC, stuck_value DESC
                                   ROWS UNBOUNDED PRECEDING) AS cum_orders,
           SUM(stuck_orders) OVER () AS total_orders
    FROM s
)
SELECT seller_rank, seller_id, stuck_orders, stuck_value,
       ROUND(100.0 * cum_orders / total_orders, 1) AS cum_pct_of_backlog
FROM r
ORDER BY seller_rank;
