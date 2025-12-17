from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db  

# 1. 药品分类模型（对应 MedicineCategory）
class MedicineCategory(db.Model):
    __tablename__ = 'medicine_category'  # 数据库表名
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(100), nullable=False, unique=True)  # 分类名称（如：西药、中成药、保健品）
    remark = db.Column(db.String(200))  # 备注
    create_time = db.Column(db.DateTime, default=datetime.now)  # 创建时间

    # 关联药品（一个分类对应多个药品）
    medicines = db.relationship('Medicine', backref='category', lazy=True)

# 2. 单位模型（对应 Unit）
class Unit(db.Model):
    __tablename__ = 'unit'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # 单位名称（如：个、千克）
    abbreviation = db.Column(db.String(20))  # 缩写（如：kg）

    # 关联药品
    medicines = db.relationship('Medicine', backref='unit', lazy=True)


# 3. 医药供应商模型（对应 Supplier）
class Supplier(db.Model):
    __tablename__ = 'supplier'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # 供应商名称（唯一）
    license_number = db.Column(db.String(50), unique=True)  # 药品经营许可证号（唯一）
    contact = db.Column(db.String(50))  # 联系人
    phone = db.Column(db.String(20))  # 电话
    address = db.Column(db.String(200))  # 地址
    create_time = db.Column(db.DateTime, default=datetime.now)

    # 关联采购单
    purchases = db.relationship('Purchase', backref='supplier', lazy=True)


# 4. 药品仓库模型（对应 Warehouse）
class Warehouse(db.Model):
    __tablename__ = 'warehouse'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # 仓库名称（唯一）
    warehouse_type = db.Column(db.String(50))  # 仓库类型（常温库、冷藏库、阴凉库）
    location = db.Column(db.String(200), unique=True)  # 位置（唯一）
    manager = db.Column(db.String(50))  # 管理员
    phone = db.Column(db.String(20))  # 电话
    is_active = db.Column(db.Integer, default=1)  # 是否启用（1=启用，0=禁用）

    # 关联采购单和销售单
    purchases = db.relationship('Purchase', backref='warehouse', lazy=True)
    sales = db.relationship('Sale', backref='warehouse', lazy=True)


# 5. 药品模型（对应 Medicine）
class Medicine(db.Model):
    __tablename__ = 'medicine'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, index=True)  # 药品名称，添加索引
    generic_name = db.Column(db.String(100))  # 通用名称
    approval_number = db.Column(db.String(50), unique=True)  # 批准文号（国家唯一）
    specification = db.Column(db.String(100), nullable=False)  # 规格（如：10mg*24片），必填，缩短长度避免索引超限
    dosage_form = db.Column(db.String(50))  # 剂型（片剂、胶囊、注射液等）
    manufacturer = db.Column(db.String(200))  # 生产厂家
    category_id = db.Column(db.Integer, db.ForeignKey('medicine_category.id'))  # 关联分类
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))  # 关联单位
    is_prescription = db.Column(db.Integer, default=0)  # 是否处方药（0=OTC，1=处方药）
    stock = db.Column(db.Integer, default=0)  # 当前库存
    min_stock = db.Column(db.Integer, default=0)  # 最低库存预警
    retail_price = db.Column(db.Float, default=0)  # 零售价
    create_time = db.Column(db.DateTime, default=datetime.now)
    remark = db.Column(db.String(500))

    # 关联采购明细、销售明细、盘点明细
    purchase_details = db.relationship('PurchaseDetail', backref='medicine', lazy=True)
    sale_details = db.relationship('SaleDetail', backref='medicine', lazy=True)
    stock_details = db.relationship('StockCheckDetail', backref='medicine', lazy=True)

    # 联合唯一约束：药品名称+规格 唯一（避免重复录入同一药品）
    __table_args__ = (
        db.UniqueConstraint('name', 'specification', name='uq_medicine_name_spec'),
        db.Index('idx_medicine_name', 'name'),  # 查询优化索引
    )


# 6. 采购入库单主表（对应 Purchase）
class Purchase(db.Model):
    __tablename__ = 'purchase'
    purchase_id = db.Column(db.String(50), primary_key=True)  # 采购单号（如：PC20231114001）
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))  # 关联供应商
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))  # 关联仓库
    purchase_date = db.Column(db.Date, nullable=False)  # 采购日期
    total_amount = db.Column(db.Float, default=0)  # 总金额
    remark = db.Column(db.Text)  # 备注
    audit_status = db.Column(db.Integer, default=0)  # 审核状态（0=待审核，1=已审核，2=已驳回）
    create_time = db.Column(db.DateTime, default=datetime.now)

    # 关联采购明细
    details = db.relationship('PurchaseDetail', backref='purchase', lazy=True)

