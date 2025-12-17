from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# 初始化数据库
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 绑定数据库
    db.init_app(app)
    
    # 注册路由
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # 创建数据库表（首次运行自动创建）
    with app.app_context():
        db.create_all()
        # 初始化默认管理员（如果没有）
        from app.models import User
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", real_name="系统管理员")
            admin.set_password("123456")  # 密码123456
            db.session.add(admin)
            db.session.commit()
    
    return app