# ShopClone — โปรเจคเว็บขายของออนไลน์ (Flask + Supabase)

ระบบมี 3 บทบาท: **ผู้ซื้อ**, **ผู้ขาย**, **แอดมิน**

## ฟีเจอร์

- **ผู้ซื้อ**: สมัคร/ล็อกอิน · เบราว์ส+ค้นหา+filter สินค้า (หมวดหมู่, ช่วงราคา) · หน้ารายละเอียดสินค้า · ตะกร้าสินค้า · สั่งซื้อ (checkout จำลอง) · ติดตามสถานะคำสั่งซื้อ · รีวิว+ให้คะแนนสินค้า
- **ผู้ขาย**: เพิ่ม/แก้ไข/ลบสินค้า (พร้อมอัปโหลดรูป, สต๊อก) · แดชบอร์ด (ยอดขาย, จำนวนสินค้า) · จัดการสถานะคำสั่งซื้อ
- **แอดมิน**: อนุมัติ/ปฏิเสธสินค้าที่ผู้ขายเพิ่มเข้ามาก่อนขึ้นแสดงจริง · ลบสินค้าได้

## ขั้นตอนติดตั้ง

### 1. ตั้งค่า Supabase

1. สร้างโปรเจคใหม่ที่ [supabase.com](https://supabase.com)
2. ไปที่ **SQL Editor** แล้วรันไฟล์ `schema.sql` ทั้งหมด (จะสร้างตาราง, RLS policies, และข้อมูลหมวดหมู่ตัวอย่าง)
3. ไปที่ **Storage** → สร้าง bucket ใหม่ชื่อ `product-images` ตั้งเป็น **Public bucket**
4. ไปที่ **Project Settings → API** คัดลอกค่า:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_KEY` (⚠️ เก็บเป็นความลับ ห้าม commit ขึ้น git)

### 2. ตั้งค่าโปรเจค

```bash
# สร้าง virtual environment
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# ติดตั้ง dependencies
pip install -r requirements.txt

# คัดลอกไฟล์ env แล้วใส่ค่าจริง
cp .env.example .env
# แก้ไข .env ให้ใส่ SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
```

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

## หมายเหตุ

- ระบบชำระเงินเป็น**การจำลอง** (ยืนยันคำสั่งซื้อ = ถือว่าชำระเงินสำเร็จทันที) — ถ้าต้องการของจริงค่อยต่อ payment gateway เพิ่ม
- สินค้าที่ผู้ขายเพิ่ม/แก้ไข จะมีสถานะ `pending` เสมอ ต้องรอแอดมินกด "อนุมัติ" ก่อนถึงจะแสดงในหน้าร้าน
- RLS (Row Level Security) ถูกตั้งไว้ใน `schema.sql` แล้ว เพื่อไม่ให้ผู้ใช้ query/แก้ไขข้อมูลข้ามสิทธิ์กันได้
