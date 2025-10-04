import os
from datetime import datetime
from decimal import Decimal

import pandas as pd
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///candles.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class FixedCost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.Numeric(10, 2), default=0)
    hosting = db.Column(db.Numeric(10, 2), default=0)
    pro_labore = db.Column(db.Numeric(10, 2), default=0)
    paid_traffic = db.Column(db.Numeric(10, 2), default=0)
    accounting = db.Column(db.Numeric(10, 2), default=0)
    utilities = db.Column(db.Numeric(10, 2), default=0)
    other_description = db.Column(db.String(255))
    other_amount = db.Column(db.Numeric(10, 2), default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContainerBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(120), nullable=False)
    capacity = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False)
    lot_price = db.Column(db.Numeric(10, 2), default=0)
    unit_price = db.Column(db.Numeric(10, 4), default=0)
    freight = db.Column(db.Numeric(10, 2), default=0)
    units_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def available_units(self) -> int:
        return max(self.quantity - self.units_used, 0)

    @property
    def base_unit_price(self) -> float:
        if self.unit_price and float(self.unit_price) > 0:
            return float(self.unit_price)
        if self.quantity:
            return float(self.lot_price or 0) / float(self.quantity)
        return 0.0

    @property
    def freight_per_unit(self) -> float:
        if not self.quantity:
            return 0.0
        return float(self.freight or 0) / float(self.quantity)

    @property
    def allocated_unit_cost(self) -> float:
        return self.base_unit_price + self.freight_per_unit


class EssenceBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(120), nullable=False)
    capacity_grams = db.Column(db.Float, nullable=False)
    stock_units = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    freight = db.Column(db.Numeric(10, 2), default=0)
    grams_used = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def total_grams(self) -> float:
        return float(self.capacity_grams) * float(self.stock_units)

    @property
    def available_grams(self) -> float:
        return max(self.total_grams - float(self.grams_used or 0), 0)

    @property
    def freight_per_unit(self) -> float:
        if not self.stock_units:
            return 0.0
        return float(self.freight or 0) / float(self.stock_units)

    @property
    def cost_per_gram(self) -> float:
        if not self.capacity_grams:
            return 0.0
        unit_total = float(self.unit_price or 0) + self.freight_per_unit
        return unit_total / float(self.capacity_grams)


class WaxBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(120), nullable=False)
    capacity_grams = db.Column(db.Float, nullable=False)
    stock_units = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    freight = db.Column(db.Numeric(10, 2), default=0)
    grams_used = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def total_grams(self) -> float:
        return float(self.capacity_grams) * float(self.stock_units)

    @property
    def available_grams(self) -> float:
        return max(self.total_grams - float(self.grams_used or 0), 0)

    @property
    def freight_per_unit(self) -> float:
        if not self.stock_units:
            return 0.0
        return float(self.freight or 0) / float(self.stock_units)

    @property
    def cost_per_gram(self) -> float:
        if not self.capacity_grams:
            return 0.0
        unit_total = float(self.unit_price or 0) + self.freight_per_unit
        return unit_total / float(self.capacity_grams)


class WickBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    lot_price = db.Column(db.Numeric(10, 2), default=0)
    unit_price = db.Column(db.Numeric(10, 4), default=0)
    freight = db.Column(db.Numeric(10, 2), default=0)
    units_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def available_units(self) -> int:
        return max(self.quantity - self.units_used, 0)

    @property
    def base_unit_price(self) -> float:
        if self.unit_price and float(self.unit_price) > 0:
            return float(self.unit_price)
        if self.quantity:
            return float(self.lot_price or 0) / float(self.quantity)
        return 0.0

    @property
    def freight_per_unit(self) -> float:
        if not self.quantity:
            return 0.0
        return float(self.freight or 0) / float(self.quantity)

    @property
    def allocated_unit_cost(self) -> float:
        return self.base_unit_price + self.freight_per_unit


class OtherVariableCost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    cost_per_unit = db.Column(db.Numeric(10, 4), nullable=False)


class CandleTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    wax_product = db.Column(db.String(120), nullable=False)
    wax_weight_g = db.Column(db.Float, nullable=False)
    essence_product = db.Column(db.String(120), nullable=False)
    fragrance_percentage = db.Column(db.Float, nullable=False)
    container_product = db.Column(db.String(120), nullable=False)
    wick_product = db.Column(db.String(120))
    other_variable_cost = db.Column(db.Numeric(10, 4), default=0)
    desired_margin = db.Column(db.Float, default=0.3)
    expected_monthly_units = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FinishedProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey("candle_template.id"))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2))
    unit_variable_cost = db.Column(db.Numeric(10, 2))
    unit_total_cost = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    template = db.relationship("CandleTemplate")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def ensure_default_user():
    if not User.query.first():
        user = User(username="admin")
        user.set_password(os.getenv("DEFAULT_ADMIN_PASSWORD", "admin"))
        db.session.add(user)
        db.session.commit()


with app.app_context():
    db.create_all()
    ensure_default_user()


def get_fixed_costs() -> FixedCost:
    fixed = FixedCost.query.first()
    if not fixed:
        fixed = FixedCost()
        db.session.add(fixed)
        db.session.commit()
    return fixed


def total_fixed_cost() -> float:
    fixed = get_fixed_costs()
    values = [
        fixed.domain,
        fixed.hosting,
        fixed.pro_labore,
        fixed.paid_traffic,
        fixed.accounting,
        fixed.utilities,
        fixed.other_amount,
    ]
    return sum(float(v or 0) for v in values)


def average_cost_per_container(product: str) -> float:
    batches = ContainerBatch.query.filter_by(product=product).all()
    if not batches:
        return 0.0
    total_units = sum(b.quantity for b in batches)
    if not total_units:
        return 0.0
    total_cost = sum((b.base_unit_price + b.freight_per_unit) * b.quantity for b in batches)
    return total_cost / total_units


def average_cost_per_gram_essence(product: str) -> float:
    batches = EssenceBatch.query.filter_by(product=product).all()
    if not batches:
        return 0.0
    total_grams = sum(b.total_grams for b in batches)
    if not total_grams:
        return 0.0
    total_cost = sum(b.cost_per_gram * b.total_grams for b in batches)
    return total_cost / total_grams


def average_cost_per_gram_wax(product: str) -> float:
    batches = WaxBatch.query.filter_by(product=product).all()
    if not batches:
        return 0.0
    total_grams = sum(b.total_grams for b in batches)
    if not total_grams:
        return 0.0
    total_cost = sum(b.cost_per_gram * b.total_grams for b in batches)
    return total_cost / total_grams


def average_cost_per_wick(product: str) -> float:
    batches = WickBatch.query.filter_by(product=product).all()
    if not batches:
        return 0.0
    total_units = sum(b.quantity for b in batches)
    if not total_units:
        return 0.0
    total_cost = sum(b.allocated_unit_cost * b.quantity for b in batches)
    return total_cost / total_units


def template_cost_breakdown(template: CandleTemplate) -> dict:
    wax_cost_per_gram = average_cost_per_gram_wax(template.wax_product)
    essence_cost_per_gram = average_cost_per_gram_essence(template.essence_product)
    container_cost = average_cost_per_container(template.container_product)
    wick_cost = average_cost_per_wick(template.wick_product) if template.wick_product else 0.0
    wax_cost = template.wax_weight_g * wax_cost_per_gram
    essence_grams = template.wax_weight_g * (template.fragrance_percentage / 100.0)
    essence_cost = essence_grams * essence_cost_per_gram
    other_cost = float(template.other_variable_cost or 0)
    variable_cost = wax_cost + essence_cost + container_cost + wick_cost + other_cost
    return {
        "wax_cost": wax_cost,
        "essence_cost": essence_cost,
        "container_cost": container_cost,
        "wick_cost": wick_cost,
        "other_cost": other_cost,
        "variable_cost": variable_cost,
    }


def total_expected_units() -> int:
    units = sum(t.expected_monthly_units for t in CandleTemplate.query.all())
    return units or 1


def template_financials(template: CandleTemplate) -> dict:
    breakdown = template_cost_breakdown(template)
    fixed_per_unit = total_fixed_cost() / total_expected_units()
    total_unit_cost = breakdown["variable_cost"] + fixed_per_unit
    price_suggested = total_unit_cost * (1 + template.desired_margin)
    unit_profit = price_suggested - total_unit_cost
    return {
        "breakdown": breakdown,
        "fixed_per_unit": fixed_per_unit,
        "total_unit_cost": total_unit_cost,
        "price_suggested": price_suggested,
        "unit_profit": unit_profit,
    }


