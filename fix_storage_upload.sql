-- ============================================================
-- แก้ปัญหา: อัปโหลดรูปภาพสินค้าไม่ได้ (storage upload error)
-- สาเหตุ: bucket แบบ Public อนุญาตแค่ "ดู" รูป แต่ไม่ได้อนุญาต "อัปโหลด"
-- ต้องสร้าง policy ให้ storage.objects แยกต่างหาก
-- ============================================================

-- อนุญาตให้ผู้ใช้ที่ล็อกอินแล้ว (authenticated) อัปโหลดไฟล์เข้า bucket นี้ได้
create policy "Authenticated users can upload product images"
on storage.objects for insert
to authenticated
with check (bucket_id = 'product-images');

-- อนุญาตให้ทุกคนดูรูปได้ (เพราะตั้ง bucket เป็น public ไว้อยู่แล้ว แต่ใส่ policy ให้ชัดเจน)
create policy "Anyone can view product images"
on storage.objects for select
using (bucket_id = 'product-images');

-- อนุญาตให้ผู้ใช้ที่ล็อกอินแล้วแก้ไข/ลบไฟล์ในนี้ได้ (สำหรับตอนแก้ไข/ลบสินค้า)
create policy "Authenticated users can update product images"
on storage.objects for update
to authenticated
using (bucket_id = 'product-images');

create policy "Authenticated users can delete product images"
on storage.objects for delete
to authenticated
using (bucket_id = 'product-images');
