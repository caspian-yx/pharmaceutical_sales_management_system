from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Outbound, OutboundDetail, Warehouse, Material
from datetime import datetime

# 预设部门列表
DEPARTMENTS = ['采购部', '销售部', '财务部', '技术部', '仓储部', '人事部', '行政部', '市场部']
outbound_bp = Blueprint('outbound', __name__, url_prefix='/outbound')

# 出库单列表（带搜索）
@outbound_bp.route('/list')
def outbound_list():
    keyword = request.args.get('keyword', '').strip()
    query = Outbound.query.join(Warehouse)  # 关联仓库表
    if keyword:
        query = query.filter(
            db.or_(
                Outbound.outbound_id.like(f'%{keyword}%'),  # 按出库单号搜索
                Outbound.dept_name.like(f'%{keyword}%'),     # 按部门搜索
                Warehouse.name.like(f'%{keyword}%') # 按仓库名称搜索
            )
        )
    outbounds = query.order_by(Outbound.outbound_date.desc()).all()  # 按日期倒序
    return render_template('outbound_list.html', outbounds=outbounds, keyword=keyword)

# 新增出库单（自动填充日期+物资下拉框）
@outbound_bp.route('/add', methods=['GET', 'POST'])
def outbound_add():
    # 查询所有需要的下拉框数据
    warehouses = Warehouse.query.all()  # 仓库列表
    materials = Material.query.all()    # 物资列表（关键：确保物资下拉框有数据）
    
    if request.method == 'POST':
        # 生成唯一出库单号（格式：OUT+时间戳）
        outbound_id = f"OUT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 处理出库日期：优先用前端传递的值，若为空则用当前日期（双重保障）
        outbound_date = request.form.get('outbound_date') or datetime.now().strftime('%Y-%m-%d')
        
        # 创建出库单主记录
        new_outbound = Outbound(
            outbound_id=outbound_id,
            warehouse_id=request.form.get('warehouse_id'),
            dept_name=request.form.get('dept_name'),
            outbound_date=outbound_date,  # 确保日期非空
            remark=request.form.get('remark'),
            audit_status=0  # 默认为未审核
        )
        db.session.add(new_outbound)
        db.session.commit()
        
        # 添加明细（简化：直接从表单获取并添加，实际可跳转编辑页）
        material_id = request.form.get('material_id')
        quantity = request.form.get('quantity')
        if material_id and quantity:
            # 获取药品信息以获取零售价
            medicine = Material.query.get(material_id)
            if medicine:
                detail = OutboundDetail(
                    sale_id=outbound_id,  # 修正：使用sale_id
                    medicine_id=material_id,  # 修正：使用medicine_id
                    quantity=int(quantity),
                    unit_price=medicine.retail_price,  # 使用药品的零售价
                    amount=int(quantity) * medicine.retail_price  # 计算金额
                )
                db.session.add(detail)
                db.session.commit()
        
        flash('出库单创建成功', 'success')
        # 跳转到编辑页（使用outbound_id作为参数，与路由匹配）
        return redirect(url_for('outbound.outbound_edit', outbound_id=new_outbound.outbound_id))
    
    # 传递数据到模板
    return render_template(
        'outbound_add.html',
        warehouses=warehouses,
        departments=DEPARTMENTS,
        materials=materials  # 关键：传递物资列表，确保下拉框有数据
    )

