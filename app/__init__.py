from flask import Flask
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.blueprints.auth.routes import bp as auth_bp
    from app.blueprints.buyer.routes import bp as buyer_bp
    from app.blueprints.seller.routes import bp as seller_bp
    from app.blueprints.admin.routes import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(buyer_bp)
    app.register_blueprint(seller_bp)
    app.register_blueprint(admin_bp)

    from app.auth_utils import current_user

    @app.context_processor
    def inject_user():
        return {"current_user": current_user()}

    @app.template_global()
    def cover_image(images):
        """คืนรูปปกของสินค้า (หรือรูปแรกถ้าไม่มีรูปปกที่ระบุไว้) หรือ None ถ้าไม่มีรูปเลย"""
        if not images:
            return None
        for img in images:
            if img.get("is_cover"):
                return img
        return images[0]

    @app.template_global()
    def effective_price(product):
        """คืนราคาหลังหักส่วนลด (ถ้ามี)"""
        if not product:
            return 0
        discount = product.get("discount_percent") or 0
        return round(product["price"] * (1 - discount / 100), 2)

    @app.template_global()
    def youtube_embed_url(url):
        """แปลงลิงก์ YouTube รูปแบบต่างๆ ให้เป็นลิงก์สำหรับฝัง iframe คืนค่า None ถ้าไม่ใช่ลิงก์ YouTube"""
        if not url:
            return None
        import re
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([\w-]{11})"
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return f"https://www.youtube.com/embed/{match.group(1)}"
        return None

    return app