def aggregate_dashboard_metrics():
    templates = CandleTemplate.query.all()
    if not templates:
        return {
            "average_unit_cost": 0,
            "potential_revenue": 0,
            "break_even": None,
            "annual_dre": None,
        }

    total_units = total_expected_units()
    weighted_cost = 0.0
    weighted_price = 0.0
    total_unit_profit = 0.0
    for template in templates:
        info = template_financials(template)
        expected_units = template.expected_monthly_units or 0
        weighted_cost += info["total_unit_cost"] * expected_units
        weighted_price += info["price_suggested"] * expected_units
        total_unit_profit += info["unit_profit"] * expected_units
    average_unit_cost = weighted_cost / total_units if total_units else 0
    average_unit_profit = (weighted_price - weighted_cost) / total_units if total_units else 0
    break_even = None
    if average_unit_profit > 0:
        break_even = total_fixed_cost() / average_unit_profit

    monthly_revenue = weighted_price
    monthly_cmv = weighted_cost
    monthly_fixed = total_fixed_cost()
    monthly_result = monthly_revenue - monthly_cmv - monthly_fixed
    annual = {
        "revenue": monthly_revenue * 12,
        "cmv": monthly_cmv * 12,
        "fixed": monthly_fixed * 12,
        "result": monthly_result * 12,
    }

    potential_revenue = calculate_potential_revenue()

    return {
        "average_unit_cost": average_unit_cost,
        "potential_revenue": potential_revenue,
        "break_even": break_even,
        "annual_dre": annual,
    }


def load_dataframe(file_storage):
    filename = secure_filename(file_storage.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file_storage.save(path)
    try:
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)
    finally:
        os.remove(path)
    return df


def safe_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, float) and (pd.isna(value) or pd.isnull(value)):
        return Decimal("0")
    if isinstance(value, str) and not value.strip():
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def safe_float(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, float) and (pd.isna(value) or pd.isnull(value)):
        return 0.0
    if isinstance(value, str) and not value.strip():
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def safe_int(value) -> int:
    return int(round(safe_float(value)))


def add_container_from_row(row):
    batch = ContainerBatch(
        product=row.get("Produto", "Sem nome"),
        capacity=row.get("Capacidade"),
        quantity=safe_int(row.get("Qtd", 0)),
        lot_price=safe_decimal(row.get("Preço Lote (R$)")),
        unit_price=safe_decimal(row.get("Preço Unit. (R$)")),
        freight=safe_decimal(row.get("Frete (R$)")),
    )
    db.session.add(batch)


def add_essence_from_row(row):
    batch = EssenceBatch(
        product=row.get("Produto", "Sem nome"),
        capacity_grams=safe_float(row.get("Capacidade (g)")),
        stock_units=safe_int(row.get("Estoque (un)")),
        unit_price=safe_decimal(row.get("Preço Unitário (R$)")),
        freight=safe_decimal(row.get("Frete (R$)")),
    )
    db.session.add(batch)


def add_wax_from_row(row):
    batch = WaxBatch(
        product=row.get("Produto", "Sem nome"),
        capacity_grams=safe_float(row.get("Capacidade (g)")),
        stock_units=safe_int(row.get("Estoque (un)")),
        unit_price=safe_decimal(row.get("Preço Unitário (R$)")),
        freight=safe_decimal(row.get("Frete (R$)")),
    )
    db.session.add(batch)


def inventory_summary():
    containers = ContainerBatch.query.all()
    essences = EssenceBatch.query.all()
    waxes = WaxBatch.query.all()
    wicks = WickBatch.query.all()
    return {
        "containers": containers,
        "essences": essences,
        "waxes": waxes,
        "wicks": wicks,
    }


