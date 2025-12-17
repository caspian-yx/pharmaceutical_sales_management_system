from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Inbound, InboundDetail, Supplier, Warehouse, Material, MaterialCategory, Unit
from datetime import datetime

inbound_bp = Blueprint('inbound', __name__, url_prefix='/inbound')


# 1. 入库单列表页（带搜索）
@inbound_bp.route('/list')
def inbound_list():
    keyword = request.args.get('keyword', '').strip()
    # 关联供应商和仓库，支持多字段搜索
    query = Inbound.query.join(Supplier).join(Warehouse)
    if keyword:
        query = query.filter(
            db.or_(
                Inbound.inbound_id.like(f'%{keyword}%'),  # 入库单号
                Supplier.name.like(f'%{keyword}%'),       # 供应商名称
                Warehouse.name.like(f'%{keyword}%')       # 仓库名称
            )
        )
    inbounds = query.order_by(Inbound.inbound_date.desc()).all()  # 按日期倒序
    return render_template('inbound_list.html', inbounds=inbounds, keyword=keyword)


# 2. 新增入库单
@inbound_bp.route('/add', methods=['GET', 'POST'])
def inbound_add():
    # 加载下拉框数据
    suppliers = Supplier.query.all()
    warehouses = Warehouse.query.all()
    materials = Material.query.all()
    # 生成当前日期（YYYY-MM-DD），用于前端默认值
    today = datetime.now().strftime('%Y-%m-%d')

    if request.method == 'GET':
        return render_template(
            'inbound_add.html',
            suppliers=suppliers,
            warehouses=warehouses,
            materials=materials,
            today=today  # 传递当前日期给模板
        )

    # POST提交处理
    else:
        # 处理入库日期（核心：确保非空且格式正确）
        inbound_date_str = request.form.get('inbound_date', '').strip()
        try:
            # 转换为date类型（匹配模型的db.Date）
            inbound_date = datetime.strptime(inbound_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            # 空值或格式错误时，用当前日期兜底
            inbound_date = datetime.now().date()

        # 创建入库单主单
        inbound_id = f"IN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_inbound = Inbound(
            inbound_id=inbound_id,
            supplier_id=request.form.get('supplier_id'),
            warehouse_id=request.form.get('warehouse_id'),
            inbound_date=inbound_date,  # 传入有效日期
            remark=request.form.get('remark'),
            audit_status=0  # 默认为未审核
        )

        # 保存主单
        try:
            db.session.add(new_inbound)
            db.session.commit()
            flash('入库单创建成功，请添加明细', 'success')
            return redirect(url_for('inbound.inbound_edit', inbound_id=inbound_id))
        except Exception as e:
            db.session.rollback()
            flash(f'创建失败：{str(e)}', 'error')
            return render_template(
                'inbound_add.html',
                suppliers=suppliers,
                warehouses=warehouses,
                materials=materials,
                today=today
            )


