from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_documentacao, name='lista_documentacao'),                          # /documentacao/
    path('novo/', views.cadastrar_documento, name='cadastrar_documento'),                   # /documentacao/novo/
    path('<int:id_documentacao>/editar/', views.editar_documento, name='editar_documento'), # /documentacao/1/editar/
    path('<int:id_documentacao>/deletar/', views.deletar_documento, name='deletar_documento'),
]