# Case Study: Marketplace Operations & Growth Analyst

I wrote this prompt in the format of an operations analyst take-home assignment: separate problems, a fixed team, and a plan that should be based on numbers and possible to start right away.

## Context

You have joined the Central Operations team of **Olist**, a Brazilian marketplace that connects thousands of small sellers to customers across the large retail sites. An order moves through four stages:

| Stage | What happens | Systems of record |
|---|---|---|
| 1. Checkout | Customer pays (card in up to 24 instalments, *boleto*, voucher, debit) | `orders`, `payments` |
| 2. Seller handling | Seller picks, packs and hands the parcel to the carrier before a `shipping_limit_date` | `order_items` |
| 3. Carrier transit | Carrier delivers by the `estimated_delivery_date` promised at checkout | `orders` timestamps |
| 4. Post-delivery | Customer leaves a 1-5 star review; may buy again | `reviews`, `customers` |

**Data:** the real Olist public dataset: 99,441 orders, 9 tables, Sep-2016 to Oct-2018 ([source](https://github.com/olist/work-at-olist-data)).

**Your resources** (use less where you can):
1. A team of 6 operations agents (data entry, seller and carrier calls)
2. 3 seller-success account managers
3. 2 hours of one engineer's time per week
4. SQL, Python, Excel

**Format:** a short memo with the supporting analysis (SQL, notebooks, an Excel model) that leadership can act on Monday morning. State every assumption.

---

## Problem 1: Order-to-cash reconciliation

Finance says the revenue reported by the order system does not match what the payment ledger collected. Four tables describe each order: the order header, the line items, the payments, and the reviews.

1. Design reconciliation checks between these systems and run them over all orders.
2. Quantify each failure: number of orders and BRL at stake.
3. For each failure mode, find the **pattern** (status, time period, payment method, instalments…) that points to the root cause.
4. Propose one preventive and one detective control per failure mode, with an owner.

## Problem 2: The stuck-order backlog

A number of orders never reach a final status (delivered or canceled). The customer paid, and nothing has happened since.

1. How many orders are stuck, how much money is involved, and where in the process did each one stop?
2. Bucket and prioritise them so the ops team gets the most value per hour.
3. How long will it take to clear the backlog with the team you have? Show the model.
4. What process change stops the backlog from building up again?

## Problem 3: Late delivery root cause

About 1 in 12 delivered orders arrives after the promised date.

1. Break the delivery timeline into stages. Where do late orders lose time?
2. Which factors drive lateness once the others are held constant? Is it the seller, the carrier, the distance, or the promise itself?
3. What happens to the customer review when an order is late?
4. If sellers stopped missing the carrier cut-off, how much would the late rate fall? Build a what-if that leadership can play with.

## Problem 4: Seller risk and account-manager focus

You have 3 account managers and ~3,000 sellers.

1. How concentrated is GMV across sellers?
2. Build a seller risk score that does not penalise small sellers just because they have few orders.
3. Which sellers should the account managers own this quarter, and what should happen to everyone else?
4. **Prove** that the score predicts future performance, not just past performance.

## Problem 5: Retention and the cost of a bad first experience

1. What does customer retention look like by monthly cohort?
2. Segment customers so marketing knows who is worth a win-back campaign.
3. Does a late first delivery reduce the chance of a second purchase? Test it properly: watch for confounding.
4. Put a BRL value on the effect.

---

### Deliverables checklist

- [x] SQL that a reviewer can re-run (`/sql`)
- [x] Executed notebooks with charts and statistical tests (`/notebooks`)
- [x] Excel workbook with live formulas: dashboard, worklist, capacity model, what-if (`/excel`)
- [x] Executive memo (`/reports/executive_memo.md`)
