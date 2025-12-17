from flask import Blueprint, render_template

# 蓝图名称为'main'，总导航页为根路径
main_bp = Blueprint('main', __name__)

# 访问 http://127.0.0.1:5000 时显示总导航页
@main_bp.route('/')
def index():
    return render_template('index.html')  # 对应上面的总导航模板