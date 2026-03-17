# MiniCRM — Auditoria Técnica (2026-03)

## Resumo executivo

- **Risco crítico 1:** escalonamento de privilégio no cadastro (autoatribuição de `Gestor`).
- **Risco alto 2:** logout via `GET` sem CSRF (session riding).
- **Risco alto 3:** ausência de proteção anti-brute force no login.
- **Risco médio 4:** import CSV sem limite de tamanho (DoS por memória) e whitelist de status inconsistente.
- **Risco médio 5:** export CSV/XLSX sem neutralização de fórmulas (CSV Injection).

## Achados priorizados

### 1) Escalonamento de privilégio no registro (CRÍTICO)
- A tela de cadastro expõe um seletor de perfil para qualquer usuário (`Operador`/`Gestor`) e o back-end persiste diretamente o valor enviado.
- Impacto: qualquer usuário recém-criado pode nascer com permissão administrativa.
- Recomendação:
  - Remover `role` do cadastro público.
  - Definir papel padrão `Operador` no servidor.
  - Criar fluxo administrativo separado para promoção de perfil (apenas Gestor/Admin).

### 2) Logout por GET sem proteção CSRF (ALTO)
- A rota de logout aceita `GET` e é acionada por link.
- Impacto: terceiros podem forçar logout do usuário (session riding), degradando UX e podendo interromper operações críticas.
- Recomendação:
  - Migrar logout para `POST` com CSRF token.
  - Atualizar navbar para `<form method="post">`.

### 3) Falta de rate limiting e lockout no login (ALTO)
- Não há limitação por IP/usuário nem backoff progressivo no endpoint de autenticação.
- Impacto: facilita brute force e credential stuffing.
- Recomendação:
  - Adotar Flask-Limiter (ou gateway com rate-limit).
  - Registrar tentativas por usuário/IP e bloquear temporariamente após N falhas.

### 4) Importação CSV sem limite de tamanho e validação parcial (MÉDIO)
- O upload lê o arquivo inteiro na memória.
- A validação de status no import não inclui `Cancelado`, divergindo do restante do sistema.
- Impacto: risco de DoS por memória e inconsistência de dados.
- Recomendação:
  - Definir `MAX_CONTENT_LENGTH`.
  - Processamento em stream/chunks e validação de schema robusta.
  - Unificar enum/status em fonte única.

### 5) CSV/XLSX export sem mitigação de fórmula (MÉDIO)
- Campos textuais são exportados sem prefixo seguro para valores iniciando com `=`, `+`, `-`, `@`.
- Impacto: ao abrir no Excel/LibreOffice, pode haver execução de fórmulas maliciosas (CSV Injection).
- Recomendação:
  - Sanitizar células exportadas com prefixo `'` quando começarem com caracteres de fórmula.

## Robustez para nível “apps grandes”

1. **Arquitetura e domínio**
   - Separar camadas (API/service/repository) para reduzir acoplamento em `views.py`.
   - Introduzir eventos de domínio/auditoria assinada (imutável).

2. **Segurança by design**
   - RBAC centralizado + políticas por recurso.
   - Segredos fora de env local em produção (Vault/KMS).
   - SAST/DAST/dependency scanning no CI.

3. **Confiabilidade operacional**
   - Observabilidade (logs estruturados, métricas, tracing).
   - Health checks, readiness/liveness, e runbooks.
   - Backups automáticos e testes periódicos de restore.

4. **Escalabilidade e performance**
   - Migrar de SQLite para Postgres em produção.
   - Índices por consultas de filtro (`status`, `deadline`, `user_id`, `created_at`).
   - Tarefas assíncronas (fila) para import/export pesado.

5. **Qualidade de engenharia**
   - Pirâmide de testes (unit, integração, e2e) com cobertura mínima.
   - Ambientes com Docker + CI/CD (lint, type-check, testes, migrações).
   - Versionamento de API/contratos e feature flags.

## Roadmap sugerido (90 dias)

- **Semana 1–2:** corrigir riscos críticos/altos (registro, logout POST+CSRF, rate limiting).
- **Semana 3–4:** hardening import/export e unificação de enum/status.
- **Mês 2:** observabilidade, índices, migração para Postgres em staging.
- **Mês 3:** CI/CD completo, testes e processos de resposta a incidentes.
