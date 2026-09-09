-- ============================================================
-- MIGRATION: เพิ่มระบบส่วนลดสินค้า (เลือกจากเปอร์เซ็นต์ที่กำหนดไว้)
-- ============================================================
alter table products add column discount_percent integer not null default 0
  check (discount_percent in (0, 5, 25, 30, 50, 70, 95));
