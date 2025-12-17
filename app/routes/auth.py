from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import User
from datetime import datetime
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    # 如果已经登录，直接跳转到主页
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空', 'error')
            return render_template('login.html', username=username)

        # 查询用户
        user = User.query.filter_by(username=username).first()

        if user and user.is_active == 1:
            # 验证密码
            if user.check_password(password):
                # 登录成功，设置会话
                session.permanent = True  # 设置为永久会话，应用超时时间
                session['user_id'] = user.id
                session['username'] = user.username
                session['real_name'] = user.real_name or user.username

                # 更新最后登录时间
                user.last_login = datetime.now()
                db.session.commit()

                flash(f'欢迎回来，{session["real_name"]}！', 'success')
                # 跳转到主页或之前访问的页面
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('密码错误，请重试', 'error')
        elif user and user.is_active == 0:
            flash('该账户已被禁用，请联系管理员', 'error')
        else:
            flash('用户名不存在', 'error')

        return render_template('login.html', username=username)

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """登出"""
    username = session.get('real_name', '用户')
    session.clear()
    flash(f'{username}，您已成功退出登录', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/init_admin')
def init_admin():
    """初始化管理员账户（仅用于首次安装）"""
    # 检查是否已有管理员
    admin = User.query.filter_by(username='admin').first()
    if admin:
        flash('管理员账户已存在，无需重复创建', 'error')
        return redirect(url_for('auth.login'))

    # 创建默认管理员账户
    admin = User(
        username='admin',
        real_name='系统管理员',
        role='admin',
        is_active=1
    )
    admin.set_password('admin123')  # 默认密码：admin123

    db.session.add(admin)
    db.session.commit()

    flash('管理员账户创建成功！用户名：admin，密码：admin123（请尽快修改密码）', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        old_password = request.form.get('old_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # 验证输入
        if not old_password or not new_password or not confirm_password:
            flash('所有字段都不能为空', 'error')
            return render_template('change_password.html')

        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return render_template('change_password.html')

        if len(new_password) < 6:
            flash('新密码长度至少为 6 位', 'error')
            return render_template('change_password.html')

        # 获取当前用户
        user = User.query.get(session['user_id'])

        # 验证旧密码
        if not user.check_password(old_password):
            flash('原密码错误', 'error')
            return render_template('change_password.html')

        # 更新密码
        user.set_password(new_password)
        db.session.commit()

        flash('密码修改成功，请重新登录', 'success')
        return redirect(url_for('auth.logout'))

    return render_template('change_password.html')
