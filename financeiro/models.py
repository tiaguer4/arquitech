from django.db import models
from clientes.models import Cliente
from usuarios.models import Usuario


class Contrato(models.Model):
    """
    Contrato firmado entre o arquiteto e um cliente.
    Um contrato gera N parcelas (PagamentoParcela) e N projetos.
    """

    STATUS_CHOICES = [
        ('AS', 'Assinado'),
        ('NA', 'Não Assinado'),
        ('CA', 'Cancelado'),
    ]
    TP_PROJETO_CHOICES = [
        ('RE', 'Residencial'),
        ('CO', 'Comercial'),
    ]

    id_contrato = models.AutoField(primary_key=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='NA')
    num_contrato = models.IntegerField(unique=True)   # Número único por contrato
    tp_projeto = models.CharField(max_length=2, choices=TP_PROJETO_CHOICES)
    vlr_contrato = models.DecimalField(max_digits=10, decimal_places=2)  # 10 dígitos, 2 casas decimais
    num_parcelas = models.IntegerField()
    dt_assinatura_contrato = models.DateField(blank=True, null=True)  # Pode estar em branco

    # Vínculo com o arquiteto (dono do contrato) e com o cliente
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario')
    id_cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column='id_cliente')

    class Meta:
        db_table = 'contrato'


class PagamentoParcela(models.Model):
    """
    Cada linha é UMA parcela de um contrato (ex: 1/10 de R$ 10.000).
    Ao cadastrar um contrato, o sistema gera automaticamente todas as parcelas.
    """

    STATUS_CHOICES = [('P', 'Pago'), ('A', 'Em Aberto')]
    FORMA_CHOICES = [
        ('T', 'Transferência/PIX'),
        ('D', 'Dinheiro'),
        ('C', 'Cartão'),
        ('B', 'Boleto'),
        ('P', 'Permuta'),
        ('O', 'Outros'),
    ]

    id_pagamento_parcelas = models.AutoField(primary_key=True)
    dt_vencimento = models.DateField()                     # Data em que vence
    dt_pagamento = models.DateField(blank=True, null=True) # Preenchida quando é paga
    vlr_parcela = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField(max_length=1, choices=FORMA_CHOICES, blank=True, null=True)
    status_pagamento = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')

    # Dados do pagamento (preenchidos ao registrar que a parcela foi paga)
    comprovante = models.FileField(upload_to='comprovantes/', blank=True, null=True)  # PDF/JPG/PNG
    observacao = models.TextField(blank=True, null=True)  # ex.: "pago por PIX às 14h"
    
    # Cada parcela pertence a UM contrato
    id_contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, db_column='id_contrato')

    class Meta:
        db_table = 'pagamento_parcelas'