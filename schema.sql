-- ============================================================
-- SHOPCLONE DATABASE SCHEMA (for Supabase / PostgreSQL)
-- ============================================================
-- Run this in the Supabase SQL Editor.
-- Supabase already provides `auth.users` for authentication.
-- We extend it with a `profiles` table that stores app-specific
-- data (role, name, etc.) linked 1:1 to auth.users.
-- ============================================================

-- Enable UUID generation (usually already enabled on Supabase)
create extension if not exists "pgcrypto";

-- ============================================================
-- 1. PROFILES  (extends Supabase auth.users)
-- ============================================================
create type user_role as enum ('buyer', 'seller', 'admin');

create table profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    full_name text not null,
    role user_role not null default 'buyer',
    shop_name text,               -- only used when role = 'seller'
    phone text,
    created_at timestamptz not null default now()
);

-- Automatically create a profile row when a new auth user signs up
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name, role)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', ''), 'buyer');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ============================================================
-- 2. CATEGORIES
-- ============================================================
create table categories (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    created_at timestamptz not null default now()
);

-- ============================================================
-- 3. PRODUCTS
-- ============================================================
create type product_status as enum ('pending', 'approved', 'rejected');

create table products (
    id uuid primary key default gen_random_uuid(),
    seller_id uuid not null references profiles(id) on delete cascade,
    category_id uuid references categories(id) on delete set null,
    name text not null,
    description text,
    price numeric(12,2) not null check (price >= 0),
    stock integer not null default 0 check (stock >= 0),
    status product_status not null default 'pending',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index idx_products_status on products(status);
create index idx_products_seller on products(seller_id);
create index idx_products_category on products(category_id);

-- ============================================================
-- 4. PRODUCT IMAGES  (a product can have multiple photos)
-- ============================================================
create table product_images (
    id uuid primary key default gen_random_uuid(),
    product_id uuid not null references products(id) on delete cascade,
    image_url text not null,
    sort_order integer not null default 0
);

-- ============================================================
-- 5. CART ITEMS
-- ============================================================
create table cart_items (
    id uuid primary key default gen_random_uuid(),
    buyer_id uuid not null references profiles(id) on delete cascade,
    product_id uuid not null references products(id) on delete cascade,
    quantity integer not null default 1 check (quantity > 0),
    created_at timestamptz not null default now(),
    unique (buyer_id, product_id)
);

-- ============================================================
-- 6. ORDERS
-- ============================================================
create type order_status as enum (
    'pending', 'paid', 'shipped', 'delivered', 'cancelled'
);

create table orders (
    id uuid primary key default gen_random_uuid(),
    buyer_id uuid not null references profiles(id) on delete cascade,
    status order_status not null default 'pending',
    total_amount numeric(12,2) not null default 0,
    shipping_address text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- ============================================================
-- 7. ORDER ITEMS
-- ============================================================
create table order_items (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references orders(id) on delete cascade,
    product_id uuid not null references products(id),
    seller_id uuid not null references profiles(id),  -- denormalized for seller dashboard queries
    quantity integer not null check (quantity > 0),
    unit_price numeric(12,2) not null,   -- price at time of purchase
    created_at timestamptz not null default now()
);

create index idx_order_items_order on order_items(order_id);
create index idx_order_items_seller on order_items(seller_id);

-- ============================================================
-- 8. REVIEWS
-- ============================================================
create table reviews (
    id uuid primary key default gen_random_uuid(),
    product_id uuid not null references products(id) on delete cascade,
    buyer_id uuid not null references profiles(id) on delete cascade,
    order_item_id uuid references order_items(id),  -- proves the buyer actually bought it
    rating integer not null check (rating between 1 and 5),
    comment text,
    created_at timestamptz not null default now(),
    unique (buyer_id, product_id)  -- one review per product per buyer
);

create index idx_reviews_product on reviews(product_id);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================
alter table profiles enable row level security;
alter table products enable row level security;
alter table product_images enable row level security;
alter table cart_items enable row level security;
alter table orders enable row level security;
alter table order_items enable row level security;
alter table reviews enable row level security;
alter table categories enable row level security;

-- ---- profiles ----
create policy "Profiles are viewable by everyone"
  on profiles for select using (true);
create policy "Users can update their own profile"
  on profiles for update using (auth.uid() = id);

-- ---- categories ----
create policy "Categories are viewable by everyone"
  on categories for select using (true);
create policy "Admins manage categories"
  on categories for all using (
    exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );

-- ---- products ----
create policy "Approved products are viewable by everyone"
  on products for select using (
    status = 'approved'
    or seller_id = auth.uid()
    or exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );
create policy "Sellers insert their own products"
  on products for insert with check (
    seller_id = auth.uid()
    and exists (select 1 from profiles where id = auth.uid() and role = 'seller')
  );
create policy "Sellers update their own products"
  on products for update using (seller_id = auth.uid());
create policy "Admins update any product"
  on products for update using (
    exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );
create policy "Admins delete any product"
  on products for delete using (
    exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );

-- ---- product_images ----
create policy "Product images viewable by everyone"
  on product_images for select using (true);
create policy "Sellers manage images of their own products"
  on product_images for all using (
    exists (select 1 from products p where p.id = product_id and p.seller_id = auth.uid())
  );

-- ---- cart_items ----
create policy "Buyers manage their own cart"
  on cart_items for all using (buyer_id = auth.uid());

-- ---- orders ----
create policy "Buyers view their own orders"
  on orders for select using (
    buyer_id = auth.uid()
    or exists (select 1 from profiles where id = auth.uid() and role = 'admin')
    or exists (
      select 1 from order_items oi
      where oi.order_id = orders.id and oi.seller_id = auth.uid()
    )
  );
create policy "Buyers create their own orders"
  on orders for insert with check (buyer_id = auth.uid());

-- ---- order_items ----
create policy "Order items viewable by buyer, seller, or admin"
  on order_items for select using (
    exists (select 1 from orders o where o.id = order_id and o.buyer_id = auth.uid())
    or seller_id = auth.uid()
    or exists (select 1 from profiles where id = auth.uid() and role = 'admin')
  );
create policy "Buyers create order items via their own order"
  on order_items for insert with check (
    exists (select 1 from orders o where o.id = order_id and o.buyer_id = auth.uid())
  );
create policy "Sellers update status of their own order items"
  on order_items for update using (seller_id = auth.uid());

-- ---- reviews ----
create policy "Reviews are viewable by everyone"
  on reviews for select using (true);
create policy "Buyers create their own reviews"
  on reviews for insert with check (buyer_id = auth.uid());
create policy "Buyers update their own reviews"
  on reviews for update using (buyer_id = auth.uid());

-- ============================================================
-- SEED DATA (optional, for quick testing)
-- ============================================================
insert into categories (name) values
  ('เสื้อผ้า'), ('อิเล็กทรอนิกส์'), ('ของใช้ในบ้าน'), ('ความงาม'), ('อาหาร');
