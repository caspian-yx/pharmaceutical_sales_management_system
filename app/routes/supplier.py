from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Supplier
from sqlalchemy.exc import IntegrityError

supplier_bp = Blueprint('supplier', __name__, url_prefix='/supplier')

# 1. 供应商列表页（支持搜索）
@supplier_bp.route('/list')
def supplier_list():
    keyword = request.args.get('keyword', '').strip()
    query = Supplier.query
    if keyword:
        # 支持搜索：名称、联系人、电话
        query = query.filter(
            db.or_(
                Supplier.name.like(f'%{keyword}%'),
                Supplier.contact.like(f'%{keyword}%'),
                Supplier.phone.like(f'%{keyword}%')
            )
        )
    suppliers = query.all()
    return render_template('supplier_list.html', suppliers=suppliers, keyword=keyword)

# 2. 新增供应商
@supplier_bp.route('/add', methods=['GET', 'POST'])
def supplier_add():
    if request.method == 'POST':
        name = request.form.get('name')
        license_number = request.form.get('license_number')
        contact = request.form.get('contact')
        phone = request.form.get('phone')
        address = request.form.get('address')

        if not name:
            flash('供应商名称不能为空', 'error')
            return render_template('supplier_add.html')

        new_supplier = Supplier(
            name=name,
            license_number=license_number,
            contact=contact,
            phone=phone,
            address=address
        )
        db.session.add(new_supplier)
        try:
            db.session.commit()
            flash('新增成功', 'success')
            return redirect(url_for('supplier.supplier_list'))
        except IntegrityError:
            db.session.rollback()
            flash('供应商名称或经营许可证号已存在，请勿重复添加', 'error')
            return render_template('supplier_add.html')

    return render_template('supplier_add.html')

# 3. 编辑供应商（保持原逻辑）
@supplier_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def supplier_edit(id):
    sup = Supplier.query.get_or_404(id)
    if request.method == 'POST':
        sup.name = request.form.get('name')
        sup.license_number = request.form.get('license_number')
        sup.contact = request.form.get('contact')
        sup.phone = request.form.get('phone')
        sup.address = request.form.get('address')
        try:
            db.session.commit()
            flash('编辑成功', 'success')
            return redirect(url_for('supplier.supplier_list'))
        except IntegrityError:
            db.session.rollback()
            flash('供应商名称或经营许可证号已存在，请勿重复', 'error')
            return render_template('supplier_edit.html', supplier=sup)

    return render_template('supplier_edit.html', supplier=sup)

# 4. 删除供应商
@supplier_bp.route('/delete/<int:id>')
def supplier_delete(id):
    sup = Supplier.query.get_or_404(id)
    db.session.delete(sup)
    db.session.commit()
    flash('删除成功', 'success')
    return redirect(url_for('supplier.supplier_list'))