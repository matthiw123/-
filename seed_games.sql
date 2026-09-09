-- ============================================================
-- SEED DATA: เพิ่มเกม 50 เกมเข้าระบบ (ไม่มีรูปภาพ ไปเพิ่มเองทีหลังได้)
-- ทุกเกมตั้งสถานะเป็น "approved" ทันที ไม่ต้องรอแอดมินอนุมัติ
-- ============================================================
-- ข้อกำหนด: ต้องมีบัญชีผู้ขาย (role = 'seller') อย่างน้อย 1 บัญชีในระบบก่อน
-- สคริปต์นี้จะหยิบผู้ขายคนแรกที่สมัครไว้มาเป็นเจ้าของสินค้าทั้งหมดโดยอัตโนมัติ
-- ============================================================

with seller as (
  select id from profiles where role = 'seller' order by created_at asc limit 1
)
insert into products (seller_id, name, description, price, stock, condition, status)
select seller.id, v.name, v.description, v.price, v.stock, v.condition::product_condition, 'approved'
from seller, (values
  ('Persona 3 Portable (Steam)', 'JRPG จาก Atlus ผสมผสานชีวิตนักเรียนกับการต่อสู้ Shadow ในดันเจี้ยน Tartarus', 590, 25, 'new'),
  ('Persona 4 Golden (Steam)', 'ภาคต่อของซีรีส์ Persona เนื้อเรื่องสืบสวนฆาตกรรมในเมืองชนบท พร้อมระบบ Social Link', 590, 20, 'new'),
  ('Persona 3 Reload (Steam)', 'รีเมคเต็มรูปแบบของ Persona 3 กราฟิกและระบบต่อสู้ปรับใหม่ทั้งหมด', 1690, 15, 'new'),
  ('Red Dead Redemption 2 (Steam)', 'เกมโลกเปิดยุคตะวันตกเถื่อนจาก Rockstar Games เนื้อเรื่องเข้มข้นระดับรางวัล', 990, 18, 'used'),
  ('Persona 5 Royal (Steam)', 'ภาคสมบูรณ์ของ Persona 5 พร้อมตัวละครและเนื้อเรื่องเพิ่มเติม', 1290, 22, 'new'),
  ('The Witcher 3: Wild Hunt (Steam)', 'เกม RPG โลกเปิดจาก CD Projekt Red รับบทนักล่าปีศาจเกรอลต์', 490, 30, 'used'),
  ('Elden Ring (Steam)', 'เกมแอคชัน RPG โลกเปิดจาก FromSoftware ร่วมกับ George R.R. Martin', 1990, 12, 'new'),
  ('Dark Souls III (Steam)', 'เกมแอคชัน RPG สุดโหดจาก FromSoftware', 690, 15, 'used'),
  ('Hollow Knight (Steam)', 'เกม Metroidvania วาดมือ โลกใต้ดินอันกว้างใหญ่ของอาณาจักรแมลง', 259, 40, 'new'),
  ('Stardew Valley (Steam)', 'เกมทำฟาร์มพิกเซลอาร์ตสุดผ่อนคลาย ปลูกพืช เลี้ยงสัตว์ ผูกมิตร', 199, 50, 'new'),
  ('Terraria (Steam)', 'เกมผจญภัยขุดสร้างโลก 2D สุดคลาสสิก', 179, 35, 'used'),
  ('Minecraft (Steam)', 'เกมสร้างโลกบล็อกที่โด่งดังที่สุดในโลก', 699, 28, 'new'),
  ('Grand Theft Auto V (Steam)', 'เกมโลกเปิดอาชญากรรมจาก Rockstar Games', 599, 33, 'used'),
  ('Cyberpunk 2077 (Steam)', 'เกม RPG โลกอนาคตไซไฟจาก CD Projekt Red', 890, 20, 'new'),
  ('God of War (Steam)', 'แอคชันผจญภัยตำนานเทพเจ้านอร์ส รับบทเครโตสและแอทเทรียส', 1290, 16, 'new'),
  ('Sekiro: Shadows Die Twice (Steam)', 'เกมแอคชันซามูไรสุดโหดจาก FromSoftware', 890, 14, 'used'),
  ('Hades (Steam)', 'เกม Roguelike แอคชันธีมเทพนิยายกรีก จาก Supergiant Games', 459, 27, 'new'),
  ('Celeste (Steam)', 'เกมแพลตฟอร์มปีนเขาสุดหิน เนื้อเรื่องอบอุ่นหัวใจ', 299, 32, 'new'),
  ('Portal 2 (Steam)', 'เกมไขปริศนามิติพอร์ทัลสุดคลาสสิกจาก Valve', 199, 38, 'used'),
  ('Half-Life: Alyx (Steam)', 'เกม VR สุดล้ำในจักรวาล Half-Life', 1390, 10, 'new'),
  ('Counter-Strike 2 (Steam)', 'เกมยิงปืนทีมแข่งขันระดับตำนาน', 0, 100, 'new'),
  ('Dota 2 (Steam)', 'เกม MOBA แข่งขันชื่อดังระดับโลก', 0, 100, 'new'),
  ('Apex Legends (Steam)', 'เกมยิงปืน Battle Royale ทีมฮีโร่', 0, 100, 'new'),
  ('Baldur''s Gate 3 (Steam)', 'เกม RPG แฟนตาซีเทิร์นเบสระดับรางวัลเกมแห่งปี', 1590, 17, 'new'),
  ('Divinity: Original Sin 2 (Steam)', 'เกม RPG แฟนตาซีเทิร์นเบสจาก Larian Studios', 890, 13, 'used'),
  ('Disco Elysium (Steam)', 'เกม RPG แนวสืบสวนบทสนทนาล้วน เนื้อเรื่องลึกซึ้ง', 690, 19, 'new'),
  ('Hollow Knight: Silksong (Steam)', 'ภาคต่อของ Hollow Knight รับบทฮอร์เน็ตนักล่า', 590, 24, 'new'),
  ('Monster Hunter: World (Steam)', 'เกมล่ามอนสเตอร์ยักษ์ร่วมมือกับเพื่อน', 790, 21, 'used'),
  ('Resident Evil 4 Remake (Steam)', 'รีเมคเกมสยองขวัญเอาชีวิตรอดระดับตำนาน', 1290, 18, 'new'),
  ('Silent Hill 2 Remake (Steam)', 'รีเมคเกมสยองขวัญจิตวิทยาสุดคลาสสิก', 1590, 11, 'new'),
  ('Dead Space Remake (Steam)', 'รีเมคเกมสยองขวัญไซไฟอวกาศ', 990, 15, 'used'),
  ('Doom Eternal (Steam)', 'เกมยิงมันส์ปีศาจนรกสุดดุเดือด', 690, 22, 'new'),
  ('Devil May Cry 5 (Steam)', 'เกมแอคชันฟันคอมโบสุดมันส์', 890, 16, 'used'),
  ('Bayonetta (Steam)', 'เกมแอคชันแม่มดสุดเท่ ฟันคอมโบลื่นไหล', 590, 20, 'new'),
  ('Nier: Automata (Steam)', 'เกมแอคชัน RPG หุ่นยนต์สุดเมโลดราม่า', 890, 17, 'used'),
  ('Persona 5 Strikers (Steam)', 'สปินออฟแอคชันของซีรีส์ Persona 5', 990, 14, 'new'),
  ('Yakuza: Like a Dragon (Steam)', 'เกม RPG แนวยากูซ่าปรับระบบต่อสู้เป็นเทิร์นเบส', 890, 15, 'used'),
  ('Final Fantasy VII Remake (Steam)', 'รีเมคเกม RPG ตำนาน Final Fantasy VII', 1690, 13, 'new'),
  ('Final Fantasy XVI (Steam)', 'เกม RPG แอคชันภาคล่าสุดของซีรีส์ Final Fantasy', 1990, 9, 'new'),
  ('Octopath Traveler II (Steam)', 'เกม RPG พิกเซลอาร์ตย้อนยุค 8 เส้นเรื่องราว', 1490, 12, 'new'),
  ('Chrono Trigger (Steam)', 'เกม RPG ย้อนเวลาสุดคลาสสิกในตำนาน', 490, 25, 'used'),
  ('Undertale (Steam)', 'เกม RPG อินดี้สุดฮิต เลือกได้ทั้งสู้และไม่ฆ่า', 199, 30, 'new'),
  ('Cuphead (Steam)', 'เกมแอคชันบอสรัชวาดมือสไตล์การ์ตูนยุค 1930', 259, 26, 'new'),
  ('It Takes Two (Steam)', 'เกมผจญภัยสองผู้เล่นร่วมมือกันแก้ปริศนา', 599, 19, 'used'),
  ('Portal (Steam)', 'เกมไขปริศนามิติพอร์ทัลภาคแรก', 99, 40, 'new'),
  ('Left 4 Dead 2 (Steam)', 'เกมยิงซอมบี้ร่วมมือสี่คนสุดคลาสสิก', 199, 28, 'used'),
  ('Team Fortress 2 (Steam)', 'เกมยิงปืนทีมสไตล์การ์ตูนสุดฮิต', 0, 100, 'new'),
  ('Rocket League (Steam)', 'เกมฟุตบอลรถยนต์สุดมันส์', 0, 100, 'new'),
  ('Slay the Spire (Steam)', 'เกม Roguelike การ์ดต่อสู้สุดเสพติด', 259, 22, 'new'),
  ('Balatro (Steam)', 'เกมไพ่โป๊กเกอร์ Roguelike สุดเสพติดแห่งปี', 259, 30, 'new')
) as v(name, description, price, stock, condition);
