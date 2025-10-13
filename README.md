# Sistema de Gestão para Fábrica Artesanal de Velas Aromáticas

Aplicação web completa (Flask + SQLite) para controle financeiro, produtivo e de estoque de um ateliê de velas artesanais. O sistema foi desenhado para uso multiusuário (sócios) e cobre todas as sessões solicitadas:

- **Dashboard** com KPIs chave: custo médio unitário, estoque de insumos, receita potencial, ponto de equilíbrio e DRE anualizada.
- **Sessão 1 – Precificação**: cadastro de custos fixos, upload de planilhas de insumos, cadastro manual e criação de modelos de vela com cálculo automático do custo unitário e preço sugerido.
- **Sessão 2 – Estoque**: visão consolidada dos insumos, gargalo produtivo e receita em potencial.
- **Sessão 3 – Produção**: registro de ordens de produção com baixa automática dos insumos e geração de estoque de produtos acabados.
- **Sessão 4 – Gestão Orçamentária**: orçamento de vendas, custos, estoque, DRE anualizada e simulador de cenários.

## Como executar

1. Crie e ative um ambiente virtual Python 3.11+.
2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Execute o servidor Flask:

   ```bash
   flask --app app run
   ```

4. Acesse `http://localhost:5000` no navegador. O usuário padrão é `admin` com senha `admin`. Altere a senha em produção configurando a variável de ambiente `DEFAULT_ADMIN_PASSWORD`.

## Estrutura de dados

- `candles.db` (SQLite) guarda usuários, custos fixos, lotes de insumos, modelos de vela e produções.
- Uploads de planilhas aceitam CSV ou Excel (`.xlsx`) com as colunas descritas nas telas.
- O sistema calcula automaticamente o rateio de frete entre as unidades.

## Funcionalidades adicionais

- Alocação FIFO de insumos nas ordens de produção.
- Cálculo de custo variável unitário (cera + essência + lata + pavio + outros) e custo total com rateio dos custos fixos.
- Sugestão de preço de venda baseada na margem desejada configurada por modelo.
- Simulador para testar cenários de margem, preço, volume e custos.

## Segurança

- Autenticação obrigatória para todas as rotas (multiusuário).
- Os dados são compartilhados entre os sócios autenticados.

A aplicação foi desenvolvida para servir como base sólida e extensível para a gestão do negócio artesanal de velas aromáticas.

## Como testar

Com as dependências instaladas e o ambiente virtual ativo, você pode verificar rapidamente se o projeto está saudável executando a compilação dos módulos Python e iniciando o servidor de desenvolvimento:

```bash
# checa se há erros de sintaxe
python -m compileall .

# roda a suíte de integração manual (servidor Flask)
flask --app app run
```

Depois de o servidor estar em execução (`http://localhost:5000`), autentique-se com `admin/admin` e navegue pelas sessões do sistema (Dashboard, Precificação, Estoque, Produção e Orçamento) para validar os fluxos principais. Recomenda-se cadastrar alguns custos fixos, importar ou registrar insumos manualmente, gerar um modelo de vela e lançar uma ordem de produção para observar a atualização automática dos estoques e dos indicadores financeiros.
