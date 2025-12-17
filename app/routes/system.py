from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import User, Role, OperationLog
from datetime import datetime

system_bp = Blueprint("system", __name__)

# 用户管理
@system_bp.route("/user")
def user_list():
    users = User.query.join(Role, User.role_id == Role.role_id).all()
    return render_template("system_user_list.html", users=users, Role=Role)

# 添加用户
@system_bp.route("/user/add", methods=["GET", "POST"])
def add_user():
    roles = Role.query.all()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        real_name = request.form.get("real_name")
        role_id = request.form.get("role_id")

        if not username or not password:
            flash("账号和密码不能为空！")
            return render_template("system_user_add.html", roles=roles)
        if User.query.filter_by(username=username).first():
            flash("该账号已存在！")
            return render_template("system_user_add.html", roles=roles)

        new_user = User(username=username, real_name=real_name, role_id=role_id)
        new_user.set_password(password)  # 加密密码
        db.session.add(new_user)
        db.session.commit()

        # 记录操作日志
        log = OperationLog(
            user_id=1,  # 当前操作人（管理员）
            operation="添加用户",
            detail=f"添加用户：{username}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        flash("用户添加成功！")
        return redirect(url_for("system.user_list"))
    return render_template("system_user_add.html", roles=roles)

# 角色管理
@system_bp.route("/role")
def role_list():
    roles = Role.query.all()
    return render_template("system_role_list.html", roles=roles)

# 添加角色
@system_bp.route("/role/add", methods=["GET", "POST"])
def add_role():
    if request.method == "POST":
        role_name = request.form.get("role_name")
        permissions = request.form.get("permissions")
        if not role_name:
            flash("角色名称不能为空！")
            return render_template("system_role_add.html")
        if Role.query.filter_by(role_name=role_name).first():
            flash("该角色已存在！")
            return render_template("system_role_add.html")
        new_role = Role(role_name=role_name, permissions=permissions)
        db.session.add(new_role)
        db.session.commit()
        flash("角色添加成功！")
        return redirect(url_for("system.role_list"))
    return render_template("system_role_add.html")

# 操作日志
@system_bp.route("/log")
def log_list():
    logs = OperationLog.query.join(User, OperationLog.user_id == User.user_id).order_by(OperationLog.operation_time.desc()).all()
    return render_template("system_log_list.html", logs=logs, User=User)