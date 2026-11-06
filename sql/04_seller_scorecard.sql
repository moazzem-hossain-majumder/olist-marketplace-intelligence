-- =====================================================================
-- 04_seller_scorecard.sql  |  PROBLEM 4 - Seller performance & risk
-- One row per seller with the operational metrics an account manager
-- would be measured on. Scoring and tiering happen in Python
-- (notebooks/02_seller_risk_and_backlog.ipynb).
-- =====================================================================

-- name: seller_scorecard
WITH lost AS (
    -- Orders a seller accepted but never fulfilled.
    SELECT ps.seller_id,
           SUM(CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END) AS canceled_orders
    FROM orders o
    JOIN v_primary_seller ps ON ps.order_id = o.order_id
    GROUP BY ps.seller_id
),
del AS (
    SELECT seller_id,
           COUNT(*)                                  AS delivered_orders,
           ROUND(SUM(items_value), 2)                AS gmv_brl,
           ROUND(AVG(seller_late_handoff), 4)        AS late_handoff_rate,
           ROUND(AVG(is_late), 4)                    AS customer_late_rate,
           ROUND(AVG(seller_handling_days), 2)       AS avg_handling_days,
           ROUND(AVG(review_score), 3)               AS avg_review,
           ROUND(AVG(CASE WHEN review_score <= 2 THEN 1.0
                          WHEN review_score IS NULL THEN NULL ELSE 0 END), 4) AS bad_review_rate,
           MIN(purchase_month)                       AS first_month,
           MAX(purchase_month)                       AS last_month
    FROM v_delivered
    GROUP BY seller_id
)
SELECT s.seller_id, s.seller_state, s.seller_city,
       d.delivered_orders, d.gmv_brl,
       d.late_handoff_rate, d.customer_late_rate, d.avg_handling_days,
       d.avg_review, d.bad_review_rate,
       COALESCE(l.canceled_orders, 0) AS canceled_orders,
       ROUND(1.0 * COALESCE(l.canceled_orders, 0) /
             (d.delivered_orders + COALESCE(l.canceled_orders, 0)), 4) AS cancel_rate,
       d.first_month, d.last_month
FROM del d
JOIN sellers s ON s.seller_id = d.seller_id
LEFT JOIN lost l ON l.seller_id = d.seller_id
ORDER BY d.gmv_brl DESC;

-- name: seller_pareto
-- How concentrated is GMV across sellers?
WITH s AS (
    SELECT seller_id, SUM(price) AS gmv FROM order_items GROUP BY seller_id
),
r AS (
    SELECT seller_id, gmv,
           ROW_NUMBER() OVER (ORDER BY gmv DESC) AS rnk,
           COUNT(*) OVER () AS n,
           SUM(gmv) OVER (ORDER BY gmv DESC ROWS UNBOUNDED PRECEDING) AS cum_gmv,
           SUM(gmv) OVER () AS total_gmv
    FROM s
)
SELECT rnk AS seller_rank,
       ROUND(100.0 * rnk / n, 2)            AS pct_of_sellers,
       ROUND(gmv, 2)                        AS gmv_brl,
       ROUND(100.0 * cum_gmv / total_gmv, 2) AS cum_pct_of_gmv
FROM r
ORDER BY rnk;