# 为了兼容旧路由代码，在类定义后添加字段别名
Purchase.inbound_date = Purchase.purchase_date
Purchase.inbound_id = Purchase.purchase_id


# 7. 采购入库单明细表（对应 PurchaseDetail）
class PurchaseDetail(db.Model):
    __tablename__ = 'purchase_detail'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.String(50), db.ForeignKey('purchase.purchase_id'))  # 关联采购单
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))  # 关联药品
    production_batch = db.Column(db.String(50))  # 生产批次
    production_date = db.Column(db.Date)  # 生产日期
    expiry_date = db.Column(db.Date)  # 有效期
    quantity = db.Column(db.Integer, nullable=False)  # 采购数量
    unit_price = db.Column(db.Float, nullable=False)  # 采购单价
    amount = db.Column(db.Float)  # 金额（数量×单价）


# 8. 销售出库单主表（对应 Sale）
class Sale(db.Model):
    __tablename__ = 'sale'
    sale_id = db.Column(db.String(50), primary_key=True)  # 销售单号（如：SL20231114001）
    customer_name = db.Column(db.String(100))  # 客户姓名
    customer_phone = db.Column(db.String(20))  # 客户电话
    prescription_no = db.Column(db.String(50))  # 处方单号（处方药需要）
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))  # 关联仓库
    sale_date = db.Column(db.Date, nullable=False)  # 销售日期
    total_amount = db.Column(db.Float, default=0)  # 总金额
    remark = db.Column(db.Text)  # 备注
    audit_status = db.Column(db.Integer, default=0)  # 审核状态
    create_time = db.Column(db.DateTime, default=datetime.now)

    # 关联销售明细
    details = db.relationship('SaleDetail', backref='sale', lazy=True)

# 为了兼容旧路由代码，在类定义后添加字段别名
Sale.outbound_date = Sale.sale_date
Sale.outbound_id = Sale.sale_id
Sale.dept_name = Sale.customer_name  # 领用部门 -> 客户名称


# 9. 销售出库单明细表（对应 SaleDetail）
class SaleDetail(db.Model):
    __tablename__ = 'sale_detail'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.String(50), db.ForeignKey('sale.sale_id'))  # 关联销售单
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))  # 关联药品
    quantity = db.Column(db.Integer, nullable=False)  # 销售数量
    unit_price = db.Column(db.Float, nullable=False)  # 销售单价
    amount = db.Column(db.Float)  # 金额（数量×单价）


# 10. 库存盘点主表（对应 StockCheck）
class StockCheck(db.Model):
    __tablename__ = 'stock_check'
    check_id = db.Column(db.String(50), primary_key=True)  # 盘点单号（如：CHECK20231114001）
    checker = db.Column(db.String(50), nullable=False)  # 盘点人
    check_date = db.Column(db.Date, nullable=False)  # 盘点日期
    remark = db.Column(db.Text)  # 备注
    create_time = db.Column(db.DateTime, default=datetime.now)

    # 关联盘点明细
    details = db.relationship('StockCheckDetail', backref='check', lazy=True)


# 11. 库存盘点明细表（对应 StockCheckDetail）
class StockCheckDetail(db.Model):
    __tablename__ = 'stock_check_detail'
    id = db.Column(db.Integer, primary_key=True)
    check_id = db.Column(db.String(50), db.ForeignKey('stock_check.check_id'))  # 关联盘点单
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))  # 关联药品
    system_stock = db.Column(db.Integer, nullable=False)  # 系统库存
    actual_stock = db.Column(db.Integer, nullable=False)  # 实际库存
    diff = db.Column(db.Integer)  # 差异（实际-系统）


# 12. 用户模型（用于登录管理）
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)  # 用户名（唯一）
    password = db.Column(db.String(200), nullable=False)  # 密码（哈希存储）
    real_name = db.Column(db.String(50))  # 真实姓名
    role = db.Column(db.String(20), default='admin')  # 角色（admin=管理员）
    is_active = db.Column(db.Integer, default=1)  # 是否启用（1=启用，0=禁用）
    create_time = db.Column(db.DateTime, default=datetime.now)  # 创建时间
    last_login = db.Column(db.DateTime)  # 最后登录时间

    def set_password(self, password):
        """设置密码（哈希存储）"""
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password)


# ============================================================
# 兼容层：为旧路由代码提供别名，避免导入错误
# ============================================================
Material = Medicine  # 物资 → 药品
MaterialCategory = MedicineCategory  # 物资分类 → 药品分类
Inbound = Purchase  # 入库单 → 采购单
InboundDetail = PurchaseDetail  # 入库明细 → 采购明细
Outbound = Sale  # 出库单 → 销售单
OutboundDetail = SaleDetail  # 出库明细 → 销售明细