# 编辑出库单（含明细）
@outbound_bp.route('/edit/<string:outbound_id>', methods=['GET', 'POST'])
def outbound_edit(outbound_id):
    outbound = Outbound.query.get_or_404(outbound_id)  # 用outbound_id查询
    materials = Material.query.all()  # 物资列表
    details = OutboundDetail.query.filter_by(sale_id=outbound_id).all()  # 修正：使用sale_id

    if request.method == 'POST':
        # 保存旧的审核状态和明细（用于库存回退）
        old_audit_status = outbound.audit_status
        old_details = OutboundDetail.query.filter_by(sale_id=outbound_id).all()

        # 如果之前是已审核状态，先回退旧明细的库存
        if old_audit_status == 1:
            for old_detail in old_details:
                mat = Material.query.get(old_detail.medicine_id)
                if mat:
                    mat.stock += old_detail.quantity

        # 更新出库单主信息
        outbound.warehouse_id = request.form.get('warehouse_id')
        outbound.dept_name = request.form.get('dept_name')
        outbound.outbound_date = request.form.get('outbound_date') or datetime.now().strftime('%Y-%m-%d')
        outbound.remark = request.form.get('remark')
        new_audit_status = int(request.form.get('audit_status', 0))
        outbound.audit_status = new_audit_status

        # 先删除旧明细
        OutboundDetail.query.filter_by(sale_id=outbound_id).delete()  # 修正：使用sale_id

        # 支持两种方式：1. 选择现有药品ID  2. 输入药品名称+规格
        material_ids = request.form.getlist('material_id[]')
        material_names = request.form.getlist('material_name[]')
        material_specs = request.form.getlist('material_specification[]')
        quantities = request.form.getlist('quantity[]')

        # 如果新状态是已审核，先检查库存是否充足
        if new_audit_status == 1:
            for i, qty in enumerate(quantities):
                if not qty:
                    continue

                qty = int(qty)

                # 优先使用material_id，如果没有则使用name+specification查找
                mat_id = material_ids[i] if i < len(material_ids) and material_ids[i] else None

                if mat_id:
                    mat = Material.query.get(mat_id)
                else:
                    # 使用药品名称+规格查找
                    mat_name = material_names[i] if i < len(material_names) else None
                    mat_spec = material_specs[i] if i < len(material_specs) else None

                    if not mat_name or not mat_spec:
                        continue

                    mat = Material.query.filter_by(name=mat_name, specification=mat_spec).first()

                if not mat:
                    db.session.rollback()
                    flash(f'药品不存在', 'error')
                    return redirect(url_for('outbound.outbound_edit', outbound_id=outbound_id))

                # 关键：检查库存是否充足
                if mat.stock < qty:
                    db.session.rollback()
                    flash(f'药品【{mat.name} {mat.specification}】库存不足！当前库存：{mat.stock}，需要：{qty}', 'error')
                    return redirect(url_for('outbound.outbound_edit', outbound_id=outbound_id))

        # 添加新明细
        for i, qty in enumerate(quantities):
            if not qty:
                continue

            qty = int(qty)

            # 优先使用material_id，如果没有则使用name+specification查找
            mat_id = material_ids[i] if i < len(material_ids) and material_ids[i] else None

            if mat_id:
                mat = Material.query.get(mat_id)
            else:
                # 使用药品名称+规格查找
                mat_name = material_names[i] if i < len(material_names) else None
                mat_spec = material_specs[i] if i < len(material_specs) else None

                if not mat_name or not mat_spec:
                    continue

                mat = Material.query.filter_by(name=mat_name, specification=mat_spec).first()

            if not mat:
                continue

            # 添加新明细
            detail = OutboundDetail(
                sale_id=outbound_id,  # 修正：使用sale_id
                medicine_id=mat.id,  # 修正：使用medicine_id
                quantity=qty,
                unit_price=mat.retail_price,  # 使用药品的零售价
                amount=qty * mat.retail_price  # 计算金额
            )
            db.session.add(detail)

            # 如果新状态是已审核，则扣减库存
            if new_audit_status == 1:
                mat.stock -= qty

        db.session.commit()
        flash('出库单更新成功', 'success')
        return redirect(url_for('outbound.outbound_list'))

    return render_template(
        'outbound_edit.html',
        outbound=outbound,
        materials=materials,
        details=details,
        warehouses=Warehouse.query.all(),
        departments=DEPARTMENTS
    )


# 查看出库单详情（只读）
@outbound_bp.route('/detail/<string:outbound_id>')
def outbound_detail(outbound_id):
    outbound = Outbound.query.get_or_404(outbound_id)
    details = OutboundDetail.query.filter_by(sale_id=outbound_id).all()
    return render_template('outbound_detail.html', outbound=outbound, details=details)

# 删除出库单
@outbound_bp.route('/delete/<string:outbound_id>')
def outbound_delete(outbound_id):
    try:
        outbound = Outbound.query.get_or_404(outbound_id)

        # 如果出库单已审核通过（状态=1），需要先回退库存（增加）
        if outbound.audit_status == 1:
            details = OutboundDetail.query.filter_by(sale_id=outbound_id).all()
            for detail in details:
                mat = Material.query.get(detail.medicine_id)
                if mat:
                    mat.stock += detail.quantity

        # 先删除关联的明细
        OutboundDetail.query.filter_by(sale_id=outbound_id).delete()
        # 再删除主单
        db.session.delete(outbound)
        db.session.commit()
        flash('出库单已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'error')
    return redirect(url_for('outbound.outbound_list'))