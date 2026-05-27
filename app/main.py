from datetime import datetime
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

# Banco SQLite simples para o trabalho
DATABASE_URL = "sqlite:///./pagamentos.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# MODELOS DO BANCO DE DADOS
# =========================

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cnpj = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=True)

    vendas = relationship("Venda", back_populates="cliente")


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    descricao = Column(String, nullable=True)


class CondicaoPagamento(Base):
    __tablename__ = "condicoes_pagamento"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)
    quantidade_parcelas = Column(Integer, default=1)


class PrecoCliente(Base):
    __tablename__ = "precos_cliente"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    condicao_pagamento_id = Column(Integer, ForeignKey("condicoes_pagamento.id"), nullable=False)
    preco = Column(Float, nullable=False)

    cliente = relationship("Cliente")
    produto = relationship("Produto")
    condicao_pagamento = relationship("CondicaoPagamento")


class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    data_venda = Column(DateTime, default=datetime.utcnow)
    total = Column(Float, default=0)

    cliente = relationship("Cliente", back_populates="vendas")
    itens = relationship("VendaItem", cascade="all, delete", back_populates="venda")


class VendaItem(Base):
    __tablename__ = "venda_itens"

    id = Column(Integer, primary_key=True, index=True)
    venda_id = Column(Integer, ForeignKey("vendas.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    venda = relationship("Venda", back_populates="itens")
    produto = relationship("Produto")


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    mensagem = Column(String, nullable=False)
    status = Column(String, default="NAO_LIDA")
    criada_em = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente")
    produto = relationship("Produto")


# =========================
# SCHEMAS DA API
# =========================

class ClienteSchema(BaseModel):
    nome: str
    cnpj: str
    email: Optional[str] = None


class ProdutoSchema(BaseModel):
    nome: str
    descricao: Optional[str] = None


class CondicaoPagamentoSchema(BaseModel):
    descricao: str
    quantidade_parcelas: int = 1


class PrecoClienteSchema(BaseModel):
    cliente_id: int
    produto_id: int
    condicao_pagamento_id: int
    preco: float


class VendaItemSchema(BaseModel):
    produto_id: int
    quantidade: int
    preco_unitario: float


class VendaSchema(BaseModel):
    cliente_id: int
    itens: List[VendaItemSchema]


class Resposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int


# =========================
# FUNÇÕES AUXILIARES
# =========================

app = FastAPI(title="Sistema de Pagamentos API Simplificado")


def buscar_ou_erro(db: Session, modelo, registro_id: int):
    registro = db.get(modelo, registro_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return registro


def gerar_notificacoes(produto_id: int, novo_preco: float):
    """
    Essa função roda em segundo plano.
    Assim, a API não precisa fazer uma requisição HTTP separada para notificar o cliente.
    """
    db = SessionLocal()
    try:
        itens = db.query(VendaItem).filter(
            VendaItem.produto_id == produto_id,
            VendaItem.preco_unitario > novo_preco,
        ).all()

        clientes_notificados = set()

        for item in itens:
            cliente_id = item.venda.cliente_id

            if cliente_id in clientes_notificados:
                continue

            produto = db.get(Produto, produto_id)
            mensagem = (
                f"O produto {produto.nome} agora está custando R$ {novo_preco:.2f}. "
                f"Você comprou anteriormente por um valor maior."
            )

            notificacao = Notificacao(
                cliente_id=cliente_id,
                produto_id=produto_id,
                mensagem=mensagem,
            )
            db.add(notificacao)
            clientes_notificados.add(cliente_id)

        db.commit()
    finally:
        db.close()


# =========================
# ROTAS BÁSICAS
# =========================

@app.get("/")
def inicio():
    return {"mensagem": "API de Sistema de Pagamentos funcionando"}


# CLIENTES
@app.post("/clientes/")
def criar_cliente(dados: ClienteSchema, db: Session = Depends(get_db)):
    cliente = Cliente(**dados.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@app.get("/clientes/")
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).all()


@app.get("/clientes/{cliente_id}")
def buscar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    return buscar_ou_erro(db, Cliente, cliente_id)


@app.put("/clientes/{cliente_id}")
def atualizar_cliente(cliente_id: int, dados: ClienteSchema, db: Session = Depends(get_db)):
    cliente = buscar_ou_erro(db, Cliente, cliente_id)
    cliente.nome = dados.nome
    cliente.cnpj = dados.cnpj
    cliente.email = dados.email
    db.commit()
    db.refresh(cliente)
    return cliente


@app.delete("/clientes/{cliente_id}")
def excluir_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = buscar_ou_erro(db, Cliente, cliente_id)
    db.delete(cliente)
    db.commit()
    return {"mensagem": "Cliente excluído"}


# PRODUTOS
@app.post("/produtos/")
def criar_produto(dados: ProdutoSchema, db: Session = Depends(get_db)):
    produto = Produto(**dados.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@app.get("/produtos/")
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).all()


@app.get("/produtos/{produto_id}")
def buscar_produto(produto_id: int, db: Session = Depends(get_db)):
    return buscar_ou_erro(db, Produto, produto_id)


@app.put("/produtos/{produto_id}")
def atualizar_produto(produto_id: int, dados: ProdutoSchema, db: Session = Depends(get_db)):
    produto = buscar_ou_erro(db, Produto, produto_id)
    produto.nome = dados.nome
    produto.descricao = dados.descricao
    db.commit()
    db.refresh(produto)
    return produto


@app.delete("/produtos/{produto_id}")
def excluir_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = buscar_ou_erro(db, Produto, produto_id)
    db.delete(produto)
    db.commit()
    return {"mensagem": "Produto excluído"}


# CONDIÇÕES DE PAGAMENTO
@app.post("/condicoes-pagamento/")
def criar_condicao(dados: CondicaoPagamentoSchema, db: Session = Depends(get_db)):
    condicao = CondicaoPagamento(**dados.model_dump())
    db.add(condicao)
    db.commit()
    db.refresh(condicao)
    return condicao


@app.get("/condicoes-pagamento/")
def listar_condicoes(db: Session = Depends(get_db)):
    return db.query(CondicaoPagamento).all()


@app.get("/condicoes-pagamento/{condicao_id}")
def buscar_condicao(condicao_id: int, db: Session = Depends(get_db)):
    return buscar_ou_erro(db, CondicaoPagamento, condicao_id)


@app.put("/condicoes-pagamento/{condicao_id}")
def atualizar_condicao(condicao_id: int, dados: CondicaoPagamentoSchema, db: Session = Depends(get_db)):
    condicao = buscar_ou_erro(db, CondicaoPagamento, condicao_id)
    condicao.descricao = dados.descricao
    condicao.quantidade_parcelas = dados.quantidade_parcelas
    db.commit()
    db.refresh(condicao)
    return condicao


@app.delete("/condicoes-pagamento/{condicao_id}")
def excluir_condicao(condicao_id: int, db: Session = Depends(get_db)):
    condicao = buscar_ou_erro(db, CondicaoPagamento, condicao_id)
    db.delete(condicao)
    db.commit()
    return {"mensagem": "Condição de pagamento excluída"}


# TABELA DE PREÇOS POR CLIENTE
@app.post("/precos-clientes/")
def criar_preco(dados: PrecoClienteSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    buscar_ou_erro(db, Cliente, dados.cliente_id)
    buscar_ou_erro(db, Produto, dados.produto_id)
    buscar_ou_erro(db, CondicaoPagamento, dados.condicao_pagamento_id)

    preco = PrecoCliente(**dados.model_dump())
    db.add(preco)
    db.commit()
    db.refresh(preco)

    background_tasks.add_task(gerar_notificacoes, dados.produto_id, dados.preco)
    return preco


@app.get("/precos-clientes/")
def listar_precos(db: Session = Depends(get_db)):
    return db.query(PrecoCliente).all()


@app.get("/precos-clientes/{preco_id}")
def buscar_preco(preco_id: int, db: Session = Depends(get_db)):
    return buscar_ou_erro(db, PrecoCliente, preco_id)


@app.put("/precos-clientes/{preco_id}")
def atualizar_preco(preco_id: int, dados: PrecoClienteSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    preco = buscar_ou_erro(db, PrecoCliente, preco_id)

    preco.cliente_id = dados.cliente_id
    preco.produto_id = dados.produto_id
    preco.condicao_pagamento_id = dados.condicao_pagamento_id
    preco.preco = dados.preco

    db.commit()
    db.refresh(preco)

    background_tasks.add_task(gerar_notificacoes, dados.produto_id, dados.preco)
    return preco


@app.delete("/precos-clientes/{preco_id}")
def excluir_preco(preco_id: int, db: Session = Depends(get_db)):
    preco = buscar_ou_erro(db, PrecoCliente, preco_id)
    db.delete(preco)
    db.commit()
    return {"mensagem": "Preço excluído"}


# VENDAS
@app.post("/vendas/")
def criar_venda(dados: VendaSchema, db: Session = Depends(get_db)):
    buscar_ou_erro(db, Cliente, dados.cliente_id)

    venda = Venda(cliente_id=dados.cliente_id, total=0)
    db.add(venda)
    db.flush()

    total = 0
    for item in dados.itens:
        buscar_ou_erro(db, Produto, item.produto_id)
        subtotal = item.quantidade * item.preco_unitario
        total += subtotal

        venda_item = VendaItem(
            venda_id=venda.id,
            produto_id=item.produto_id,
            quantidade=item.quantidade,
            preco_unitario=item.preco_unitario,
            subtotal=subtotal,
        )
        db.add(venda_item)

    venda.total = total
    db.commit()
    db.refresh(venda)
    return venda


@app.get("/vendas/")
def listar_vendas(db: Session = Depends(get_db)):
    return db.query(Venda).all()


@app.get("/vendas/{venda_id}")
def buscar_venda(venda_id: int, db: Session = Depends(get_db)):
    return buscar_ou_erro(db, Venda, venda_id)


@app.put("/vendas/{venda_id}")
def atualizar_venda(venda_id: int, dados: VendaSchema, db: Session = Depends(get_db)):
    venda = buscar_ou_erro(db, Venda, venda_id)
    buscar_ou_erro(db, Cliente, dados.cliente_id)

    venda.cliente_id = dados.cliente_id

    for item_antigo in venda.itens:
        db.delete(item_antigo)
    db.flush()

    total = 0
    for item in dados.itens:
        buscar_ou_erro(db, Produto, item.produto_id)
        subtotal = item.quantidade * item.preco_unitario
        total += subtotal

        venda_item = VendaItem(
            venda_id=venda.id,
            produto_id=item.produto_id,
            quantidade=item.quantidade,
            preco_unitario=item.preco_unitario,
            subtotal=subtotal,
        )
        db.add(venda_item)

    venda.total = total
    db.commit()
    db.refresh(venda)
    return venda


@app.delete("/vendas/{venda_id}")
def excluir_venda(venda_id: int, db: Session = Depends(get_db)):
    venda = buscar_ou_erro(db, Venda, venda_id)
    db.delete(venda)
    db.commit()
    return {"mensagem": "Venda excluída"}


# NOTIFICAÇÕES
@app.get("/notificacoes/")
def listar_notificacoes(cliente_id: Optional[int] = None, db: Session = Depends(get_db)):
    consulta = db.query(Notificacao)
    if cliente_id:
        consulta = consulta.filter(Notificacao.cliente_id == cliente_id)
    return consulta.all()


@app.patch("/notificacoes/{notificacao_id}/ler")
def marcar_como_lida(notificacao_id: int, db: Session = Depends(get_db)):
    notificacao = buscar_ou_erro(db, Notificacao, notificacao_id)
    notificacao.status = "LIDA"
    db.commit()
    db.refresh(notificacao)
    return notificacao


@app.delete("/notificacoes/{notificacao_id}")
def excluir_notificacao(notificacao_id: int, db: Session = Depends(get_db)):
    notificacao = buscar_ou_erro(db, Notificacao, notificacao_id)
    db.delete(notificacao)
    db.commit()
    return {"mensagem": "Notificação excluída"}


Base.metadata.create_all(bind=engine)
