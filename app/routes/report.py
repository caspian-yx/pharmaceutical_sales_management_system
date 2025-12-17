from flask import Blueprint, render_template, request
from app import db
from app.models import Inbound, InboundDetail, Outbound, OutboundDetail, Stock, Material, Supplier, Warehouse
from datetime import datetime, timedelta

report_bp = Blueprint("report", __name__)

# 入库统计报表
@report_bp.route("/inbound")
def inbound_report():
    # 按日期范围查询（默认近30天）
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # 转换日期格式
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 查询该时间段内已审核的入库单
    inbounds = Inbound.query.filter(Inbound.inbound_date.between(start, end), Inbound.audit_status == 1).all()
    # 统计数据：按供应商分组
    supplier_stats = {}
    for inbound in inbounds:
        supplier = Supplier.query.get(inbound.supplier_id)
        details = InboundDetail.query.filter_by(purchase_id=inbound.purchase_id).all()  # 修正：使用purchase_id
        total_amount = sum(d.quantity * d.unit_price for d in details)
        if supplier.id not in supplier_stats:  # 修正：使用id
            supplier_stats[supplier.id] = {
                "name": supplier.name,  # 修正：使用name
                "count": 0,  # 入库单数
                "total_quantity": 0,  # 总入库量
                "total_amount": 0.00  # 总金额
            }
        supplier_stats[supplier.id]["count"] += 1
        supplier_stats[supplier.id]["total_quantity"] += sum(d.quantity for d in details)
        supplier_stats[supplier.id]["total_amount"] += total_amount

    return render_template("report_inbound.html", supplier_stats=supplier_stats.values(), start_date=start_date, end_date=end_date)

# 库存汇总报表
@report_bp.route("/stock_summary")
def stock_summary():
    # 按仓库汇总库存
    warehouses = Warehouse.query.all()
    stock_summary = []
    for warehouse in warehouses:
        stocks = Stock.query.filter_by(warehouse_id=warehouse.id).join(Material).all()
        total_value = sum(s.current_stock * (InboundDetail.query.filter_by(medicine_id=s.medicine_id).first().unit_price if InboundDetail.query.filter_by(medicine_id=s.medicine_id).first() else 0) for s in stocks)  # 修正：使用medicine_id
        stock_summary.append({
            "name": warehouse.name,
            "material_count": len(stocks),  # 物资种类数
            "total_stock": sum(s.current_stock for s in stocks),  # 总库存数量
            "total_value": round(total_value, 2)  # 库存总价值
        })

    return render_template("report_stock.html", stock_summary=stock_summary)