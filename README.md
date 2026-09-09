# (Flask + Supabase)

ระบบมี 3 บทบาท: **ผู้ซื้อ**, **ผู้ขาย**, **แอดมิน**

## ขั้นตอนติดตั้ง

### 1. ตั้งค่า Supabase

1. สร้างโปรเจคใหม่ที่ [supabase.com](https://supabase.com)
2. ไปที่ **SQL Editor** แล้วรันไฟล์ `schema.sql` ทั้งหมด (จะสร้างตาราง, RLS policies, และข้อมูลหมวดหมู่ตัวอย่าง)
3. ไปที่ **Storage** → สร้าง bucket ใหม่ชื่อ `product-images` ตั้งเป็น **Public bucket**
4. ไปที่ **Project Settings → API**

### 2. ตั้งค่าโปรเจค

```bash
# สร้าง virtual environment
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# ติดตั้ง dependencies
pip install -r requirements.txt

# คัดลอกไฟล์ env แล้วใส่ค่าจริง
cp .env.example .env


### 3. สร้างบัญชีแอดมิน

ตอนสมัครสมาชิกทั่วไป ระบบจะให้เลือกได้แค่ "ผู้ซื้อ" หรือ "ผู้ขาย" เท่านั้น
สำหรับบัญชีแอดมิน ให้:
1. สมัครสมาชิกปกติ 1 บัญชีก่อน (เลือกอะไรก็ได้)
2. ไปที่ Supabase → **Table Editor** → ตาราง `profiles`
3. แก้ไข column `role` ของ user นั้นเป็น `admin`

### 4. รันโปรเจค

```bash
python run.py
```

เปิดเบราว์เซอร์ไปที่ `http://localhost:5000`

## โครงสร้างโปรเจค

```
shopclone/
├── run.py                     # entry point
├── config.py                  # การตั้งค่า (อ่านจาก .env)
├── schema.sql                 # SQL สำหรับสร้างตารางใน Supabase
├── requirements.txt
├── .env.example
└── app/
    ├── __init__.py             # Flask app factory
    ├── supabase_client.py      # Supabase client (anon + admin)
    ├── auth_utils.py           # session helpers, login_required, role_required
    ├── blueprints/
    │   ├── auth/routes.py      # สมัคร, ล็อกอิน, ล็อกเอาท์
    │   ├── buyer/routes.py     # หน้าแรก, สินค้า, ตะกร้า, สั่งซื้อ, รีวิว
    │   ├── seller/routes.py    # แดชบอร์ด, จัดการสินค้า, คำสั่งซื้อ
    │   └── admin/routes.py     # อนุมัติ/ลบสินค้า
    ├── templates/               # Jinja2 + Tailwind CSS
    └── static/
```
```
###ขอบคุณครับครูนัท
```

