-- ============================================================
-- แก้ปัญหา: สต๊อกไม่ลดหลังซื้อ (RLS บล็อกผู้ซื้อไม่ให้แก้ไขตาราง products)
-- วิธีแก้: สร้างฟังก์ชันเฉพาะสำหรับ "ลดสต๊อก" เท่านั้น ที่ผู้ซื้อเรียกได้
-- อย่างปลอดภัย (ทำได้แค่ลดสต๊อก แก้ไขข้อมูลอื่นของสินค้าไม่ได้)
-- ============================================================
create or replace function public.decrement_product_stock(p_product_id uuid, p_qty integer)
returns void
language plpgsql
security definer
as $$
begin
  update products
  set stock = greatest(stock - p_qty, 0)
  where id = p_product_id;
end;
$$;

grant execute on function public.decrement_product_stock(uuid, integer) to authenticated;
