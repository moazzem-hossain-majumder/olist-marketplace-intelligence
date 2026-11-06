"""
Step 5 - Build the Excel deliverable: excel/Olist_Ops_Command_Center.xlsx

Reads the CSVs produced by SQL (step 3) and the notebooks (step 4) and writes an
operations workbook in which every KPI, total, and capacity figure is a live Excel
formula. Change a blue input cell and the whole workbook updates.

Sheets
  Cover            what the workbook is, how to use it, colour legend
  Dashboard        KPI tiles + month selector (INDEX/MATCH) + native charts
  Monthly_KPIs     SQL output + formula-derived ratios
  Recon_Checks     Problem 1 - reconciliation checks, owners, controls
  Backlog_Worklist Problem 2 - prioritised 1,729-order worklist (filterable tracker)
  Capacity_Model   Problem 2/4 - team hours, days-to-clear, account-manager coverage
  Seller_Risk      Problem 4 - scored sellers with quadrant summary
  WhatIf_Handoff   Problem 3 - late-handoff reduction scenario

Usage:  python scripts/04_build_excel.py
"""
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.comments import Comment
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT = ROOT / "excel" / "Olist_Ops_Command_Center.xlsx"

# ---------- style helpers ----------
F = "Arial"
HEADER_GREEN, OUTPUT_FILL, LIGHT, GREY = "375623", "E2EFDA", "F2F2F2", "595959"
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
HDR_FILL = PatternFill("solid", fgColor=HEADER_GREEN)
TILE_FILL = PatternFill("solid", fgColor=LIGHT)
thin = Side(style="thin", color="D9D9D9")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)


def font(**kw):
    base = dict(name=F, size=10, color="000000")
    base.update(kw)
    return Font(**base)


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = font(size=16, bold=True, color=HEADER_GREEN)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = font(size=10, italic=True, color=GREY)
    ws.sheet_view.showGridLines = False


def header(ws, row, col, labels, widths=None):
    for i, lab in enumerate(labels):
        c = ws.cell(row=row, column=col + i, value=lab)
        c.font = font(bold=True, color="FFFFFF")
        c.fill = HDR_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX
        if widths:
            ws.column_dimensions[get_column_letter(col + i)].width = widths[i]
    ws.row_dimensions[row].height = 40


def inp(cell, value, note=None, fmt=None):
    """Blue input cell with yellow fill and an explanatory comment."""
    cell.value = value
    cell.font = font(color="0000FF", bold=True)
    cell.fill = INPUT_FILL
    cell.border = BOX
    if fmt:
        cell.number_format = fmt
    if note:
        cell.comment = Comment(note, "Analyst")


def write_df(ws, df, r0, c0, fmts=None, link_color=False):
    for i, row in enumerate(df.itertuples(index=False)):
        for j, v in enumerate(row):
            c = ws.cell(row=r0 + i, column=c0 + j, value=(None if pd.isna(v) else v))
            c.font = font()
            c.border = BOX
            if fmts and df.columns[j] in fmts:
                c.number_format = fmts[df.columns[j]]


