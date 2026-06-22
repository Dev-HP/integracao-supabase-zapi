-- Migração inicial: cria a tabela de contatos
-- Executada automaticamente pelo Docker ao subir o container

create table if not exists contatos (
  id        bigint generated always as identity primary key,
  nome      text not null,
  telefone  text not null,
  created_at timestamptz default now()
);

-- Habilita Row Level Security
alter table contatos enable row level security;

-- Permite leitura pública com a chave anon
create policy "Leitura pública de contatos"
  on contatos for select
  using (true);

-- Dados de exemplo para desenvolvimento local
insert into contatos (nome, telefone) values
  ('Maria Silva',  '5511999999999'),
  ('João Santos',  '5511888888888'),
  ('Ana Costa',    '5511777777777');
