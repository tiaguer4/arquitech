from django.db import models
from usuarios.models import Usuario


class Cliente(models.Model):
    """
    Cliente do arquiteto. Cada cliente pertence a UM usuário (arquiteto),
    mas um arquiteto pode ter vários clientes.
    """

    STATUS_CHOICES = [
        ('A', 'Ativo'),
        ('I', 'Inativo'),
    ]
    
    id_cliente = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, unique=True)  # CPF só com números no banco
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    observacao = models.TextField(blank=True, null=True)  # TextField = texto longo
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    
    # ForeignKey = chave estrangeira. Liga este cliente a um usuário.
    # on_delete=CASCADE significa: se o usuário for deletado, os clientes dele também são.
    # db_column garante que a coluna no Postgres se chame "id_usuario".
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario')

    class Meta:
        db_table = 'cliente'

    def __str__(self):
        return self.nome