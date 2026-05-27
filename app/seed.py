from app.main import (
    Cliente,
    CondicaoPagamento,
    Produto,
    SessionLocal,
    Venda,
    VendaItem,
)


def popular_banco():
    db = SessionLocal()
    try:
        if db.query(Cliente).first():
            print("O banco já possui dados.")
            return

        cliente = Cliente(nome="Mercado Central", cnpj="12.345.678/0001-99", email="mercado@email.com")
        produto = Produto(nome="Arroz 5kg", descricao="Pacote de arroz")
        condicao = CondicaoPagamento(descricao="À vista", quantidade_parcelas=1)

        db.add_all([cliente, produto, condicao])
        db.commit()

        venda = Venda(cliente_id=cliente.id, total=100)
        db.add(venda)
        db.flush()

        item = VendaItem(
            venda_id=venda.id,
            produto_id=produto.id,
            quantidade=1,
            preco_unitario=100,
            subtotal=100,
        )
        db.add(item)
        db.commit()

        print("Dados de exemplo cadastrados com sucesso.")
        print("Cliente ID: 1 | Produto ID: 1 | Condição ID: 1")
        print("Para testar a notificação, cadastre um preço menor que 100 para o produto 1.")
    finally:
        db.close()


if __name__ == "__main__":
    popular_banco()