def calculate_possible_units(template: CandleTemplate) -> int:
    wax_required = template.wax_weight_g
    essence_required = template.wax_weight_g * (template.fragrance_percentage / 100.0)

    total_wax = sum(
        b.available_grams for b in WaxBatch.query.filter_by(product=template.wax_product).all()
    )
    total_essence = sum(
        b.available_grams
        for b in EssenceBatch.query.filter_by(product=template.essence_product).all()
    )
    total_containers = sum(
        b.available_units
        for b in ContainerBatch.query.filter_by(product=template.container_product).all()
    )
    total_wicks = None
    if template.wick_product:
        total_wicks = sum(
            b.available_units for b in WickBatch.query.filter_by(product=template.wick_product).all()
        )

    possible_by_wax = int(total_wax // wax_required) if wax_required else 0
    possible_by_essence = int(total_essence // essence_required) if essence_required else possible_by_wax
    possible_by_container = total_containers

    candidates = [possible_by_wax, possible_by_container]
    if essence_required > 0:
        candidates.append(possible_by_essence)
    if total_wicks is not None:
        candidates.append(total_wicks)
    return max(min(candidates), 0) if candidates else 0


def calculate_potential_revenue() -> float:
    total = 0.0
    templates = CandleTemplate.query.all()
    for template in templates:
        info = template_financials(template)
        possible = calculate_possible_units(template)
        total += possible * info["price_suggested"]
    return total


def allocate_from_batches(batches, required_amount, attr_name="grams_used", capacity_attr=None):
    remaining = required_amount
    for batch in batches:
        if capacity_attr:
            available = getattr(batch, capacity_attr) - float(getattr(batch, attr_name) or 0)
        else:
            available = getattr(batch, "available_units")
        if available <= 0:
            continue
        take = min(available, remaining)
        current_used = float(getattr(batch, attr_name) or 0)
        setattr(batch, attr_name, current_used + take)
        remaining -= take
        if remaining <= 0:
            break
    if remaining > 0:
        raise ValueError("Estoque insuficiente para completar a produção.")


def allocate_wax(product: str, grams: float):
    batches = (
        WaxBatch.query.filter_by(product=product)
        .order_by(WaxBatch.created_at.asc())
        .all()
    )
    allocate_from_batches(batches, grams, attr_name="grams_used", capacity_attr="total_grams")


def allocate_essence(product: str, grams: float):
    batches = (
        EssenceBatch.query.filter_by(product=product)
        .order_by(EssenceBatch.created_at.asc())
        .all()
    )
    allocate_from_batches(batches, grams, attr_name="grams_used", capacity_attr="total_grams")


def allocate_containers(product: str, units: int):
    batches = (
        ContainerBatch.query.filter_by(product=product)
        .order_by(ContainerBatch.created_at.asc())
        .all()
    )
    allocate_from_batches(batches, units, attr_name="units_used", capacity_attr=None)


def allocate_wicks(product: str, units: int):
    batches = (
        WickBatch.query.filter_by(product=product)
        .order_by(WickBatch.created_at.asc())
        .all()
    )
    allocate_from_batches(batches, units, attr_name="units_used", capacity_attr=None)


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Credenciais inválidas", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    metrics = aggregate_dashboard_metrics()
    inventory = inventory_summary()
    finished = FinishedProduct.query.all()
    total_finished_units = sum(item.quantity for item in finished)
    return render_template(
        "dashboard.html",
        metrics=metrics,
        inventory=inventory,
        finished_units=total_finished_units,
    )


@app.route("/pricing", methods=["GET", "POST"])
@login_required
def pricing():
    fixed = get_fixed_costs()
    templates = CandleTemplate.query.all()
    if request.method == "POST":
        form_name = request.form.get("form_name")
        try:
            if form_name == "fixed_costs":
                fixed.domain = request.form.get("domain", type=float) or 0
                fixed.hosting = request.form.get("hosting", type=float) or 0
                fixed.pro_labore = request.form.get("pro_labore", type=float) or 0
                fixed.paid_traffic = request.form.get("paid_traffic", type=float) or 0
                fixed.accounting = request.form.get("accounting", type=float) or 0
                fixed.utilities = request.form.get("utilities", type=float) or 0
                fixed.other_description = request.form.get("other_description")
                fixed.other_amount = request.form.get("other_amount", type=float) or 0
                fixed.updated_at = datetime.utcnow()
                db.session.commit()
                flash("Custos fixos atualizados", "success")
            elif form_name == "upload_containers":
                file = request.files.get("file")
                if file and file.filename:
                    df = load_dataframe(file)
                    for _, row in df.iterrows():
                        add_container_from_row(row)
                    db.session.commit()
                    flash("Planilha de latas importada", "success")
            elif form_name == "upload_essences":
                file = request.files.get("file")
                if file and file.filename:
                    df = load_dataframe(file)
                    for _, row in df.iterrows():
                        add_essence_from_row(row)
                    db.session.commit()
                    flash("Planilha de essências importada", "success")
            elif form_name == "upload_waxes":
                file = request.files.get("file")
                if file and file.filename:
                    df = load_dataframe(file)
                    for _, row in df.iterrows():
                        add_wax_from_row(row)
                    db.session.commit()
                    flash("Planilha de ceras importada", "success")
            elif form_name == "manual_container":
                batch = ContainerBatch(
                    product=request.form.get("product"),
                    capacity=request.form.get("capacity"),
                    quantity=request.form.get("quantity", type=int) or 0,
                    lot_price=request.form.get("lot_price", type=float) or 0,
                    unit_price=request.form.get("unit_price", type=float) or 0,
                    freight=request.form.get("freight", type=float) or 0,
                )
                db.session.add(batch)
                db.session.commit()
                flash("Lata cadastrada", "success")
            elif form_name == "manual_essence":
                batch = EssenceBatch(
                    product=request.form.get("product"),
                    capacity_grams=request.form.get("capacity_grams", type=float) or 0,
                    stock_units=request.form.get("stock_units", type=int) or 0,
                    unit_price=request.form.get("unit_price", type=float) or 0,
                    freight=request.form.get("freight", type=float) or 0,
                )
                db.session.add(batch)
                db.session.commit()
                flash("Essência cadastrada", "success")
            elif form_name == "manual_wax":
                batch = WaxBatch(
                    product=request.form.get("product"),
                    capacity_grams=request.form.get("capacity_grams", type=float) or 0,
                    stock_units=request.form.get("stock_units", type=int) or 0,
                    unit_price=request.form.get("unit_price", type=float) or 0,
                    freight=request.form.get("freight", type=float) or 0,
                )
                db.session.add(batch)
                db.session.commit()
                flash("Cera cadastrada", "success")
            elif form_name == "manual_wick":
                batch = WickBatch(
                    product=request.form.get("product"),
                    quantity=request.form.get("quantity", type=int) or 0,
                    lot_price=request.form.get("lot_price", type=float) or 0,
                    unit_price=request.form.get("unit_price", type=float) or 0,
                    freight=request.form.get("freight", type=float) or 0,
                )
                db.session.add(batch)
                db.session.commit()
                flash("Pavio cadastrado", "success")
            elif form_name == "manual_other":
                item = OtherVariableCost(
                    name=request.form.get("name"),
                    cost_per_unit=request.form.get("cost_per_unit", type=float) or 0,
                )
                db.session.add(item)
                db.session.commit()
                flash("Custo variável adicional cadastrado", "success")
            elif form_name == "template":
                margin = request.form.get("desired_margin", type=float) or 0
                if margin > 1.0:
                    margin = margin / 100.0
                template = CandleTemplate(
                    name=request.form.get("name"),
                    wax_product=request.form.get("wax_product"),
                    wax_weight_g=request.form.get("wax_weight_g", type=float) or 0,
                    essence_product=request.form.get("essence_product"),
                    fragrance_percentage=request.form.get("fragrance_percentage", type=float) or 0,
                    container_product=request.form.get("container_product"),
                    wick_product=request.form.get("wick_product") or None,
                    other_variable_cost=request.form.get("other_variable_cost", type=float) or 0,
                    desired_margin=margin,
                    expected_monthly_units=request.form.get("expected_monthly_units", type=int) or 0,
                )
                db.session.add(template)
                db.session.commit()
                flash("Template de vela criado", "success")
        except Exception as exc:
            db.session.rollback()
            flash(f"Erro ao processar a requisição: {exc}", "danger")
        return redirect(url_for("pricing"))

    inventory = inventory_summary()
    other_costs = OtherVariableCost.query.all()
    template_details = [
        {
            "template": template,
            "financials": template_financials(template),
        }
        for template in templates
    ]
    return render_template(
        "pricing.html",
        fixed=fixed,
        inventory=inventory,
        other_costs=other_costs,
        template_details=template_details,
    )


@app.route("/inventory")
@login_required
def inventory_view():
    templates = CandleTemplate.query.all()
    data = []
    for template in templates:
        financials = template_financials(template)
        possible = calculate_possible_units(template)
        data.append(
            {
                "template": template,
                "possible": possible,
                "financials": financials,
            }
        )
    return render_template(
        "inventory.html",
        inventory=inventory_summary(),
        template_data=data,
    )


@app.route("/production", methods=["GET", "POST"])
@login_required
def production():
    templates = CandleTemplate.query.all()
    if request.method == "POST":
        template_id = request.form.get("template_id", type=int)
        quantity = request.form.get("quantity", type=int) or 0
        selling_price = request.form.get("selling_price", type=float)
        template = CandleTemplate.query.get(template_id)
        if not template:
            flash("Template não encontrado", "danger")
            return redirect(url_for("production"))
        try:
            wax_required = template.wax_weight_g * quantity
            essence_required = template.wax_weight_g * (template.fragrance_percentage / 100.0) * quantity
            allocate_wax(template.wax_product, wax_required)
            if essence_required > 0:
                allocate_essence(template.essence_product, essence_required)
            allocate_containers(template.container_product, quantity)
            if template.wick_product:
                allocate_wicks(template.wick_product, quantity)
            financials = template_financials(template)
            unit_price = selling_price or financials["price_suggested"]
            finished = FinishedProduct(
                name=template.name,
                template_id=template.id,
                quantity=quantity,
                unit_price=unit_price,
                unit_variable_cost=financials["breakdown"]["variable_cost"],
                unit_total_cost=financials["total_unit_cost"],
            )
            db.session.add(finished)
            db.session.commit()
            flash("Produção registrada com sucesso", "success")
        except Exception as exc:
            db.session.rollback()
            flash(f"Erro na produção: {exc}", "danger")
        return redirect(url_for("production"))

    return render_template("production.html", templates=templates)


@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    templates = CandleTemplate.query.all()
    total_fixed = total_fixed_cost()
    revenue_budget = 0.0
    variable_budget = 0.0
    total_units = 0
    for template in templates:
        financials = template_financials(template)
        units = template.expected_monthly_units or 0
        total_units += units
        revenue_budget += financials["price_suggested"] * units
        variable_budget += financials["breakdown"]["variable_cost"] * units

    stock_value = 0.0
    for container in ContainerBatch.query.all():
        stock_value += container.allocated_unit_cost * container.available_units
    for essence in EssenceBatch.query.all():
        stock_value += essence.cost_per_gram * essence.available_grams
    for wax in WaxBatch.query.all():
        stock_value += wax.cost_per_gram * wax.available_grams
    for wick in WickBatch.query.all():
        stock_value += wick.allocated_unit_cost * wick.available_units

    monthly_result = revenue_budget - variable_budget - total_fixed
    annual_dre = {
        "revenue": revenue_budget * 12,
        "cmv": variable_budget * 12,
        "fixed": total_fixed * 12,
        "result": monthly_result * 12,
    }

    scenario_result = None
    if request.method == "POST":
        margin = request.form.get("scenario_margin", type=float) or 0
        if margin > 1.0:
            margin = margin / 100.0
        price = request.form.get("scenario_price", type=float) or 0
        volume = request.form.get("scenario_volume", type=int) or 0
        variable_cost = request.form.get("scenario_variable", type=float) or 0
        fixed_costs = request.form.get("scenario_fixed", type=float) or 0
        if price <= 0 and variable_cost > 0:
            price = variable_cost * (1 + margin)
        revenue = price * volume
        cmv = variable_cost * volume
        profit = revenue - cmv - fixed_costs
        scenario_result = {
            "revenue": revenue,
            "cmv": cmv,
            "fixed": fixed_costs,
            "profit": profit,
            "margin": (profit / revenue * 100) if revenue else 0,
        }

    return render_template(
        "budget.html",
        revenue_budget=revenue_budget,
        variable_budget=variable_budget,
        total_fixed=total_fixed,
        stock_value=stock_value,
        annual_dre=annual_dre,
        scenario_result=scenario_result,
    )


if __name__ == "__main__":
    app.run(debug=True)
