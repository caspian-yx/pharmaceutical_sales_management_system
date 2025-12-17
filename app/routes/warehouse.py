from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import Warehouse  # 仓库模型

# 仓库模块蓝图，路由前缀：/warehouse
warehouse_bp = Blueprint('warehouse', __name__, url_prefix='/warehouse')

# 1. 仓库列表页（支持搜索）
@warehouse_bp.route('/list')
def warehouse_list():
    keyword = request.args.get('keyword', '').strip()
    query = Warehouse.query
    if keyword:
        # 支持搜索：名称、位置、负责人
        query = query.filter(
            db.or_(
                Warehouse.name.like(f'%{keyword}%'),
                Warehouse.location.like(f'%{keyword}%'),
                Warehouse.manager.like(f'%{keyword}%')
            )
        )
    warehouses = query.all()
    return render_template('warehouse_list.html', warehouses=warehouses, keyword=keyword)

# 2. 新增仓库（保持原逻辑）
@warehouse_bp.route('/add', methods=['GET', 'POST'])
def warehouse_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        manager = request.form.get('manager', '').strip()
        phone = request.form.get('phone', '').strip()

        # 保留表单数据
        form_data = {
            'name': name,
            'location': location,
            'manager': manager,
            'phone': phone
        }

        if not name:
            flash('仓库名称不能为空', 'error')
            return render_template('warehouse_add.html', form_data=form_data)

        if not location:
            flash('仓库位置不能为空', 'error')
            return render_template('warehouse_add.html', form_data=form_data)

        new_warehouse = Warehouse(
            name=name,
            location=location,
            manager=manager,
            phone=phone,
            is_active=1  # 默认为启用
        )

        try:
            db.session.add(new_warehouse)
            db.session.commit()
            flash('新增成功', 'success')
            return redirect(url_for('warehouse.warehouse_list'))
        except IntegrityError:
            db.session.rollback()
            flash('仓库名称或位置已存在，请勿重复添加', 'error')
            return render_template('warehouse_add.html', form_data=form_data)

    return render_template('warehouse_add.html', form_data={})

# 3. 编辑仓库（保持原逻辑）
@warehouse_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def warehouse_edit(id):
    warehouse = Warehouse.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()

        if not name:
            flash('仓库名称不能为空', 'error')
            return render_template('warehouse_edit.html', warehouse=warehouse)

        if not location:
            flash('仓库位置不能为空', 'error')
            return render_template('warehouse_edit.html', warehouse=warehouse)

        warehouse.name = name
        warehouse.location = location
        warehouse.manager = request.form.get('manager', '').strip()
        warehouse.phone = request.form.get('phone', '').strip()
        warehouse.is_active = 1 if request.form.get('is_active') else 0  # 启用状态

        try:
            db.session.commit()
            flash('编辑成功', 'success')
            return redirect(url_for('warehouse.warehouse_list'))
        except IntegrityError:
            db.session.rollback()
            flash('仓库名称或位置已存在，请勿重复', 'error')
            return render_template('warehouse_edit.html', warehouse=warehouse)

    return render_template('warehouse_edit.html', warehouse=warehouse)

# 4. 删除仓库（保持原逻辑）
@warehouse_bp.route('/delete/<int:id>')
def warehouse_delete(id):
    warehouse = Warehouse.query.get_or_404(id)
    db.session.delete(warehouse)
    db.session.commit()
    flash('删除成功', 'success')
    return redirect(url_for('warehouse.warehouse_list'))