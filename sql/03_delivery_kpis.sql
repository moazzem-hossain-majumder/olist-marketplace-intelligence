-- =====================================================================
-- 03_delivery_kpis.sql  |  PROBLEM 3 - Late delivery: where is time lost?
-- =====================================================================

-- name: monthly_kpis
-- Executive KPI table (feeds the Excel dashboard).
WITH all_orders AS (
    SELECT SUBSTR(o.order_purchase_timestamp, 1, 7) AS purchase_month,
           COUNT(*)                                  AS orders_placed,
           SUM(CASE WHEN o.order_status IN ('canceled', 'unavailable') THEN 1 ELSE 0 END) AS orders_lost,
           ROUND(SUM(COALESCE(ov.items_value, 0)), 2) AS gmv_brl,
           ROUND(SUM(COALESCE(ov.freight_value, 0)), 2) AS freight_brl
    FROM orders o
    LEFT JOIN v_order_value ov ON ov.order_id = o.order_id
    GROUP BY 1
),
deliv AS (
    SELECT purchase_month,
           COUNT(*)                         AS orders_delivered,
           ROUND(AVG(is_late) * 100, 2)     AS late_pct,
           ROUND(AVG(seller_late_handoff) * 100, 2) AS seller_late_handoff_pct,
           ROUND(AVG(total_days), 2)        AS avg_delivery_days,
           ROUND(AVG(promised_days), 2)     AS avg_promised_days,
           ROUND(AVG(review_score), 3)      AS avg_review,
           ROUND(AVG(CASE WHEN review_score <= 2 THEN 1.0 ELSE 0 END) * 100, 2) AS bad_review_pct
    FROM v_delivered
    GROUP BY 1
)
SELECT a.purchase_month, a.orders_placed, d.orders_delivered, a.orders_lost,
       a.gmv_brl, a.freight_brl,
       d.late_pct, d.seller_late_handoff_pct, d.avg_delivery_days,
       d.avg_promised_days, d.avg_review, d.bad_review_pct
FROM all_orders a
LEFT JOIN deliv d USING (purchase_month)
-- Sep-Dec 2016 and Sep-Oct 2018 are partial ramp-up / cut-off months
WHERE a.purchase_month BETWEEN '2017-01' AND '2018-08'
ORDER BY a.purchase_month;

-- name: stage_decomposition_monthly
-- Average days spent in each fulfilment stage, per purchase month.
SELECT purchase_month,
       ROUND(AVG(approval_hours) / 24, 2)  AS approval_days,
       ROUND(AVG(seller_handling_days), 2) AS seller_handling_days,
       ROUND(AVG(carrier_transit_days), 2) AS carrier_transit_days,
       ROUND(AVG(total_days), 2)           AS total_days,
       ROUND(AVG(promised_days), 2)        AS promised_days,
       ROUND(AVG(is_late) * 100, 2)        AS late_pct
FROM v_delivered
WHERE purchase_month BETWEEN '2017-01' AND '2018-08'
GROUP BY purchase_month
ORDER BY purchase_month;

-- name: late_vs_handoff
-- The single most important cut: did the seller miss the carrier cut-off?
SELECT seller_late_handoff,
       COUNT(*)                         AS orders,
       ROUND(AVG(is_late) * 100, 2)     AS customer_late_pct,
       ROUND(AVG(review_score), 2)      AS avg_review,
       ROUND(AVG(seller_handling_days), 2) AS avg_seller_handling_days,
       ROUND(AVG(carrier_transit_days), 2) AS avg_carrier_transit_days
FROM v_delivered
GROUP BY seller_late_handoff;

-- name: late_vs_review
SELECT is_late,
       COUNT(*) AS orders_with_review,
       ROUND(AVG(review_score), 2) AS avg_review,
       ROUND(AVG(CASE WHEN review_score <= 2 THEN 1.0 ELSE 0 END) * 100, 1) AS pct_1_or_2_star,
       ROUND(AVG(CASE WHEN review_score = 5 THEN 1.0 ELSE 0 END) * 100, 1) AS pct_5_star
FROM v_delivered
WHERE review_score IS NOT NULL
GROUP BY is_late;

-- name: late_by_customer_state
SELECT customer_state,
       COUNT(*)                     AS orders,
       ROUND(AVG(is_late) * 100, 2) AS late_pct,
       ROUND(AVG(total_days), 1)    AS avg_days,
       ROUND(AVG(promised_days), 1) AS avg_promised_days,
       ROUND(AVG(carrier_transit_days), 1) AS avg_transit_days
FROM v_delivered
GROUP BY customer_state
HAVING COUNT(*) >= 100
ORDER BY late_pct DESC;

-- name: late_by_route
-- Seller state -> customer state lanes with enough volume to matter.
SELECT seller_state || ' -> ' || customer_state AS lane,
       COUNT(*) AS orders,
       ROUND(AVG(is_late) * 100, 2) AS late_pct,
       ROUND(AVG(carrier_transit_days), 1) AS avg_transit_days,
       SUM(is_late) AS late_orders
FROM v_delivered
GROUP BY lane
HAVING COUNT(*) >= 300
ORDER BY late_orders DESC
LIMIT 20;
