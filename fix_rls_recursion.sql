-- ============================================================
-- แก้ปัญหา: infinite recursion detected in policy for relation "order_items"
-- สาเหตุ: policy ของ orders กับ order_items เช็คสิทธิ์อ้างอิงกันไปมา
-- วิธีแก้: สร้างฟังก์ชันแบบ SECURITY DEFINER เพื่อตัดวงจรการอ้างอิงกัน
-- ============================================================

-- ฟังก์ชันนี้จะข้าม RLS ตอนเช็ค (ทำงานด้วยสิทธิ์ผู้สร้างฟังก์ชัน)
-- จึงไม่ทำให้เกิดการเรียก policy ของ order_items ซ้ำ
create or replace function public.is_order_seller(target_order_id uuid)
returns boolean
language sql
security definer
stable
as $$
  select exists (
    select 1 from order_items
    where order_id = target_order_id and seller_id = auth.uid()
  );
$$;

-- แก้ policy ของ orders ให้เรียกใช้ฟังก์ชันแทนการ query order_items ตรงๆ
drop policy if exists "Buyers view their own orders" on orders;
create policy "Buyers view their own orders"
  on orders for select using (
    buyer_id = auth.uid()
    or exists (select 1 from profiles where id = auth.uid() and role = 'admin')
    or public.is_order_seller(id)
  );
