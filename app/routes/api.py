from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import (
    Material, Supplier, Warehouse,
    Inbound, InboundDetail, Outbound, OutboundDetail
)

api_bp = Blueprint("api", __name__, url_prefix="/api")

# -------------------------- 物资管理接口 --------------------------
@api_bp.route("/materials", methods=["GET"])
def get_materials():
    """查询物资（支持名称筛选）"""
    name = request.args.get("name", "")
    query = Material.query
    if name:
        query = query.filter(material.name.like(f"%{name}%"))
    materials = query.all()
    return jsonify([{
        "material_id": m.material_id,
        "name": m.name,
        "category": m.category,
        "unit": m.unit,
        "stock": m.stock
    } for m in materials])

@api_bp.route("/materials", methods=["POST"])
def add_material():
    """添加物资"""
    data = request.json
    new_mat = Material(
        name=data["name"],
        category=data["category"],
        unit=data["unit"],
        stock=int(data["stock"])
    )
    db.session.add(new_mat)
    db.session.commit()
    return jsonify({"status": "success"})

@api_bp.route("/materials/<int:id>", methods=["PUT"])
def edit_material(id):
    """编辑物资"""
    mat = Material.query.get_or_404(id)
    data = request.json
    mat.name = data["name"]
    mat.category = data["category"]
    mat.unit = data["unit"]
    mat.stock = int(data["stock"])
    db.session.commit()
    return jsonify({"status": "success"})

@api_bp.route("/materials/<int:id>", methods=["DELETE"])
def delete_material(id):
    """删除物资"""
    mat = Material.query.get_or_404(id)
    db.session.delete(mat)
    db.session.commit()
    return jsonify({"status": "success"})

# -------------------------- 供应商管理接口 --------------------------
@api_bp.route("/suppliers", methods=["GET"])
def get_suppliers():
    """查询供应商"""
    name = request.args.get("supplier_name", "")
    query = Supplier.query
    if name:
        query = query.filter(Supplier.supplier_name.like(f"%{name}%"))
    suppliers = query.all()
    return jsonify([{
        "supplier_id": s.supplier_id,
        "supplier_name": s.supplier_name,
        "contact_person": s.contact_person,
        "phone": s.phone,
        "is_valid": "有效" if s.is_valid else "无效"
    } for s in suppliers])

@api_bp.route("/suppliers", methods=["POST"])
def add_supplier():
    """添加供应商"""
    data = request.json
    new_sup = Supplier(
        supplier_name=data["name"],
        contact_person=data["contact"],
        phone=data["phone"],
        is_valid=data["is_valid"]
    )
    db.session.add(new_sup)
    db.session.commit()
    return jsonify({"status": "success"})

@api_bp.route("/suppliers/<int:id>", methods=["PUT"])
def edit_supplier(id):
    """编辑供应商"""
    sup = Supplier.query.get_or_404(id)
    data = request.json
    sup.supplier_name = data["name"]
    sup.contact_person = data["contact"]
    sup.phone = data["phone"]
    sup.is_valid = data["is_valid"]
    db.session.commit()
    return jsonify({"status": "success"})

@api_bp.route("/suppliers/<int:id>", methods=["DELETE"])
def delete_supplier(id):
    """删除供应商"""
    sup = Supplier.query.get_or_404(id)
    db.session.delete(sup)
    db.session.commit()
    return jsonify({"status": "success"})

# -------------------------- 仓库管理接口 --------------------------
@api_bp.route("/warehouses", methods=["GET"])
def get_warehouses():
    """查询仓库"""
    warehouses = Warehouse.query.all()
    return jsonify([{
        "warehouse_id": w.warehouse_id,
        "name": w.name,
        "location": w.location
    } for w in warehouses])

@api_bp.route("/warehouses", methods=["POST"])
def add_warehouse():
    """添加仓库"""
    data = request.json
    new_wh = Warehouse(
        name=data["name"],
        location=data["location"]
    )
    db.session.add(new_wh)
    db.session.commit()
    return jsonify({"status": "success"})

