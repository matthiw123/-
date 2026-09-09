-- ============================================================
-- MIGRATION: เพิ่มรูปปก (cover image) แยกจากรูปอื่นๆ ของสินค้า
-- ============================================================
alter table product_images add column is_cover boolean not null default false;
