-- Migração 002: adiciona colunas de controle de envio para idempotência
-- Permite que o script rode múltiplas vezes sem reenviar mensagens já enviadas.
--
-- COMO EXECUTAR:
--   Acesse o SQL Editor no painel do Supabase e cole este script inteiro.

alter table contatos
  add column if not exists status_envio text not null default 'pendente'
    check (status_envio in ('pendente', 'enviado', 'erro')),
  add column if not exists enviado_em  timestamptz,
  add column if not exists erro_msg    text;

-- Índice para que o filtro WHERE status_envio = 'pendente' seja eficiente
create index if not exists idx_contatos_status_envio
  on contatos (status_envio);

-- Política RLS: permite que o script atualize o status dos contatos
do $$
begin
  if not exists (
    select 1 from pg_policies
    where tablename = 'contatos'
      and policyname = 'Atualizacao de status'
  ) then
    execute 'create policy "Atualizacao de status" on contatos for update using (true)';
  end if;
end$$;
