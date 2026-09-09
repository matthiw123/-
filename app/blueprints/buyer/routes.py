import random
import string
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.supabase_client import get_supabase
from app.auth_utils import login_required, current_user

bp = Blueprint("buyer", __name__, url_prefix="")


def generate_fake_code():
    """สร้างโค้ดยืนยันเกมแบบจำลอง (ไม่ใช่โค้ดจริงที่ใช้แลกเกมได้)"""
    part = lambda: "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{part()}-{part()}-{part()}"


def effective_price(product):
    """คืนราคาหลังหักส่วนลด (ถ้ามี)"""
    if not product:
        return 0
    discount = product.get("discount_percent") or 0
    return round(product["price"] * (1 - discount / 100), 2)


@bp.route("/api/search-suggest")
def search_suggest():
    """คืนรายชื่อเกมที่ตรงกับคำค้นหา สำหรับ dropdown อัตโนมัติในช่องค้นหา"""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    supabase = get_supabase()
    results = supabase.table("products").select(
        "id, name, price, product_images(image_url, is_cover)"
    ).eq("status", "approved").ilike("name", f"%{q}%").limit(8).execute().data

    suggestions = []
    for p in results:
        img = cover_image_helper(p.get("product_images"))
        suggestions.append({
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "image_url": img["image_url"] if img else None,
        })
    return jsonify(suggestions)


def cover_image_helper(images):
    if not images:
        return None
    for img in images:
        if img.get("is_cover"):
            return img
    return images[0]


@bp.route("/")
def home():
    supabase = get_supabase()
    query = supabase.table("products").select(
        "*, categories(name), product_images(image_url, is_cover)"
    ).eq("status", "approved")

    keyword = request.args.get("q")
    category_id = request.args.get("category")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    condition = request.args.get("condition")  # 'new' หรือ 'used'

    if keyword:
        query = query.ilike("name", f"%{keyword}%")
    if category_id:
        query = query.eq("category_id", category_id)
    if min_price:
        query = query.gte("price", min_price)
    if max_price:
        query = query.lte("price", max_price)
    if condition:
        query = query.eq("condition", condition)

    products = query.order("created_at", desc=True).execute().data
    categories = supabase.table("categories").select("*").execute().data
    best_sellers = get_best_sellers(supabase, limit=8)

    # เลือกเกมเด่นสำหรับ hero banner หน้าแรก (เอาที่มีรูปมาก่อน)
    featured = None
    candidates = [b["product"] for b in best_sellers] or products
    for p in candidates:
        if p.get("product_images"):
            featured = p
            break

    return render_template(
        "buyer/home.html", products=products, categories=categories,
        best_sellers=best_sellers, featured=featured
    )


def get_best_sellers(supabase, limit=8):
    """คำนวณเกมขายดีจากยอดขายรวมใน order_items"""
    order_items = supabase.table("order_items").select(
        "product_id, quantity, products(name, price, discount_percent, status, product_images(image_url, is_cover))"
    ).execute().data

    sales = {}
    for oi in order_items:
        p = oi.get("products")
        if not p or p.get("status") != "approved":
            continue
        pid = oi["product_id"]
        if pid not in sales:
            p["id"] = pid  # เผื่อไว้ใช้ทำลิงก์ (select ไม่ได้ดึง id ของ products มาโดยตรง)
            sales[pid] = {"product_id": pid, "sold": 0, "product": p}
        sales[pid]["sold"] += oi["quantity"]

    ranked = sorted(sales.values(), key=lambda x: x["sold"], reverse=True)
    return ranked[:limit]


@bp.route("/product/<product_id>")
def product_detail(product_id):
    supabase = get_supabase()
    product = supabase.table("products").select(
        "*, categories(name), product_images(image_url, is_cover), profiles(shop_name, full_name)"
    ).eq("id", product_id).single().execute().data

    reviews = supabase.table("reviews").select(
        "*, profiles(full_name)"
    ).eq("product_id", product_id).order("created_at", desc=True).execute().data

    total = len(reviews)
    positive = len([r for r in reviews if r["recommended"]])
    recommend_pct = round((positive / total) * 100) if total else None

    # เช็คว่าผู้ใช้ปัจจุบันซื้อสินค้านี้แล้วหรือยัง (รีวิวได้ต้องซื้อก่อน)
    can_review = False
    already_reviewed = False
    user = current_user()
    if user and user["role"] == "buyer":
        purchased = supabase.table("order_items").select(
            "id, orders!inner(buyer_id, status)"
        ).eq("product_id", product_id).eq("orders.buyer_id", user["id"]).execute().data
        can_review = len(purchased) > 0
        already_reviewed = any(r["buyer_id"] == user["id"] for r in reviews)

    return render_template(
        "buyer/product_detail.html", product=product, reviews=reviews,
        recommend_pct=recommend_pct, total_reviews=total,
        can_review=can_review, already_reviewed=already_reviewed
    )


