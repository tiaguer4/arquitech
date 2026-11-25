from django.db import models
from projetos.models import Projeto


class Documentacao(models.Model):
    """
    Cada linha representa um documento do projeto (Alvará, Matrícula, etc.).
    O arquivo é OPCIONAL — o arquiteto pode criar o registro primeiro (pendência)
    e só anexar o PDF/imagem depois, quando coletar.
    """

    STATUS_CHOICES = [
        ('CO', 'Coletado'),
        ('NC', 'Não Coletado'),
    ]
    
    id_documentacao = models.AutoField(primary_key=True)
    tp_documentacao = models.CharField(max_length=10)  # ALV, MAT, TOP, MDR, etc.
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='NC')
    observacao = models.TextField(blank=True, null=True)

    # FileField salva o ARQUIVO em media/documentos/ e guarda o CAMINHO no banco.
    # blank=True, null=True = campo opcional.
    arquivo = models.FileField(upload_to='documentos/', blank=True, null=True)
    
    # Cada documento pertence a UM projeto
    id_projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, db_column='id_projeto')

    class Meta:
        db_table = 'documentacao'