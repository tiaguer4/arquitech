from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_clientes, name='lista_clientes'),                              # /clientes/
    path('novo/', views.cadastrar_cliente, name='cadastrar_cliente'),                    # /clientes/novo/
    path('<int:id_cliente>/', views.detalhe_cliente, name='detalhe_cliente'),            # /clientes/1/
    path('<int:id_cliente>/editar/', views.editar_cliente, name='editar_cliente'),       # /clientes/1/editar/
    path('<int:id_cliente>/deletar/', views.deletar_cliente, name='deletar_cliente'),    # exclui (sem contrato) ou inativa (com contrato)
    path('<int:id_cliente>/reativar/', views.reativar_cliente, name='reativar_cliente'),
]