def main() -> None:
    kpi = pd.read_csv(P / "monthly_kpis.csv")
    recon = pd.read_csv(P / "recon_summary.csv")
    stuck = pd.read_csv(P / "stuck_orders_prioritized.csv")
    sellers = pd.read_csv(P / "seller_risk_tiers.csv")
    whatif = pd.read_csv(P / "whatif_handoff.csv")
    base = pd.read_csv(P / "whatif_baseline.csv").set_index("metric").value

    wb = Workbook()

    # ================= Monthly_KPIs =================
    mk = wb.active
    mk.title = "Monthly_KPIs"
    title(mk, "Monthly KPIs (Jan-2017 to Aug-2018)", "Source: sql/03_delivery_kpis.sql -> monthly_kpis. Columns M-P are Excel formulas.")
    cols = ["Month", "Orders placed", "Orders delivered", "Orders lost (canceled/unavailable)", "GMV (BRL)",
            "Freight (BRL)", "Late delivery %", "Seller late handoff %", "Avg delivery days", "Avg promised days",
            "Avg review (1-5)", "1-2 star review %", "AOV (BRL)", "Lost order rate", "Freight % of GMV", "MoM GMV growth"]
    header(mk, 4, 1, cols, [10, 10, 10, 13, 13, 12, 10, 11, 10, 10, 10, 10, 10, 10, 10, 11])
    k = kpi.copy()
    for c in ["late_pct", "seller_late_handoff_pct", "bad_review_pct"]:
        k[c] = k[c] / 100  # store percentages as fractions
    write_df(mk, k, 5, 1, {"gmv_brl": "#,##0", "freight_brl": "#,##0", "late_pct": "0.0%",
                           "seller_late_handoff_pct": "0.0%", "bad_review_pct": "0.0%",
                           "avg_delivery_days": "0.0", "avg_promised_days": "0.0", "avg_review": "0.00",
                           "orders_placed": "#,##0", "orders_delivered": "#,##0", "orders_lost": "#,##0"})
    n = len(k)
    last = 4 + n
    for r in range(5, last + 1):
        for col, f, fmt in [("M", f"=IFERROR(E{r}/B{r},0)", "#,##0.00"), ("N", f"=IFERROR(D{r}/B{r},0)", "0.0%"),
                            ("O", f"=IFERROR(F{r}/E{r},0)", "0.0%"),
                            ("P", "" if r == 5 else f"=IFERROR(E{r}/E{r-1}-1,0)", "0.0%;[Red]-0.0%")]:
            c = mk[f"{col}{r}"]
            c.value = f or None
            c.number_format = fmt
            c.font = font()
            c.border = BOX
    mk.freeze_panes = "B5"

    # ================= Dashboard =================
    db = wb.create_sheet("Dashboard", 0)
    title(db, "Olist Marketplace - Operations Command Center",
          "Real data: Olist Brazilian E-Commerce public dataset, ~99k orders, Jan-2017 to Aug-2018. All tiles are live formulas.")
    for col, w in zip("ABCDEFGHIJ", [2, 22, 14, 18, 14, 22, 14, 18, 14, 2]):
        db.column_dimensions[col].width = w
    rng = lambda c: f"Monthly_KPIs!${c}$5:${c}${last}"
    tiles = [
        ("Orders placed", f"=SUM({rng('B')})", "#,##0"),
        ("GMV (BRL)", f"=SUM({rng('E')})", '"R$ "#,##0,"k"'),
        ("Late delivery rate", f"=SUMPRODUCT({rng('G')},{rng('C')})/SUM({rng('C')})", "0.0%"),
        ("Avg review score", f"=SUMPRODUCT({rng('K')},{rng('C')})/SUM({rng('C')})", "0.00"),
        ("Seller late handoff", f"=SUMPRODUCT({rng('H')},{rng('C')})/SUM({rng('C')})", "0.0%"),
        ("Stuck orders (backlog)", "=COUNTA(Backlog_Worklist!B5:B5000)", "#,##0"),
        ("Recon exceptions", "=SUM(Recon_Checks!C5:C13)", "#,##0"),
        ("Money in recon gaps", "=SUM(Recon_Checks!E5:E13)", '"R$ "#,##0,"k"'),
    ]
    for i, (lab, f, fmt) in enumerate(tiles):
        r = 4 + (i // 4) * 3
        c = 2 + (i % 4) * 2
        lc = db.cell(row=r, column=c, value=lab)
        lc.font = font(size=9, color=GREY, bold=True)
        vc = db.cell(row=r + 1, column=c, value=f)
        vc.font = font(size=18, bold=True, color=HEADER_GREEN)
        vc.number_format = fmt
        for rr in (r, r + 1):
            for cc in (c, c + 1):
                db.cell(row=rr, column=cc).fill = TILE_FILL
        db.merge_cells(start_row=r + 1, start_column=c, end_row=r + 1, end_column=c + 1)
        db.row_dimensions[r + 1].height = 30

    # Month selector
    db["B11"] = "Month drill-down"
    db["B11"].font = font(size=12, bold=True, color=HEADER_GREEN)
    db["B12"] = "Select month (yyyy-mm):"
    db["B12"].font = font(bold=True)
    inp(db["C12"], kpi.purchase_month.iloc[-1], "Pick any month from the dropdown; the table below updates with INDEX/MATCH.")
    dv = DataValidation(type="list", formula1=f"=Monthly_KPIs!$A$5:$A${last}", allow_blank=False)
    db.add_data_validation(dv)
    dv.add("C12")
    header(db, 13, 2, ["Metric", "Selected month", "Prior month", "Change"])
    drill = [("Orders placed", "B", "#,##0"), ("GMV (BRL)", "E", "#,##0"), ("Late delivery %", "G", "0.0%"),
             ("Seller late handoff %", "H", "0.0%"), ("Avg delivery days", "I", "0.0"),
             ("Avg promised days", "J", "0.0"), ("Avg review", "K", "0.00"), ("1-2 star review %", "L", "0.0%"),
             ("AOV (BRL)", "M", "#,##0.00")]
    for i, (lab, col, fmt) in enumerate(drill):
        r = 14 + i
        db.cell(row=r, column=2, value=lab).font = font()
        m = f"MATCH($C$12,Monthly_KPIs!$A$5:$A${last},0)"
        cur = db.cell(row=r, column=3, value=f"=INDEX({rng(col)},{m})")
        prv = db.cell(row=r, column=4, value=f"=IFERROR(INDEX({rng(col)},{m}-1),\"-\")")
        chg = db.cell(row=r, column=5, value=f"=IFERROR(C{r}-D{r},\"-\")")
        for c_ in (cur, prv, chg):
            c_.number_format = fmt
            c_.font = font()
            c_.border = BOX
        db.cell(row=r, column=2).border = BOX
        chg.number_format = fmt.replace("0.0%", "+0.0%;-0.0%") if "%" in fmt else "+" + fmt + ";-" + fmt

    # Charts (native Excel charts, read from Monthly_KPIs)
    cats = Reference(mk, min_col=1, min_row=5, max_row=last)
    c1 = BarChart(); c1.type = "col"; c1.title = "Orders placed per month"; c1.style = 10
    c1.add_data(Reference(mk, min_col=2, min_row=4, max_row=last), titles_from_data=True); c1.set_categories(cats)
    c1.legend = None; c1.height, c1.width = 7.2, 12.5; c1.y_axis.majorGridlines = None
    c1.series[0].graphicalProperties.solidFill = "ED7D31"; c1.series[0].graphicalProperties.line.noFill = True
    db.add_chart(c1, "F11")
    c2 = LineChart(); c2.title = "Late delivery vs late handoff (%)"; c2.style = 12
    c2.add_data(Reference(mk, min_col=7, max_col=8, min_row=4, max_row=last), titles_from_data=True); c2.set_categories(cats)
    c2.height, c2.width = 7.5, 12.5; c2.y_axis.number_format = "0%"; c2.legend.position = "b"
    for s, colr in zip(c2.series, ["C00000", "70AD47"]):
        s.graphicalProperties.line.solidFill = colr; s.graphicalProperties.line.width = 22000; s.smooth = False
    db.add_chart(c2, "B25")
    c3 = LineChart(); c3.title = "Average review score"; c3.style = 12
    c3.add_data(Reference(mk, min_col=11, min_row=4, max_row=last), titles_from_data=True); c3.set_categories(cats)
    c3.height, c3.width = 7.5, 12.5; c3.legend = None; c3.y_axis.scaling.min = 3.5; c3.y_axis.scaling.max = 4.5
    c3.series[0].graphicalProperties.line.solidFill = "7030A0"; c3.series[0].graphicalProperties.line.width = 22000; c3.series[0].smooth = False
    db.add_chart(c3, "F25")

    # ================= Recon_Checks =================
    rc = wb.create_sheet("Recon_Checks")
    title(rc, "Problem 1 - Order-to-cash reconciliation checks", "Source: sql/01_reconciliation.sql. Share columns are formulas.")
    header(rc, 4, 1, ["Check", "Description", "Orders failing", "Share of all orders", "Amount at stake (BRL)",
                      "Share of money", "Root cause (evidence)", "Control", "Owner"],
           [30, 44, 11, 11, 14, 11, 46, 46, 12])
    rca = {
        "C1_order_without_items": ("99% of 'unavailable' orders lost their items on stock-out; payment row kept", "Stock-out triggers refund + void line; daily refund-match query", "Finance Ops"),
        "C2_order_without_payment": ("Single orphan record", "Weekly exception report", "Data Eng"),
        "C3_overpaid_vs_basket": ("Instalment interest not stored: 0.06% -> 0.88% mismatch as instalments rise", "Add interest_amount to payment schema; tolerance rule", "Payments"),
        "C4_underpaid_vs_basket": ("Partial voucher capture / discounts not stored", "Add discount_amount; flag gap > R$1", "Payments"),
        "C5_delivered_without_delivery_date": ("Manual status override", "Status change only via carrier event", "Logistics"),
        "C6_delivered_without_approval": ("Manual status override", "Block 'delivered' without approval", "Payments"),
        "C7_carrier_before_purchase": ("Started Apr-2018 only, median gap 36 min: timestamp recording change", "Carrier API in UTC; reject events earlier than purchase", "Data Eng"),
        "C8_customer_before_carrier": ("Same timestamp issue as C7", "Same as C7", "Data Eng"),
        "C9_canceled_but_delivered": ("Cancel after delivery not reversed", "Return flow must set its own status", "CX"),
    }
    for i, r_ in recon.iterrows():
        r = 5 + i
        vals = [r_.check_id, r_.description, int(r_.orders_failing), f"=C{r}/{99441}", float(r_.amount_at_stake_brl),
                f"=E{r}/SUM($E$5:$E$13)", *rca[r_.check_id]]
        for j, v in enumerate(vals):
            c = rc.cell(row=r, column=1 + j, value=v)
            c.font = font(); c.border = BOX
            c.alignment = Alignment(wrap_text=True, vertical="top")
        rc[f"D{r}"].number_format = "0.000%"; rc[f"E{r}"].number_format = "#,##0"; rc[f"F{r}"].number_format = "0.0%"
    rc["A14"] = "Total"; rc["A14"].font = font(bold=True)
    for col, f, fmt in [("C", "=SUM(C5:C13)", "#,##0"), ("E", "=SUM(E5:E13)", "#,##0")]:
        rc[f"{col}14"] = f; rc[f"{col}14"].font = font(bold=True); rc[f"{col}14"].number_format = fmt
    rc["A16"] = "Note: 99,441 = total orders in the dataset (denominator for 'Share of all orders')."
    rc["A16"].font = font(italic=True, color=GREY, size=9)
    rc.conditional_formatting.add("E5:E13", DataBarRule(start_type="min", end_type="max", color="F4B183"))

    # ================= Backlog_Worklist =================
    bl = wb.create_sheet("Backlog_Worklist")
    title(bl, "Problem 2 - Stuck-order worklist (prioritised)",
          "Source: notebooks/02 -> stuck_orders_prioritized.csv. Ops fills columns N-O. Sorted: priority, bucket, oldest first.")
    s = stuck.copy()
    s["first_of_seller_batch"] = (~s.duplicated(["seller_id", "bucket", "priority"])).astype(int)
    cols = ["work_rank", "order_id", "priority", "bucket", "order_status", "purchase_month", "age_days",
            "days_past_promise", "order_value", "customer_state", "seller_id", "seller_batch_size", "first_of_seller_batch"]
    header(bl, 4, 1, ["Rank", "Order ID", "Priority", "Bucket", "Status", "Purchase month", "Age (days)",
                      "Days past promise", "Value (BRL)", "Cust. state", "Seller ID", "Seller batch size",
                      "First in seller batch", "Ops status", "Owner", "Recommended action"],
           [6, 34, 8, 28, 10, 9, 8, 9, 10, 7, 34, 8, 8, 12, 12, 70])
    write_df(bl, s[cols], 5, 1, {"order_value": "#,##0.00"})
    for i, a in enumerate(s.recommended_action):
        r = 5 + i
        bl.cell(row=r, column=14, value="Open").font = font(color="0000FF")
        bl.cell(row=r, column=15).font = font(color="0000FF")
        bl.cell(row=r, column=16, value=a).font = font(size=9)
        for cc in (14, 15, 16):
            bl.cell(row=r, column=cc).border = BOX
    bl_last = 4 + len(s)
    dvs = DataValidation(type="list", formula1='"Open,In progress,Resolved - delivered,Resolved - refunded,Auto-closed"')
    bl.add_data_validation(dvs); dvs.add(f"N5:N{bl_last}")
    bl.auto_filter.ref = f"A4:P{bl_last}"
    bl.freeze_panes = "C5"
    bl.conditional_formatting.add(f"G5:G{bl_last}", ColorScaleRule(start_type="min", start_color="FFFFFF", end_type="max", end_color="F4B183"))

    # ================= Seller_Risk =================
    sr = wb.create_sheet("Seller_Risk")
    title(sr, "Problem 4 - Seller risk scorecard (>= 20 delivered orders)",
          "Source: notebooks/03 -> seller_risk_tiers.csv. Rates are empirical-Bayes shrunk. Summary table = COUNTIFS/SUMIFS.")
    header(sr, 4, 1, ["Quadrant", "Sellers", "GMV (BRL)", "GMV share", "Late handoffs", "Share of late handoffs", "Avg risk score"],
           [30, 10, 14, 10, 11, 12, 11])
    quads = ["Q1 Fix now (AM-owned)", "Q2 Protect (keep happy)", "Q3 Automate nudges / restrict", "Q4 Self-serve"]
    s0 = 13  # data start row
    sl = s0 + len(sellers) - 1
    for i, q in enumerate(quads):
        r = 5 + i
        sr.cell(row=r, column=1, value=q)
        sr.cell(row=r, column=2, value=f"=COUNTIFS($D${s0}:$D${sl},A{r})")
        sr.cell(row=r, column=3, value=f"=SUMIFS($H${s0}:$H${sl},$D${s0}:$D${sl},A{r})").number_format = "#,##0"
        sr.cell(row=r, column=4, value=f"=C{r}/SUM($C$5:$C$8)").number_format = "0.0%"
        sr.cell(row=r, column=5, value=f"=SUMIFS($L${s0}:$L${sl},$D${s0}:$D${sl},A{r})").number_format = "#,##0"
        sr.cell(row=r, column=6, value=f"=E{r}/SUM($E$5:$E$8)").number_format = "0.0%"
        sr.cell(row=r, column=7, value=f"=AVERAGEIFS($F${s0}:$F${sl},$D${s0}:$D${sl},A{r})").number_format = "0.0"
        for cc in range(1, 8):
            sr.cell(row=r, column=cc).font = font(bold=(i == 0)); sr.cell(row=r, column=cc).border = BOX
    sr["A9"] = "Total"; sr["A9"].font = font(bold=True)
    for col in "BCE":
        sr[f"{col}9"] = f"=SUM({col}5:{col}8)"; sr[f"{col}9"].font = font(bold=True); sr[f"{col}9"].number_format = "#,##0"
    labels = ["Seller ID", "State", "City", "Quadrant", "Tier", "Risk score", "Delivered orders", "GMV (BRL)",
              "Late-handoff rate", "1-2 star rate", "Cancel rate", "Late handoffs", "Bad reviews", "Canceled"]
    header(sr, 12, 1, labels, [34, 7, 18, 30, 10, 10, 10, 12, 10, 10, 10, 10, 10, 10])
    write_df(sr, sellers, s0, 1, {"risk_score": "0.0", "gmv": "#,##0", "handoff_rate": "0.0%",
                                 "bad_review_rate": "0.0%", "cancel_rate": "0.0%"})
    sr.conditional_formatting.add(f"F{s0}:F{sl}", ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                                                                 mid_type="num", mid_value=50, mid_color="FFF2CC",
                                                                 end_type="num", end_value=100, end_color="F4B183"))
    sr.auto_filter.ref = f"A12:N{sl}"
    sr.freeze_panes = f"B{s0}"

    # ================= Capacity_Model =================
    cm = wb.create_sheet("Capacity_Model")
    title(cm, "Capacity model - how long to clear the backlog, and how many account managers?",
          "Yellow cells with blue text are assumptions: change them. Counts are COUNTIFS on the live worklist / scorecard.")
    cm.column_dimensions["A"].width = 52; cm.column_dimensions["B"].width = 14; cm.column_dimensions["C"].width = 70
    rows = [
        ("A. Team assumptions", None, None, None),
        ("Ops agents assigned to backlog", 4, "Assumption: share of a 6-person ops pod", "0"),
        ("Productive hours per agent per day", 6, "Assumption: 8h shift minus meetings/breaks", "0.0"),
        ("Minutes per B1 carrier trace (per order)", 12, "Assumption: carrier portal lookup + claim form", "0"),
        ("Minutes per B2 seller contact (per seller batch)", 15, "Assumption: one call/e-mail clears all of that seller's orders", "0"),
        ("Minutes per B2 order inside a batch", 3, "Assumption: per-order update after the seller call", "0"),
        ("Minutes per auto-closed P3 order (QA spot check)", 0.5, "Assumption: rule-based refund, 1 in 10 spot-checked", "0.0"),
        ("Engineering hours to build ageing rule (one-off)", 2, "Assumption: nightly SQL job + status update", "0.0"),
        ("B. Backlog volume (live from Backlog_Worklist)", None, None, None),
        ("B1 orders needing a trace (P1+P2)", '=COUNTIFS(Backlog_Worklist!$D$5:$D$5000,"B1*",Backlog_Worklist!$C$5:$C$5000,"<>P3")', "COUNTIFS", "#,##0"),
        ("B2 orders needing seller contact (P1+P2)", '=COUNTIFS(Backlog_Worklist!$D$5:$D$5000,"B2*",Backlog_Worklist!$C$5:$C$5000,"<>P3")', "COUNTIFS", "#,##0"),
        ("B2 distinct seller batches (P1+P2)", '=COUNTIFS(Backlog_Worklist!$D$5:$D$5000,"B2*",Backlog_Worklist!$C$5:$C$5000,"<>P3",Backlog_Worklist!$M$5:$M$5000,1)', "COUNTIFS on 'first in seller batch' flag", "#,##0"),
        ("P3 orders auto-closed by rule", '=COUNTIFS(Backlog_Worklist!$C$5:$C$5000,"P3")', "COUNTIFS", "#,##0"),
        ("C. Output", None, None, None),
        ("Agent hours: B1 traces", "=B12*B6/60", "orders x minutes", "#,##0.0"),
        ("Agent hours: B2 seller batches", "=(B14*B7+B13*B8)/60", "batches x minutes + orders x minutes", "#,##0.0"),
        ("Agent hours: P3 QA", "=B15*B9/60", "", "#,##0.0"),
        ("Total agent hours to clear backlog", "=SUM(B17:B19)", "", "#,##0.0"),
        ("Team capacity per day (hours)", "=B4*B5", "", "#,##0.0"),
        ("Working days to clear backlog", "=ROUNDUP(B20/B21,0)", "Target: <= 10 working days", "0"),
        ("Share of backlog closed with zero agent touch", "=B15/COUNTA(Backlog_Worklist!$B$5:$B$5000)", "", "0.0%"),
        ("D. Steady state after the ageing rule", None, None, None),
        ("Avg new stuck orders per month (history)", "=COUNTA(Backlog_Worklist!$B$5:$B$5000)/20", "1,729 orders over 20 months", "#,##0.0"),
        ("Agent hours per month to keep backlog at zero", "=B25*(1-B23)*(B6/60)", "conservative: priced at trace time", "#,##0.0"),
        ("FTE needed for steady state", "=B26/(B5*21)", "21 working days / month", "0.00"),
        ("E. Seller account-manager coverage (Problem 4)", None, None, None),
        ("Q1 'Fix now' sellers", '=COUNTIFS(Seller_Risk!$D$13:$D$2000,"Q1*")', "COUNTIFS on Seller_Risk", "#,##0"),
        ("Sellers one account manager can actively manage", 12, "Assumption: weekly 30-min call + follow-up", "0"),
        ("Account managers needed", "=ROUNDUP(B29/B30,0)", "", "0"),
        ("Share of all late handoffs covered by Q1", "=Seller_Risk!F5", "link", "0.0%"),
    ]
    for i, (lab, val, note, fmt) in enumerate(rows):
        r = 2 + i + 1
        a = cm.cell(row=r, column=1, value=lab)
        if val is None:
            a.font = font(bold=True, size=11, color=HEADER_GREEN)
            continue
        a.font = font()
        b = cm.cell(row=r, column=2)
        if isinstance(val, str) and val.startswith("="):
            b.value = val; b.font = font(bold=True) if lab.startswith(("Total", "Working", "Account", "FTE")) else font()
            if "!" in val and val.count("!") == 1 and val.startswith("=Seller_Risk"):
                b.font = font(color="008000")
            b.number_format = fmt; b.border = BOX
        else:
            inp(b, val, note, fmt)
        cm.cell(row=r, column=3, value=note).font = font(size=9, italic=True, color=GREY)
    for r in (22, 31):
        cm[f"B{r}"].fill = PatternFill("solid", fgColor=OUTPUT_FILL)

    # ================= WhatIf_Handoff =================
    wf = wb.create_sheet("WhatIf_Handoff")
    title(wf, "Problem 3 - What if sellers stopped missing the carrier cut-off?",
          "Model: logistic regression in notebooks/01 (odds ratio 5.2). The table below is the model output; 'Your scenario' interpolates for any input.")
    wf.column_dimensions["A"].width = 50
    for col in "BCDEF":
        wf.column_dimensions[col].width = 16
    lines = [
        ("Baseline late-delivery rate (model)", base["baseline_late_rate_pct"] / 100, "0.00%", "From notebook 01"),
        ("1-2 star gap: late vs on-time orders", base["bad_review_gap_pp"] / 100, "0.0%", "54.1% vs 9.2% observed"),
        ("Delivered orders per month (avg)", base["orders_in_model"] / base["months"], "#,##0", "94k orders / 20 months"),
    ]
    for i, (lab, v, fmt, note) in enumerate(lines):
        r = 4 + i
        wf.cell(row=r, column=1, value=lab).font = font()
        c = wf.cell(row=r, column=2, value=round(float(v), 6)); c.number_format = fmt; c.font = font(color="0000FF"); c.border = BOX
        c.comment = Comment(note, "Analyst")
    header(wf, 8, 1, ["Reduction in late handoffs", "Late orders avoided (20 mo)", "New late rate", "Late orders avoided / month", "1-2 star reviews avoided / month"])
    for i, r_ in whatif.iterrows():
        r = 9 + i
        wf.cell(row=r, column=1, value=float(r_.handoff_reduction)).number_format = "0%"
        wf.cell(row=r, column=2, value=round(float(r_.late_orders_avoided), 1)).number_format = "#,##0"
        wf.cell(row=r, column=3, value=round(float(r_.late_rate_new_pct) / 100, 6)).number_format = "0.00%"
        wf.cell(row=r, column=4, value=round(float(r_.late_orders_avoided_per_month), 2)).number_format = "#,##0.0"
        wf.cell(row=r, column=5, value=f"=D{r}*$B$5").number_format = "#,##0.0"
        for cc in range(1, 6):
            wf.cell(row=r, column=cc).border = BOX; wf.cell(row=r, column=cc).font = font()
    wl = 9 + len(whatif) - 1
    wf.cell(row=wl + 2, column=1, value="Your scenario").font = font(bold=True, size=11, color=HEADER_GREEN)
    wf.cell(row=wl + 3, column=1, value="Target reduction in late handoffs").font = font()
    inp(wf.cell(row=wl + 3, column=2), 0.4, "Enter 0%-100%. Effect is ~linear in the model, so we interpolate.", "0%")
    r = wl + 4
    wf.cell(row=r, column=1, value="Late orders avoided per month").font = font()
    wf.cell(row=r, column=2, value=f"=B{wl+3}*$D${wl}").number_format = "#,##0.0"
    wf.cell(row=r + 1, column=1, value="New late-delivery rate").font = font()
    wf.cell(row=r + 1, column=2, value=f"=$B$4-B{wl+3}*($B$4-$C${wl})").number_format = "0.00%"
    wf.cell(row=r + 2, column=1, value="1-2 star reviews avoided per month").font = font()
    wf.cell(row=r + 2, column=2, value=f"=B{r}*$B$5").number_format = "#,##0.0"
    wf.cell(row=r + 3, column=1, value="Relative reduction in late rate").font = font()
    wf.cell(row=r + 3, column=2, value=f"=1-B{r+1}/$B$4").number_format = "0.0%"
    for rr in range(r, r + 4):
        wf.cell(row=rr, column=2).font = font(bold=True); wf.cell(row=rr, column=2).border = BOX
        wf.cell(row=rr, column=2).fill = PatternFill("solid", fgColor=OUTPUT_FILL)
    wf.cell(row=r + 5, column=1, value="Reading: even a 100% fix of seller handoffs removes only ~20% of late orders. "
                                       "The other ~73% are handed over on time and are lost in carrier transit or "
                                       "promise-setting, so the plan needs a carrier lever too.").font = font(italic=True, color=GREY, size=9)
    wf.cell(row=r + 5, column=1).alignment = Alignment(wrap_text=True)
    wf.merge_cells(start_row=r + 5, start_column=1, end_row=r + 5, end_column=5)
    wf.row_dimensions[r + 5].height = 42

    # ================= Cover =================
    cv = wb.create_sheet("Cover", 0)
    title(cv, "Olist Marketplace - Operations & Growth Case Study",
          "Excel deliverable of the project. SQL builds the data, Python models it, Excel lets the ops team run it.")
    cv.column_dimensions["A"].width = 24; cv.column_dimensions["B"].width = 100
    guide = [
        ("Sheet", "What it answers"),
        ("Dashboard", "Headline KPIs, month drill-down (pick a month in C12), trend charts"),
        ("Monthly_KPIs", "Monthly operating table from SQL, plus formula-derived AOV, lost-order rate, freight %, MoM growth"),
        ("Recon_Checks", "Problem 1 - 9 reconciliation checks: orders failing, money at stake, root cause, control, owner"),
        ("Backlog_Worklist", "Problem 2 - 1,729 stuck orders prioritised P1/P2/P3 with recommended action; ops updates the status column"),
        ("Capacity_Model", "Problems 2 & 4 - agent hours / days to clear the backlog, steady-state FTE, account managers needed"),
        ("Seller_Risk", "Problem 4 - risk-scored sellers, quadrant summary (COUNTIFS/SUMIFS)"),
        ("WhatIf_Handoff", "Problem 3 - what a reduction in late seller handoffs is worth"),
    ]
    for i, (a, b) in enumerate(guide):
        r = 4 + i
        ca, cb = cv.cell(row=r, column=1, value=a), cv.cell(row=r, column=2, value=b)
        for c in (ca, cb):
            c.border = BOX
            c.font = font(bold=(i == 0), color="FFFFFF" if i == 0 else "000000")
            if i == 0:
                c.fill = HDR_FILL
    cv["A14"] = "Colour legend"; cv["A14"].font = font(bold=True, color=HEADER_GREEN, size=11)
    inp(cv["A15"], "1,234"); cv["B15"] = "Input / assumption: change it and the model recalculates"
    cv["A16"] = "=1+1"; cv["A16"].font = font(); cv["B16"] = "Black text: formula"
    cv["A17"] = "Link"; cv["A17"].font = font(color="008000"); cv["B17"] = "Green text: formula linking to another sheet"
    cv["A19"] = "Data source"; cv["A19"].font = font(bold=True, color=HEADER_GREEN, size=11)
    cv["B19"] = "Olist, Brazilian E-Commerce Public Dataset (CC BY-NC-SA 4.0): https://github.com/olist/work-at-olist-data"
    for r in range(15, 20):
        cv[f"B{r}"].font = font()

    for ws in wb.worksheets:
        ws.sheet_properties.tabColor = {"Cover": HEADER_GREEN, "Dashboard": "ED7D31"}.get(ws.title, "A9D08E")
    # print setup for screenshots / PDF export
    for ws, area in [(cv, "A1:B20"), (db, "A1:J41"), (cm, "A1:C33"), (wf, f"A1:E{r+5}"),
                     (rc, "A1:I16"), (sr, "A1:N30"), (bl, "A1:P30"), (mk, f"A1:P{last}")]:
        ws.print_area = area
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True

    wb.calculation.fullCalcOnLoad = True  # Excel recalculates every formula on open
    OUT.parent.mkdir(exist_ok=True)
    wb.save(OUT)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
