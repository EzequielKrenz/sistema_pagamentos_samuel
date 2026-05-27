# Diagrama Entidade-Relacionamento Simplificado

```mermaid
erDiagram
    CLIENTE ||--o{ VENDA : realiza
    CLIENTE ||--o{ PRECO_CLIENTE : possui
    CLIENTE ||--o{ NOTIFICACAO : recebe

    PRODUTO ||--o{ VENDA_ITEM : vendido_em
    PRODUTO ||--o{ PRECO_CLIENTE : possui_preco
    PRODUTO ||--o{ NOTIFICACAO : gera

    CONDICAO_PAGAMENTO ||--o{ PRECO_CLIENTE : define

    VENDA ||--o{ VENDA_ITEM : possui

    CLIENTE {
        int id PK
        string nome
        string cnpj
        string email
    }

    PRODUTO {
        int id PK
        string nome
        string descricao
    }

    CONDICAO_PAGAMENTO {
        int id PK
        string descricao
        int quantidade_parcelas
    }

    PRECO_CLIENTE {
        int id PK
        int cliente_id FK
        int produto_id FK
        int condicao_pagamento_id FK
        float preco
    }

    VENDA {
        int id PK
        int cliente_id FK
        datetime data_venda
        float total
    }

    VENDA_ITEM {
        int id PK
        int venda_id FK
        int produto_id FK
        int quantidade
        float preco_unitario
        float subtotal
    }

    NOTIFICACAO {
        int id PK
        int cliente_id FK
        int produto_id FK
        string mensagem
        string status
        datetime criada_em
    }
```

## Explicação simples

- Um cliente pode fazer várias vendas.
- Uma venda possui um ou mais itens.
- Cada item da venda possui um produto e o preço pago naquele momento.
- A tabela `precos_cliente` guarda o preço praticado para cada cliente.
- Quando um novo preço fica menor que o preço já pago em uma venda, o sistema cria uma notificação.