@api_bp.route("/warehouses/<int:id>", methods=["PUT"])
def edit_warehouse(id):
    """编辑仓库"""
    wh = Warehouse.query.get_or_404(id)
    data = request.json
    wh.name = data["name"]
    wh.location = data["location"]
    db.session.commit()
    return jsonify({"status": "success"})

@api_bp.route("/warehouses/<int:id>", methods=["DELETE"])
def delete_warehouse(id):
    """删除仓库"""
    wh = Warehouse.query.get_or_404(id)
    db.session.delete(wh)
    db.session.commit()
    return jsonify({"status": "success"})

# -------------------------- 入库管理接口 --------------------------
@api_bp.route("/inbounds", methods=["GET"])
def get_inbounds():
    """查询入库单"""
    inbound_id = request.args.get("inbound_id", "")
    supplier_id = request.args.get("supplier_id", "")
    audit_status = request.args.get("audit_status", "")
    
    query = Inbound.query
    if inbound_id:
        query = query.filter(Inbound.inbound_id.like(f"%{inbound_id}%"))
    if supplier_id:
        query = query.filter(Inbound.supplier_id == supplier_id)
    if audit_status:
        query = query.filter(Inbound.audit_status == int(audit_status))
    
    inbounds = query.order_by(Inbound.inbound_date.desc()).all()
    return jsonify([{
        "inbound_id": i.inbound_id,
        "supplier_name": i.supplier.supplier_name if i.supplier else "",
        "name": i.warehouse.name if i.warehouse else "",
        "inbound_date": i.inbound_date.strftime("%Y-%m-%d"),
        "audit_status": ["未审核", "已通过", "已驳回"][i.audit_status],
        "remark": i.remark or ""
    } for i in inbounds])

@api_bp.route("/inbounds", methods=["POST"])
def add_inbound():
    """添加入库单（主表+明细）"""
    data = request.json
    # 生成单号：IN+20251114+001（日期+3位序号）
    today = datetime.now().strftime("%Y%m%d")
    last_inbound = Inbound.query.filter(Inbound.inbound_id.like(f"IN{today}%")).order_by(Inbound.inbound_id.desc()).first()
    seq = "001" if not last_inbound else f"{int(last_inbound.inbound_id[-3:])+1:03d}"
    inbound_id = f"IN{today}{seq}"
    
    # 添加主表
    new_inbound = Inbound(
        inbound_id=inbound_id,
        supplier_id=data["supplier_id"],
        warehouse_id=data["warehouse_id"],
        inbound_date=datetime.strptime(data["date"], "%Y-%m-%d"),
        remark=data["remark"]
    )
    db.session.add(new_inbound)
    
    # 添加明细+更新库存
    for item in data["details"]:
        detail = InboundDetail(
            purchase_id=inbound_id,  # 修正：使用purchase_id
            medicine_id=item["material_id"],  # 修正：使用medicine_id（参数名保持material_id以兼容API）
            quantity=int(item["quantity"]),
            unit_price=float(item["unit_price"])
        )
        db.session.add(detail)
        # 增加库存
        mat = Material.query.get(item["material_id"])
        mat.stock += int(item["quantity"])
    
    db.session.commit()
    return jsonify({"status": "success"})

@api_bp.route("/inbounds/<string:id>", methods=["PUT"])
def edit_inbound(id):
    """编辑入库单（含审核状态）"""
    inbound = Inbound.query.get_or_404(id)
    data = request.json
    
    # 更新主表
    inbound.supplier_id = data["supplier_id"]
    inbound.warehouse_id = data["warehouse_id"]
    inbound.inbound_date = datetime.strptime(data["date"], "%Y-%m-%d")
    inbound.remark = data["remark"]
    inbound.audit_status = int(data["audit_status"])
    inbound.auditor_id = 1  # 默认管理员审核
    inbound.audit_time = datetime.now()
    
    db.session.commit()
    return jsonify({"status": "success"})

