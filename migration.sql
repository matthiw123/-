-- ============================================================
-- MIGRATION: เกม (มือ1/มือสอง) + รีวิวแบบ Steam + ล็อกอินด้วยชื่อ
-- รันไฟล์นี้ต่อจาก schema.sql เดิม (ไม่ลบตาราง/ข้อมูลเดิม)
-- ============================================================

-- 1) เพิ่มสถานะสินค้า: มือ1 (new) / มือสอง (used)
create type product_condition as enum ('new', 'used');
alter table products add column condition product_condition not null default 'used';

-- 2) เก็บ email ไว้ใน profiles ด้วย (เพื่อให้ล็อกอินด้วย "ชื่อ" ได้)
alter table profiles add column email text;
update profiles p set email = u.email from auth.users u where p.id = u.id and p.email is null;

-- อัปเดต trigger ให้บันทึก email ทุกครั้งที่มีผู้ใช้ใหม่สมัคร
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name, role, email)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', ''), 'buyer', new.email);
  return new;
end;
$$ language plpgsql security definer;

-- 3) รีวิวแบบ Steam: เปลี่ยนจากให้ดาว 1-5 เป็น "แนะนำ / ไม่แนะนำ"
alter table reviews alter column rating drop not null;
alter table reviews drop constraint if exists reviews_rating_check;
alter table reviews add column recommended boolean not null default true;

-- ============================================================
-- หมายเหตุสำหรับหมวดหมู่เกม (categories):
-- ไม่ต้องแก้ schema เพราะตาราง categories ใช้ร่วมกันได้อยู่แล้ว
-- ไปที่ Supabase > Table Editor > categories แล้วแก้ชื่อ/เพิ่มแถวเป็น
-- ประเภทเกมแทนได้เลย เช่น Action, RPG, Sports, Indie, Horror
-- ============================================================
