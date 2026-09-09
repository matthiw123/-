"""
ตัวช่วยสร้าง Supabase client
- get_supabase(): client แบบ anon key (ใช้สิทธิ์ตาม RLS ของผู้ใช้ทั่วไป)
- get_supabase_admin(): client แบบ service key (ข้าม RLS ได้ทั้งหมด — ใช้เฉพาะฝั่ง server
  สำหรับงานที่แอดมินต้องทำ เช่น อนุมัติ/ลบสินค้า อย่า expose key นี้ไปฝั่ง client เด็ดขาด)
"""
from supabase import create_client, Client
from flask import current_app, g, session


def get_supabase() -> Client:
    if "supabase" not in g:
        g.supabase = create_client(
            current_app.config["SUPABASE_URL"],
            current_app.config["SUPABASE_ANON_KEY"],
        )
        # ผูก access_token ของผู้ใช้ที่ล็อกอินอยู่ (ถ้ามี) เข้ากับ client
        # เพื่อให้ RLS policy ที่เช็ค auth.uid() ทำงานถูกต้อง
        # (ต้องผูกทั้ง postgrest สำหรับตาราง และ storage สำหรับไฟล์รูปภาพ แยกกัน)
        token = session.get("access_token")
        if token:
            g.supabase.postgrest.auth(token)
            g.supabase.storage._client.headers["Authorization"] = f"Bearer {token}"
    return g.supabase


def get_supabase_admin() -> Client:
    if "supabase_admin" not in g:
        g.supabase_admin = create_client(
            current_app.config["SUPABASE_URL"],
            current_app.config["SUPABASE_SERVICE_KEY"],
        )
    return g.supabase_admin
