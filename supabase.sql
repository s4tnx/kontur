-- Контур Дома · настройка базы для общего кабинета
-- Выполните этот скрипт целиком в Supabase → SQL Editor → New query → Run.

-- 1. Профили: имя, телефон и роль (client / manager / admin)
create table if not exists public.profiles(
  id uuid primary key references auth.users on delete cascade,
  name text,
  phone text,
  role text not null default 'client',
  created_at timestamptz default now()
);
alter table public.profiles enable row level security;

-- вспомогательная функция: сотрудник ли текущий пользователь
create or replace function public.is_staff() returns boolean
language sql security definer set search_path = public as $$
  select exists(select 1 from public.profiles where id = auth.uid() and role in ('manager','admin'));
$$;

drop policy if exists "profile read" on public.profiles;
create policy "profile read" on public.profiles for select
  using (auth.uid() = id or public.is_staff());

drop policy if exists "profile insert self" on public.profiles;
create policy "profile insert self" on public.profiles for insert
  with check (auth.uid() = id);

-- менять можно только своё имя и телефон; роль остаётся прежней
drop policy if exists "profile update own" on public.profiles;
create policy "profile update own" on public.profiles for update
  using (auth.uid() = id)
  with check (auth.uid() = id and role = (select p.role from public.profiles p where p.id = auth.uid()));

-- 2. Заявки
create table if not exists public.orders(
  id bigint generated always as identity primary key,
  no text not null,
  user_id uuid default auth.uid() references auth.users on delete set null,
  fio text, phone text, email text, region text, comment text,
  items jsonb not null default '[]'::jsonb,
  total numeric default 0,
  stage int default 0,
  status text default 'new',
  created_at timestamptz default now()
);
-- промокод заявки: {"code":"…","pct":10}
alter table public.orders add column if not exists promo jsonb;
alter table public.orders enable row level security;

drop policy if exists "orders insert" on public.orders;
create policy "orders insert" on public.orders for insert with check (true);

drop policy if exists "orders read" on public.orders;
create policy "orders read" on public.orders for select
  using (auth.uid() = user_id or public.is_staff());

drop policy if exists "orders staff update" on public.orders;
create policy "orders staff update" on public.orders for update
  using (public.is_staff()) with check (public.is_staff());

-- удалить заявку: сотрудник — любую, клиент — свою до договора (документы удалятся каскадом)
drop policy if exists "orders delete" on public.orders;
create policy "orders delete" on public.orders for delete
  using (public.is_staff() or (auth.uid() = user_id and status in ('new','call','visit')));

-- 3. Документы по заявке (файлы лежат в хранилище, здесь — описание)
create table if not exists public.docs(
  id bigint generated always as identity primary key,
  order_id bigint references public.orders on delete cascade,
  name text, cat text, size int, by text, who text, path text,
  uploader uuid default auth.uid(),
  created_at timestamptz default now()
);
alter table public.docs enable row level security;

drop policy if exists "docs read" on public.docs;
create policy "docs read" on public.docs for select
  using (public.is_staff() or exists(select 1 from public.orders o where o.id = order_id and o.user_id = auth.uid()));

drop policy if exists "docs insert" on public.docs;
create policy "docs insert" on public.docs for insert
  with check (public.is_staff() or exists(select 1 from public.orders o where o.id = order_id and o.user_id = auth.uid()));

drop policy if exists "docs delete" on public.docs;
create policy "docs delete" on public.docs for delete
  using (public.is_staff() or uploader = auth.uid());

-- 3.1. Переписка по заявке: менеджер и клиент, фото хранятся прямо в сообщении
create table if not exists public.messages(
  id bigint generated always as identity primary key,
  order_id bigint references public.orders on delete cascade,
  role text, who text, text text,
  files jsonb not null default '[]'::jsonb,
  item jsonb,
  author uuid default auth.uid(),
  created_at timestamptz default now()
);
alter table public.messages enable row level security;

drop policy if exists "messages read" on public.messages;
create policy "messages read" on public.messages for select
  using (public.is_staff() or exists(select 1 from public.orders o where o.id = order_id and o.user_id = auth.uid()));

drop policy if exists "messages insert" on public.messages;
create policy "messages insert" on public.messages for insert
  with check (public.is_staff() or exists(select 1 from public.orders o where o.id = order_id and o.user_id = auth.uid()));

-- 4. Хранилище файлов (закрытое, ссылки выдаются на 2 минуты)
insert into storage.buckets(id, name, public) values ('docs','docs',false)
  on conflict (id) do nothing;

drop policy if exists "docs files read" on storage.objects;
create policy "docs files read" on storage.objects for select
  using (bucket_id = 'docs' and (public.is_staff() or exists(
    select 1 from public.docs d join public.orders o on o.id = d.order_id
    where d.path = name and o.user_id = auth.uid())));

drop policy if exists "docs files insert" on storage.objects;
create policy "docs files insert" on storage.objects for insert
  with check (bucket_id = 'docs' and auth.uid() is not null);

drop policy if exists "docs files delete" on storage.objects;
create policy "docs files delete" on storage.objects for delete
  using (bucket_id = 'docs' and public.is_staff());

-- 5. Как назначить сотрудника:
-- зарегистрируйтесь на сайте обычным способом, затем выполните запрос,
-- подставив свою почту:
-- update public.profiles set role = 'admin'
--   where id = (select id from auth.users where email = 'вашапочта@example.com');