# 3. 编辑入库单（含明细）
@inbound_bp.route('/edit/<string:inbound_id>', methods=['GET', 'POST'])
def inbound_edit(inbound_id):
    inbound = Inbound.query.get_or_404(inbound_id)
    materials = Material.query.all()
    details = InboundDetail.query.filter_by(purchase_id=inbound_id).all()  # 修正：使用purchase_id
    today = datetime.now().strftime('%Y-%m-%d')  # 当前日期

    if request.method == 'GET':
        return render_template(
            'inbound_edit.html',
            inbound=inbound,
            materials=materials,
            details=details,
            suppliers=Supplier.query.all(),
            warehouses=Warehouse.query.all(),
            today=today
        )

    # POST提交处理
    else:
        # 处理入库日期（核心：确保有效）
        inbound_date_str = request.form.get('inbound_date', '').strip()
        try:
            inbound_date = datetime.strptime(inbound_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            # 错误时保留原日期（或用当前日期）
            inbound_date = inbound.inbound_date or datetime.now().date()

        # 保存旧的审核状态和明细（用于库存回退）
        old_audit_status = inbound.audit_status
        old_details = InboundDetail.query.filter_by(purchase_id=inbound_id).all()

        # 如果之前是已审核状态，先回退旧明细的库存
        if old_audit_status == 1:
            for old_detail in old_details:
                mat = Material.query.get(old_detail.medicine_id)
                if mat:
                    mat.stock -= old_detail.quantity

        # 更新主单信息
        inbound.supplier_id = request.form.get('supplier_id')
        inbound.warehouse_id = request.form.get('warehouse_id')
        inbound.inbound_date = inbound_date  # 传入有效日期
        inbound.remark = request.form.get('remark')
        new_audit_status = int(request.form.get('audit_status', 0))
        inbound.audit_status = new_audit_status

        # 处理明细（先删旧明细，再添新明细）
        InboundDetail.query.filter_by(purchase_id=inbound_id).delete()  # 修正：使用purchase_id

        # 支持两种方式：1. 选择现有药品ID  2. 输入药品名称+规格
        material_ids = request.form.getlist('material_id[]')
        material_names = request.form.getlist('material_name[]')
        material_specs = request.form.getlist('material_specification[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('unit_price[]')

        for i, (qty, price) in enumerate(zip(quantities, prices)):
            if not qty or not price:
                continue

            qty = int(qty)
            price = float(price)

            # 优先使用material_id，如果没有则使用name+specification查找或创建
            mat_id = material_ids[i] if i < len(material_ids) and material_ids[i] else None

            if mat_id:
                # 使用现有药品ID
                mat = Material.query.get(mat_id)
            else:
                # 使用药品名称+规格查找或创建
                mat_name = material_names[i] if i < len(material_names) else None
                mat_spec = material_specs[i] if i < len(material_specs) else None

                if not mat_name or not mat_spec:
                    continue

                # 根据名称+规格查找药品
                mat = Material.query.filter_by(name=mat_name, specification=mat_spec).first()

                # 如果不存在，自动创建新药品
                if not mat:
                    # 获取默认分类和单位（可以从表单获取，或使用默认值）
                    default_category = MaterialCategory.query.first()
                    default_unit = Unit.query.first()

                    mat = Material(
                        name=mat_name,
                        specification=mat_spec,
                        category_id=default_category.id if default_category else None,
                        unit_id=default_unit.id if default_unit else None,
                        stock=0,  # 初始库存为0
                        min_stock=0,
                        retail_price=price  # 使用采购价作为初始零售价
                    )
                    db.session.add(mat)
                    db.session.flush()  # 获取新创建药品的ID

            if not mat:
                continue

            # 添加新明细
            detail = InboundDetail(
                purchase_id=inbound_id,  # 修正：使用purchase_id
                medicine_id=mat.id,  # 修正：使用medicine_id
                quantity=qty,
                unit_price=price,
                amount=qty * price  # 计算金额
            )
            db.session.add(detail)

            # 如果新状态是已审核，则增加库存
            if new_audit_status == 1:
                mat.stock += qty

        # 保存更新
        try:
            db.session.commit()
            flash('入库单更新成功', 'success')
            return redirect(url_for('inbound.inbound_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'error')
            return render_template(
                'inbound_edit.html',
                inbound=inbound,
                materials=materials,
                details=details,
                suppliers=Supplier.query.all(),
                warehouses=Warehouse.query.all(),
                today=today
            )


# 3.5 查看入库单详情（只读）
@inbound_bp.route('/detail/<string:inbound_id>')
def inbound_detail(inbound_id):
    inbound = Inbound.query.get_or_404(inbound_id)
    details = InboundDetail.query.filter_by(purchase_id=inbound_id).all()
    return render_template('inbound_detail.html', inbound=inbound, details=details)


# 4. 删除入库单
@inbound_bp.route('/delete/<string:inbound_id>')
def inbound_delete(inbound_id):
    try:
        inbound = Inbound.query.get_or_404(inbound_id)

        # 如果入库单已审核通过（状态=1），需要先回退库存
        if inbound.audit_status == 1:
            details = InboundDetail.query.filter_by(purchase_id=inbound_id).all()
            for detail in details:
                mat = Material.query.get(detail.medicine_id)
                if mat:
                    mat.stock -= detail.quantity

        # 先删明细，再删主单
        InboundDetail.query.filter_by(purchase_id=inbound_id).delete()
        db.session.delete(inbound)
        db.session.commit()
        flash('入库单已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'error')
    return redirect(url_for('inbound.inbound_list'))