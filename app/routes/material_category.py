from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import MaterialCategory  # 导入修正后的模型
from sqlalchemy.exc import IntegrityError  # 导入异常

# 物资分类蓝图（url_prefix保持为'/material_category'，路径正确）
material_category_bp = Blueprint('material_category', __name__, url_prefix='/material_category')

# 1. 分类列表页（支持搜索）
@material_category_bp.route('/list')
def category_list():
    keyword = request.args.get('keyword', '').strip()
    query = MaterialCategory.query
    if keyword:
        # 修正：搜索字段用name（模型中正确字段）
        query = query.filter(MaterialCategory.name.like(f'%{keyword}%'))
    categories = query.all()
    return render_template('material_category_list.html', categories=categories, keyword=keyword)

# 2. 新增分类
@material_category_bp.route('/add', methods=['GET', 'POST'])
def category_add():
    if request.method == 'POST':
        name = request.form.get('category_name')  # 表单字段名可保持，但模型中用name
        remark = request.form.get('remark')

        # 保存用户输入，用于出错时回显
        form_data = {
            'category_name': name,
            'remark': remark
        }

        if not name:
            flash('类别名称不能为空', 'error')
            return render_template('material_category_add.html', form_data=form_data)

        # 修正：检查重复时用name字段
        if MaterialCategory.query.filter_by(name=name).first():
            flash(f'类别"{name}"已存在，请勿重复添加', 'error')
            return render_template('material_category_add.html', form_data=form_data)

        # 修正：模型实例化用name和remark（匹配模型字段）
        try:
            new_category = MaterialCategory(
                name=name,
                remark=remark
            )
            db.session.add(new_category)
            db.session.commit()
            flash('新增成功', 'success')
            return redirect(url_for('material_category.category_list'))
        except IntegrityError:
            db.session.rollback()
            flash(f'类别"{name}"已存在，请勿重复添加', 'error')
            return render_template('material_category_add.html', form_data=form_data)

    return render_template('material_category_add.html', form_data={})

# 3. 编辑分类
@material_category_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def category_edit(id):
    category = MaterialCategory.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('category_name')
        remark = request.form.get('remark')

        # 修正：检查重复时用name字段，排除当前记录
        existing = MaterialCategory.query.filter(
            MaterialCategory.name == name,
            MaterialCategory.id != id
        ).first()

        if existing:
            flash(f'类别"{name}"已存在，请勿重复', 'error')
            return render_template('material_category_edit.html', category=category)

        try:
            # 修正：赋值给name字段（模型中正确字段）
            category.name = name
            category.remark = remark
            db.session.commit()
            flash('编辑成功', 'success')
            return redirect(url_for('material_category.category_list'))
        except IntegrityError:
            db.session.rollback()
            flash(f'类别"{name}"已存在，请勿重复', 'error')
            return render_template('material_category_edit.html', category=category)

    return render_template('material_category_edit.html', category=category)

# 4. 删除分类
@material_category_bp.route('/delete/<int:id>')
def category_delete(id):
    category = MaterialCategory.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('删除成功', 'success')
    return redirect(url_for('material_category.category_list'))