from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db  # 你的数据库实例
from app.models import Material, MaterialCategory  # 导入分类模型用于关联查询
from sqlalchemy.exc import IntegrityError, DataError  # 导入异常

# 物资模块蓝图，路由前缀：/material
material_bp = Blueprint('material', __name__, url_prefix='/material')

# 1. 物资列表页（支持多字段搜索）
@material_bp.route('/list')
def material_list():
    keyword = request.args.get('keyword', '').strip()
    query = Material.query.join(MaterialCategory, Material.category_id == MaterialCategory.id)  # 关联分类表
    if keyword:
        # 支持搜索：物资名称、规格、分类名称
        query = query.filter(
            db.or_(
                Material.name.like(f'%{keyword}%'),
                Material.specification.like(f'%{keyword}%'),
                MaterialCategory.name.like(f'%{keyword}%')
            )
        )
    materials = query.all()
    return render_template('material_list.html', materials=materials, keyword=keyword)

# 2. 新增物资页面（保持不变，仅确保表单字段正确）
@material_bp.route('/add', methods=['GET', 'POST'])
def material_add():
    from app.models import MaterialCategory, Unit  # 导入分类和单位模型
    categories = MaterialCategory.query.all()
    units = Unit.query.all()

    if request.method == 'POST':
        # 接收表单数据（注意字段名与模板一致）
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        unit_id = request.form.get('unit_id')
        stock = request.form.get('stock', 0)
        specification = request.form.get('specification')
        remark = request.form.get('remark')

        # 保存用户输入，用于出错时回显
        form_data = {
            'name': name,
            'specification': specification,
            'category_id': category_id,
            'unit_id': unit_id,
            'stock': stock,
            'remark': remark
        }

        # 验证必填字段
        if not name:
            flash('药品名称不能为空', 'error')
            return render_template('material_add.html', categories=categories, units=units, form_data=form_data)

        if not specification:
            flash('规格不能为空', 'error')
            return render_template('material_add.html', categories=categories, units=units, form_data=form_data)

        if not category_id:
            flash('请选择药品分类', 'error')
            return render_template('material_add.html', categories=categories, units=units, form_data=form_data)

        if not unit_id:
            flash('请选择计量单位', 'error')
            return render_template('material_add.html', categories=categories, units=units, form_data=form_data)

        # 检查是否已存在相同的 名称+规格 组合
        existing = Material.query.filter_by(name=name, specification=specification).first()
        if existing:
            flash(f'药品"{name}"规格"{specification}"已存在，请勿重复添加', 'error')
            return render_template('material_add.html', categories=categories, units=units, form_data=form_data)

        # 保存到数据库
        try:
            new_mat = Material(
                name=name,
                specification=specification,
                category_id=category_id,
                unit_id=unit_id,
                stock=stock,
                remark=remark
            )
            db.session.add(new_mat)
            db.session.commit()
            flash('新增成功', 'success')
            return redirect(url_for('material.material_list'))
        except IntegrityError:
            db.session.rollback()
            flash(f'药品"{name}"规格"{specification}"已存在，请勿重复添加', 'error')
            return render_template('material_add.html', categories=categories, units=units, form_data=form_data)
        except DataError:
            db.session.rollback()
            flash('数据格式错误，请检查分类和单位是否正确选择', 'error')
            return render_template('material_add.html', categories=categories, units=units, form_data=form_data)

    # GET请求：显示新增表单
    return render_template('material_add.html', categories=categories, units=units, form_data={})

# 3. 编辑物资页面（保持不变，确保数据回显正确）
@material_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def material_edit(id):
    from app.models import MaterialCategory, Unit
    mat = Material.query.get_or_404(id)
    categories = MaterialCategory.query.all()
    units = Unit.query.all()

    if request.method == 'POST':
        name = request.form.get('name')
        specification = request.form.get('specification')
        category_id = request.form.get('category_id')
        unit_id = request.form.get('unit_id')

        # 验证必填字段
        if not name:
            flash('药品名称不能为空', 'error')
            return render_template('material_edit.html', material=mat, categories=categories, units=units)

        if not specification:
            flash('规格不能为空', 'error')
            return render_template('material_edit.html', material=mat, categories=categories, units=units)

        if not category_id:
            flash('请选择药品分类', 'error')
            return render_template('material_edit.html', material=mat, categories=categories, units=units)

        if not unit_id:
            flash('请选择计量单位', 'error')
            return render_template('material_edit.html', material=mat, categories=categories, units=units)

        # 检查是否已存在相同的 名称+规格 组合（排除自身）
        existing = Material.query.filter(
            Material.name == name,
            Material.specification == specification,
            Material.id != id  # 排除当前编辑的记录
        ).first()
        if existing:
            flash(f'药品"{name}"规格"{specification}"已存在，请勿重复', 'error')
            return render_template('material_edit.html', material=mat, categories=categories, units=units)

        try:
            mat.name = name
            mat.specification = specification
            mat.category_id = request.form.get('category_id')
            mat.unit_id = request.form.get('unit_id')
            mat.stock = request.form.get('stock', 0)
            mat.remark = request.form.get('remark')

            db.session.commit()
            flash('编辑成功', 'success')
            return redirect(url_for('material.material_list'))
        except IntegrityError:
            db.session.rollback()
            flash(f'药品"{name}"规格"{specification}"已存在，请勿重复', 'error')
            return render_template('material_edit.html', material=mat, categories=categories, units=units)
        except DataError:
            db.session.rollback()
            flash('数据格式错误，请检查分类和单位是否正确选择', 'error')
            return render_template('material_edit.html', material=mat, categories=categories, units=units)

    return render_template('material_edit.html', material=mat, categories=categories, units=units)

# 4. 删除物资（保持不变）
@material_bp.route('/delete/<int:id>')
def material_delete(id):
    mat = Material.query.get_or_404(id)
    db.session.delete(mat)
    db.session.commit()
    flash('删除成功', 'success')
    return redirect(url_for('material.material_list'))