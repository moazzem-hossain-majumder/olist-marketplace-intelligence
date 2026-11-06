# Memo: Olist Operations & Growth Review

**To:** Head of Operations, Head of Growth
**From:** Minhaz Alam Jisan, Data Analyst
**Data:** Olist public dataset, 99,441 orders (Jan 2017 to Aug 2018 used for monthly figures)

## Summary

1. **Reconciliation:** 1,425 orders don't match across the order, item and payment tables, worth about R$ 202k. Most of it (R$ 162.6k, 775 orders) is orders that became unavailable: the items were removed, but the payment record stayed. We should check that these were refunded.
2. **Stuck orders:** 1,729 orders (R$ 317k) never reached a final status, and all are past their promised date. With a simple priority rule, 4 agents can clear them in about 10 working days. A nightly ageing rule stops new ones from piling up.
3. **Late deliveries:** 8.2% of orders arrive late, and over half of those get a 1-2 star review. Late seller handoff is the biggest risk factor per order (about 5x the odds), but most late orders were handed over on time, so the carrier side needs attention too.
4. **Sellers:** 32 sellers cause 20% of all late handoffs. Three account managers can cover them. The risk score held up in a back-test on later data.
5. **Retention:** 97% of customers order only once. I could not confirm that a late first delivery reduces repeat orders once other factors are controlled for.

## 1. Reconciliation

| Issue | Orders | Amount (R$) | Likely cause | Suggested fix |
|---|---:|---:|---|---|
| Payment but no items | 775 | 162.6k | Items removed on stock-out, payment kept | Automatic refund on stock-out, daily check |
| Carrier pickup before purchase | 166 | 23.1k | Only from Apr 2018 onwards, median gap 36 min: timestamp change | Fix the carrier timestamps (UTC) |
| Paid amount different from basket | 432 | 8.0k | Instalment interest and discounts not stored separately | Add interest and discount fields |
| Status doesn't match dates | 51 | 8.6k | Manual status changes | Status changes only through system events |

## 2. Stuck orders

| Where it stopped | Orders | Amount (R$) | Action |
|---|---:|---:|---|
| Shipped, never delivered | 1,107 | 177k | Carrier trace; refund if not found in 5 days |
| Seller never shipped | 615 | 139k | Contact seller (grouped per seller): ship in 48h or cancel and refund |
| Never released to seller | 7 | 0.9k | Cancel and refund |

Priority: P1 is R$ 200 and above (24% of orders, 61% of the value), P2 is R$ 80-200, and P3 (under R$ 80) is closed automatically (35% of orders). Clearing P1 and P2 takes about 233 agent hours, or 10 working days with 4 agents.

## 3. Late deliveries

- Late orders spend 25.7 days with the carrier on average, compared with 7.9 days for on-time orders.
- The Feb-Mar 2018 spike (21% late) happened while seller handoffs were normal, so it was a carrier problem.
- In Aug 2018 the promised window was cut from about 28 to 15 days. Orders arrived faster than ever, but more of them counted as late.
- Fixing all late seller handoffs would only bring the late rate from 8.2% to about 6.6%.

Suggested actions: alerts to sellers before the shipping deadline, weekly transit-time tracking per route with a second carrier on the worst routes, and promised dates based on actual transit times per route.

## 4. Sellers

- The top 10% of sellers make 67% of GMV.
- 795 sellers with at least 20 orders were scored on late handoffs, bad reviews and cancellations.
- 32 high-GMV, high-risk sellers should get an account manager (about 11 each for 3 managers). Low-GMV, high-risk sellers (119) get automatic reminders and a ranking penalty.

## 5. Retention

- Under 1% of each monthly cohort orders again the next month, and about 1.9% within 6 months.
- Two high-value one-time segments bring 68% of revenue. These are the best targets for win-back campaigns.
- Repeat rate after a late first order: 3.19% vs 4.04%. This is significant on its own, but not after controlling for state, month and spend (p = 0.13). If this question matters, it should be tested with an A/B test.

## Next 90 days

| When | What | Target |
|---|---|---|
| Month 1 | Clear the backlog, add the nightly ageing rule, check refunds for the 775 orders | Open orders past promise: 1,729 to under 50 |
| Month 1 | Account managers start with the 32 Q1 sellers | Their share of late handoffs: 20% to 10% |
| Month 2 | Fix payment fields and carrier timestamps | Exceptions: 1,425 to under 200 |
| Month 2 | Track transit time per route, add a second carrier on the worst routes | Late rate: 8.2% to 6.5% |
| Month 3 | Promised dates per route, A/B test a delay voucher | 1-2 star share of late orders: 54% to 40% |

Assumptions (all can be changed in the Excel file): 12 minutes per carrier trace, 15 minutes per seller call plus 3 minutes per order, 6 productive hours per agent per day, 12 sellers per account manager.
