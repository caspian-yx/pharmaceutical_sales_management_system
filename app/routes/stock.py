from flask import Blueprint, render_template, request, flash, redirect, url_for
from app import db
# 只导入你模型中存在的类（移除InboundItem/OutboundItem等）
from app.models import Material, MaterialCategory, Unit

# 定义蓝图（保持stock_bp名称不变）
stock_bp = Blueprint('stock', __name__, url_prefix='/stock')

# 1. 库存列表页（仅依赖现有模型）
@stock_bp.route('/list')
def stock_list():
    keyword = request.args.get('keyword', '').strip()
    category_id = request.args.get('category_id', '').strip()
    sort_by = request.args.get('sort_by', 'stock')
    order = request.args.get('order', 'asc')

    # 仅关联现有模型：物资、分类、单位
    query = Material.query.join(MaterialCategory).join(Unit)

    # 关键词搜索
    if keyword:
        query = query.filter(
            db.or_(
                Material.name.like(f'%{keyword}%'),
                Material.specification.like(f'%{keyword}%'),
                MaterialCategory.name.like(f'%{keyword}%')
            )
        )

    # 分类筛选
    if category_id and category_id.isdigit():
        query = query.filter(Material.category_id == int(category_id))

    # 排序
    if sort_by == 'stock':
        query = query.order_by(Material.stock.asc() if order == 'asc' else Material.stock.desc())
    elif sort_by == 'name':
        query = query.order_by(Material.name.asc() if order == 'asc' else Material.name.desc())

    stocks = query.all()
    categories = MaterialCategory.query.all()  # 所有分类用于筛选

    return render_template(
        'stock_list.html',
        stocks=stocks,
        categories=categories,
        keyword=keyword,
        selected_category=category_id,
        sort_by=sort_by,
        order=order
    )

# 2. 库存详情页（仅显示物资基本信息，不依赖入库/出库记录）
@stock_bp.route('/detail/<int:material_id>')
def stock_detail(material_id):
    material = Material.query.get_or_404(material_id)
    return render_template('stock_detail.html', material=material)

# 3. 低库存预警页（仅依赖物资模型）
@stock_bp.route('/warning')
def stock_warning():
    threshold = 10  # 可自定义阈值
    low_stocks = Material.query.join(MaterialCategory).join(Unit)\
        .filter(Material.stock <= threshold)\
        .order_by(Material.stock.asc())\
        .all()
    return render_template('stock_warning.html', low_stocks=low_stocks, threshold=threshold)