@bp.route("/cart")
@login_required
def cart():
    supabase = get_supabase()
    items = supabase.table("cart_items").select(
        "*, products(name, price, discount_percent, stock, product_images(image_url, is_cover))"
    ).eq("buyer_id", session["user_id"]).execute().data

    # สินค้าบางชิ้นอาจถูกผู้ขายแก้ไข ทำให้สถานะกลับไปเป็น "รอตรวจสอบ" ชั่วคราว
    # ระบบจะมองไม่เห็นสินค้านั้น (products เป็น None) ต้องกรองออกจากการคำนวณ
    available_items = [item for item in items if item.get("products")]
    unavailable_count = len(items) - len(available_items)
    total = sum(item["quantity"] * effective_price(item["products"]) for item in available_items)

    return render_template(
        "buyer/cart.html", items=available_items, total=total,
        unavailable_count=unavailable_count
    )


@bp.route("/cart/add/<product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    supabase = get_supabase()
    qty = int(request.form.get("quantity", 1))

    existing = supabase.table("cart_items").select("*").eq(
        "buyer_id", session["user_id"]
    ).eq("product_id", product_id).execute().data

    if existing:
        new_qty = existing[0]["quantity"] + qty
        supabase.table("cart_items").update({"quantity": new_qty}).eq(
            "id", existing[0]["id"]
        ).execute()
    else:
        supabase.table("cart_items").insert({
            "buyer_id": session["user_id"],
            "product_id": product_id,
            "quantity": qty,
        }).execute()

    flash("เพิ่มลงตะกร้าแล้ว", "success")
    return redirect(url_for("buyer.product_detail", product_id=product_id, added=1))


@bp.route("/cart/remove/<item_id>", methods=["POST"])
@login_required
def remove_from_cart(item_id):
    supabase = get_supabase()
    supabase.table("cart_items").delete().eq("id", item_id).eq(
        "buyer_id", session["user_id"]
    ).execute()
    return redirect(url_for("buyer.cart"))


@bp.route("/cart/update/<item_id>", methods=["POST"])
@login_required
def update_cart_quantity(item_id):
    """ปุ่ม +/- ปรับจำนวนสินค้าในตะกร้า"""
    supabase = get_supabase()
    delta = int(request.form.get("delta", 0))

    item = supabase.table("cart_items").select("*, products(stock)").eq(
        "id", item_id
    ).eq("buyer_id", session["user_id"]).single().execute().data

    if item:
        max_stock = item["products"]["stock"] if item.get("products") else 99
        new_qty = item["quantity"] + delta
        new_qty = max(1, min(new_qty, max_stock))
        supabase.table("cart_items").update({"quantity": new_qty}).eq("id", item_id).execute()

    return redirect(url_for("buyer.cart"))


@bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    supabase = get_supabase()

    if request.method == "POST":
        payment_method = request.form.get("payment_method")
        payment_code = request.form.get("payment_code", "").strip()

        if payment_method not in ("truemoney", "promptpay"):
            flash("กรุณาเลือกวิธีชำระเงิน", "warning")
            return redirect(url_for("buyer.checkout"))
        if not (payment_code.isdigit() and len(payment_code) == 6):
            flash("กรุณากรอกรหัสยืนยัน 6 หลัก", "warning")
            return redirect(url_for("buyer.checkout"))
        # หมายเหตุ: payment_method/payment_code เป็นแค่การจำลอง ไม่ได้บันทึกเก็บไว้ที่ไหน

        items = supabase.table("cart_items").select(
            "*, products(price, discount_percent, stock, seller_id)"
        ).eq("buyer_id", session["user_id"]).execute().data

        items = [i for i in items if i.get("products")]  # กันสินค้าที่มองไม่เห็นชั่วคราว (รอตรวจสอบใหม่)

        if not items:
            flash("ตะกร้าว่างเปล่า หรือสินค้าในตะกร้าไม่พร้อมจำหน่ายแล้ว", "warning")
            return redirect(url_for("buyer.cart"))

        total = sum(i["quantity"] * effective_price(i["products"]) for i in items)

        order = supabase.table("orders").insert({
            "buyer_id": session["user_id"],
            "total_amount": total,
            "status": "paid",  # จำลองว่าชำระเงินสำเร็จทันที
        }).execute().data[0]

        for item in items:
            supabase.table("order_items").insert({
                "order_id": order["id"],
                "product_id": item["product_id"],
                "seller_id": item["products"]["seller_id"],
                "quantity": item["quantity"],
                "unit_price": effective_price(item["products"]),
                "activation_code": generate_fake_code(),
            }).execute()
            # ลดสต๊อกสินค้า (ใช้ฟังก์ชันเฉพาะ เพราะผู้ซื้อไม่มีสิทธิ์แก้ตาราง products ตรงๆ)
            supabase.rpc("decrement_product_stock", {
                "p_product_id": item["product_id"],
                "p_qty": item["quantity"],
            }).execute()

        supabase.table("cart_items").delete().eq(
            "buyer_id", session["user_id"]
        ).execute()

        flash("สั่งซื้อสำเร็จ!", "success")
        return redirect(url_for("buyer.order_history"))

    items = supabase.table("cart_items").select(
        "*, products(name, price, discount_percent)"
    ).eq("buyer_id", session["user_id"]).execute().data
    items = [i for i in items if i.get("products")]
    total = sum(i["quantity"] * effective_price(i["products"]) for i in items)
    return render_template("buyer/checkout.html", items=items, total=total)


@bp.route("/orders")
@login_required
def order_history():
    supabase = get_supabase()
    orders = supabase.table("orders").select(
        "*, order_items(*, activation_code, products(name, product_images(image_url, is_cover)))"
    ).eq("buyer_id", session["user_id"]).order("created_at", desc=True).execute().data
    return render_template("buyer/orders.html", orders=orders)


AVATAR_CHOICES = ["🎮", "👾", "🕹️", "🦸", "🐉", "🤖", "🧙", "🥷", "👑", "🔥", "⚔️", "🎯"]


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    supabase = get_supabase()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        avatar = request.form.get("avatar", "").strip()
        update_data = {}
        if full_name:
            update_data["full_name"] = full_name
        if avatar in AVATAR_CHOICES:
            update_data["avatar"] = avatar
        if session.get("role") == "seller":
            shop_name = request.form.get("shop_name", "").strip()
            if shop_name:
                update_data["shop_name"] = shop_name

        if update_data:
            supabase.table("profiles").update(update_data).eq("id", session["user_id"]).execute()
            # อัปเดต session ให้ตรงกับข้อมูลใหม่ทันที
            if "full_name" in update_data:
                session["full_name"] = update_data["full_name"]
            flash("บันทึกโปรไฟล์แล้ว", "success")
        return redirect(url_for("buyer.profile"))

    profile_data = supabase.table("profiles").select("*").eq(
        "id", session["user_id"]
    ).single().execute().data

    # เกม/โค้ดที่เคยซื้อทั้งหมด (เฉพาะคำสั่งซื้อที่จ่ายเงินแล้ว)
    purchased = supabase.table("order_items").select(
        "*, orders!inner(buyer_id, status, created_at), products(name, product_images(image_url, is_cover))"
    ).eq("orders.buyer_id", session["user_id"]).order("created_at", desc=True).execute().data

    return render_template(
        "buyer/profile.html", profile=profile_data, purchased=purchased,
        avatar_choices=AVATAR_CHOICES
    )


@bp.route("/review/<product_id>", methods=["POST"])
@login_required
def add_review(product_id):
    """รีวิวแบบ Steam: แนะนำ (👍) หรือ ไม่แนะนำ (👎) + คอมเมนต์ — ต้องซื้อสินค้านี้ก่อนถึงจะรีวิวได้"""
    supabase = get_supabase()

    purchased = supabase.table("order_items").select(
        "id, orders!inner(buyer_id)"
    ).eq("product_id", product_id).eq("orders.buyer_id", session["user_id"]).execute().data
    if not purchased:
        flash("ต้องซื้อเกมนี้ก่อนถึงจะรีวิวได้", "danger")
        return redirect(url_for("buyer.product_detail", product_id=product_id))

    recommended = request.form.get("recommended") == "yes"
    comment = request.form.get("comment", "")

    supabase.table("reviews").upsert({
        "product_id": product_id,
        "buyer_id": session["user_id"],
        "recommended": recommended,
        "comment": comment,
    }, on_conflict="buyer_id,product_id").execute()

    flash("ขอบคุณสำหรับรีวิว!", "success")
    return redirect(url_for("buyer.product_detail", product_id=product_id))
