# Sistema de Pagamentos API 

A API foi feita com **FastAPI**, **SQLAlchemy** e **SQLite**.

## O que o projeto faz

O sistema possui os cadastros principais do trabalho:

- clientes;
- produtos;
- condições de pagamento;
- preços por cliente;
- vendas;
- notificações.

A ideia principal é permitir cadastrar uma **tabela de preços por cliente**. Quando o preço de um produto fica menor do que o valor pago anteriormente por um cliente, o sistema gera uma notificação para esse cliente.

A notificação não é feita por uma nova requisição HTTP. Ela é gerada em segundo plano pela própria API, usando `BackgroundTasks` do FastAPI.

## Como rodar

Abra a pasta no VS Code e rode os comandos abaixo.

### 1. Criar ambiente virtual

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

No Linux/Mac:

```bash
source .venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Popular o banco com dados de exemplo

```bash
python -m app.seed
```

### 4. Rodar a API

```bash
uvicorn app.main:app --reload
```

Acesse:

```text
http://127.0.0.1:8000/docs
```

## Teste rápido da notificação

Depois de rodar o seed, existe uma venda de exemplo onde o cliente comprou o produto 1 por R$ 100,00.

Para testar a regra, cadastre um preço menor para o produto 1:

```http
POST /precos-clientes/
```

Com este JSON:

```json
{
  "cliente_id": 1,
  "produto_id": 1,
  "condicao_pagamento_id": 1,
  "preco": 80.0
}
```

Depois consulte:

```http
GET /notificacoes/?cliente_id=1
```

O sistema deve retornar uma notificação dizendo que o produto agora está mais barato.

## Principais rotas

### Clientes

- `POST /clientes/`
- `GET /clientes/`
- `GET /clientes/{cliente_id}`
- `PUT /clientes/{cliente_id}`
- `DELETE /clientes/{cliente_id}`

### Produtos

- `POST /produtos/`
- `GET /produtos/`
- `GET /produtos/{produto_id}`
- `PUT /produtos/{produto_id}`
- `DELETE /produtos/{produto_id}`

### Condições de pagamento

- `POST /condicoes-pagamento/`
- `GET /condicoes-pagamento/`
- `GET /condicoes-pagamento/{condicao_id}`
- `PUT /condicoes-pagamento/{condicao_id}`
- `DELETE /condicoes-pagamento/{condicao_id}`

### Preços por cliente

- `POST /precos-clientes/`
- `GET /precos-clientes/`
- `GET /precos-clientes/{preco_id}`
- `PUT /precos-clientes/{preco_id}`
- `DELETE /precos-clientes/{preco_id}`

### Vendas

- `POST /vendas/`
- `GET /vendas/`
- `GET /vendas/{venda_id}`
- `PUT /vendas/{venda_id}`
- `DELETE /vendas/{venda_id}`

### Notificações

- `GET /notificacoes/`
- `GET /notificacoes/?cliente_id=1`
- `PATCH /notificacoes/{notificacao_id}/ler`
- `DELETE /notificacoes/{notificacao_id}`

## Estrutura do projeto

```text
sistema_pagamentos_api_simplificado/
├── app/
│   ├── main.py
│   └── seed.py
├── docs/
│   └── diagrama-er.md
├── requirements.txt
└── README.md
```
