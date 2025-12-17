from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Unit

unit_bp = Blueprint('unit', __name__, url_prefix='/unit')

# 单位列表页（支持搜索）
@unit_bp.route('/list')
def unit_list():
    keyword = request.args.get('keyword', '').strip()
    query = Unit.query
    if keyword:
        query = query.filter(
            db.or_(
                Unit.name.like(f'%{keyword}%'),
                Unit.abbreviation.like(f'%{keyword}%')
            )
        )
    units = query.all()
    return render_template('unit_list.html', units=units, keyword=keyword)

# 新增单位
@unit_bp.route('/add', methods=['GET', 'POST'])
def unit_add():
    if request.method == 'POST':
        name = request.form.get('name')
        abbreviation = request.form.get('abbreviation')
        
        if not name:
            flash('单位名称不能为空', 'error')
            return render_template('unit_add.html')
        
        # 检查重复
        if Unit.query.filter_by(name=name).first():
            flash('该单位已存在', 'error')
            return render_template('unit_add.html')
        
        new_unit = Unit(name=name, abbreviation=abbreviation)
        db.session.add(new_unit)
        db.session.commit()
        flash('新增成功', 'success')
        return redirect(url_for('unit.unit_list'))
    
    return render_template('unit_add.html')

# 编辑单位
@unit_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def unit_edit(id):
    unit = Unit.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name')
        # 检查重复（排除当前记录）
        if Unit.query.filter_by(name=name).first() and name != unit.name:
            flash('该单位已存在', 'error')
            return render_template('unit_edit.html', unit=unit)
        
        unit.name = name
        unit.abbreviation = request.form.get('abbreviation')
        db.session.commit()
        flash('编辑成功', 'success')
        return redirect(url_for('unit.unit_list'))
    
    return render_template('unit_edit.html', unit=unit)

# 删除单位
@unit_bp.route('/delete/<int:id>')
def unit_delete(id):
    unit = Unit.query.get_or_404(id)
    db.session.delete(unit)
    db.session.commit()
    flash('删除成功', 'success')
    return redirect(url_for('unit.unit_list'))