@api_bp.route("/inbounds/<string:id>", methods=["DELETE"])
def delete_inbound(id):
    """删除入库单（先删明细，再删主表）"""
    # 删除明细
    details = InboundDetail.query.filter_by(purchase_id=id).all()  # 修正：使用purchase_id
    for d in details:
        # 减少库存
        mat = Material.query.get(d.medicine_id)  # 修正：使用medicine_id
        mat.stock -= d.quantity
        db.session.delete(d)
    # 删除主表
    inbound = Inbound.query.get_or_404(id)
    db.session.delete(inbound)
    db.session.commit()
    return jsonify({"status": "success"})

# -------------------------- 出库管理接口（逻辑类似入库） --------------------------
@api_bp.route("/outbounds", methods=["GET"])
def get_outbounds():
    """查询出库单"""
    outbound_id = request.args.get("outbound_id", "")
    dept_name = request.args.get("dept_name", "")
    audit_status = request.args.get("audit_status", "")
    
    query = Outbound.query
    if outbound_id:
        query = query.filter(Outbound.outbound_id.like(f"%{outbound_id}%"))
    if dept_name:
        query = query.filter(Outbound.dept_name.like(f"%{dept_name}%"))
    if audit_status:
        query = query.filter(Outbound.audit_status == int(audit_status))
    
    outbounds = query.order_by(Outbound.outbound_date.desc()).all()
    return jsonify([{
        "outbound_id": o.outbound_id,
        "dept_name": o.dept_name,
        "name": o.warehouse.name if o.warehouse else "",
        "outbound_date": o.outbound_date.strftime("%Y-%m-%d"),
        "audit_status": ["未审核", "已通过", "已驳回"][o.audit_status],
        "remark": o.remark or ""
    } for o in outbounds])

@api_bp.route("/outbounds", methods=["POST"])
def add_outbound():
    """添加出库单"""
    data = request.json
    # 生成单号：OUT+20251114+001
    today = datetime.now().strftime("%Y%m%d")
    last_outbound = Outbound.query.filter(Outbound.outbound_id.like(f"OUT{today}%")).order_by(Outbound.outbound_id.desc()).first()
    seq = "001" if not last_outbound else f"{int(last_outbound.outbound_id[-3:])+1:03d}"
    outbound_id = f"OUT{today}{seq}"
    
    # 添加主表
    new_outbound = Outbound(
        outbound_id=outbound_id,
        dept_name=data["dept_name"],
        warehouse_id=data["warehouse_id"],
        outbound_date=datetime.strptime(data["date"], "%Y-%m-%d"),
        remark=data["remark"]
    )
    db.session.add(new_outbound)
    
    # 添加明细+更新库存
    for item in data["details"]:
        detail = OutboundDetail(
            sale_id=outbound_id,  # 修正：使用sale_id
            medicine_id=item["material_id"],  # 修正：使用medicine_id（参数名保持material_id以兼容API）
            quantity=int(item["quantity"])
        )
        db.session.add(detail)
        # 减少库存
        mat = Material.query.get(item["material_id"])
        mat.stock -= int(item["quantity"])
    
    db.session.commit()
    return jsonify({"status": "success"})

@api_bp.route("/outbounds/<string:id>", methods=["PUT"])
def edit_outbound(id):
    """编辑出库单"""
    outbound = Outbound.query.get_or_404(id)
    data = request.json
    
    outbound.dept_name = data["dept_name"]
    outbound.warehouse_id = data["warehouse_id"]
    outbound.outbound_date = datetime.strptime(data["date"], "%Y-%m-%d")
    outbound.remark = data["remark"]
    outbound.audit_status = int(data["audit_status"])
    outbound.auditor_id = 1
    outbound.audit_time = datetime.now()
    
    db.session.commit()
    return jsonify({"status": "success"})

@api_bp.route("/outbounds/<string:id>", methods=["DELETE"])
def delete_outbound(id):
    """删除出库单"""
    # 删除明细
    details = OutboundDetail.query.filter_by(sale_id=id).all()  # 修正：使用sale_id
    for d in details:
        # 增加库存
        mat = Material.query.get(d.medicine_id)  # 修正：使用medicine_id
        mat.stock += d.quantity
        db.session.delete(d)
    # 删除主表
    outbound = Outbound.query.get_or_404(id)
    db.session.delete(outbound)
    db.session.commit()
    return jsonify({"status": "success"})