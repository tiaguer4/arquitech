from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import connection, IntegrityError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


# Para a APRESENTAÇÃO: False = aceita qualquer CPF com 11 números (ex.: 11111111111).
# Para uso real, volte para True (confere os dígitos verificadores).
VALIDAR_DIGITOS_CPF = False


def validar_cpf(cpf):
    """
    Valida CPF usando o algoritmo dos dígitos verificadores.
    1) Remove tudo que não é número.
    2) Rejeita CPFs de tamanho errado ou com todos dígitos iguais (111.111.111-11).
    3) Calcula os dois dígitos verificadores e compara.
    """
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11: return False
    if not VALIDAR_DIGITOS_CPF: return True   # só exige 11 números
    if cpf == cpf[0] * 11: return False

    # Primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10: resto = 0
    if resto != int(cpf[9]): return False

    # Segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10: resto = 0
    if resto != int(cpf[10]): return False
    return True


def lista_clientes(request):
    """Lista os clientes do usuário logado."""
    if not request.session.get('usuario_id'): return redirect('login')
    usuario_id = request.session.get('usuario_id')
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cl.id_cliente, cl.nome, cl.cpf, cl.telefone, cl.email, cl.endereco,
                   cl.status,
                   (SELECT COUNT(*) FROM contrato c WHERE c.id_cliente = cl.id_cliente)
                 + (SELECT COUNT(*) FROM projeto p WHERE p.id_cliente = cl.id_cliente) AS qtd_vinculos
            FROM cliente cl WHERE cl.id_usuario = %s ORDER BY cl.nome;
        """, [usuario_id])
        clientes = cursor.fetchall()
    return render(request, 'clientes/clientes.html', {
        'clientes': clientes,
        'is_admin': request.session.get('usuario_perfil') == 'A',
    })


def detalhe_cliente(request, id_cliente):
    """
    Página de detalhe do cliente: mostra dados, contratos e projetos dele.
    Serve como central de navegação cruzada (cliente → contratos → projetos).
    """
    if not request.session.get('usuario_id'): return redirect('login')
    usuario_id = request.session.get('usuario_id')

    with connection.cursor() as cursor:
        # 1) Dados do cliente (garante que é do usuário logado)
        cursor.execute("""
            SELECT id_cliente, nome, cpf, telefone, email, endereco, observacao, status
            FROM cliente WHERE id_cliente = %s AND id_usuario = %s;
        """, [id_cliente, usuario_id])
        cliente = cursor.fetchone()
        if cliente is None: return redirect('lista_clientes')

        # 2) Contratos do cliente
        cursor.execute("""
            SELECT id_contrato, num_contrato, tp_projeto, vlr_contrato, 
                   num_parcelas, dt_assinatura_contrato, status
            FROM contrato WHERE id_cliente = %s AND id_usuario = %s
            ORDER BY num_contrato DESC;
        """, [id_cliente, usuario_id])
        contratos = cursor.fetchall()

        # 3) Projetos do cliente (com ou sem contrato)
        cursor.execute("""
            SELECT p.id_projeto, p.endereco_projeto, p.status, c.num_contrato, p.dt_inicio, p.dt_previsao_termino
            FROM projeto p
            LEFT JOIN contrato c ON p.id_contrato = c.id_contrato
            WHERE p.id_cliente = %s AND p.id_usuario = %s
            ORDER BY p.id_projeto DESC;
        """, [id_cliente, usuario_id])
        projetos = cursor.fetchall()

    return render(request, 'clientes/cliente-detalhe.html', {
        'cliente': cliente, 'contratos': contratos, 'projetos': projetos,
        'is_admin': request.session.get('usuario_perfil') == 'A',
    })


def cadastrar_cliente(request):
    """Cria um novo cliente para o usuário logado."""
    if not request.session.get('usuario_id'): return redirect('login')
    usuario_id = request.session.get('usuario_id')
    erro = None

    if request.method == 'POST':
        # Pega e limpa os dados
        nome = request.POST.get('nome')
        cpf_raw = request.POST.get('cpf') or ''
        cpf = ''.join(filter(str.isdigit, cpf_raw))  # Salva só números no banco
        telefone = request.POST.get('telefone') or None
        email = request.POST.get('email') or None
        endereco = request.POST.get('endereco') or None
        observacao = request.POST.get('observacao') or None

        # Validações
        if not nome or not cpf: erro = "Nome e CPF são obrigatórios."
        elif not validar_cpf(cpf): erro = "CPF inválido. Verifique os dígitos."
        elif email:
            try: validate_email(email)
            except ValidationError: erro = "E-mail inválido."

        if erro is None:
            with connection.cursor() as cursor:
                # Verifica duplicidade de CPF PARA ESTE USUÁRIO (não global)
                cursor.execute("SELECT id_cliente FROM cliente WHERE cpf = %s AND id_usuario = %s;", [cpf, usuario_id])
                if cursor.fetchone():
                    erro = "Você já tem um cliente cadastrado com este CPF."
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO cliente (nome, cpf, telefone, email, endereco, observacao, status, id_usuario)
                            VALUES (%s, %s, %s, %s, %s, %s, 'A', %s);
                        """, [nome, cpf, telefone, email, endereco, observacao, usuario_id])
                        return redirect('lista_clientes')
                    except IntegrityError:
                        # Se o banco ainda tiver CPF UNIQUE global, o CPF pode já existir
                        # na carteira de OUTRO arquiteto. Mostra mensagem em vez de erro 500.
                        erro = "Este CPF já está cadastrado no sistema."

    return render(request, 'clientes/cliente-form.html', {
        'erro': erro, 'is_admin': request.session.get('usuario_perfil') == 'A',
    })


def editar_cliente(request, id_cliente):
    """Atualiza dados do cliente. Verifica que pertence ao usuário logado."""
    if not request.session.get('usuario_id'): return redirect('login')
    usuario_id = request.session.get('usuario_id')
    erro = None

    if request.method == 'POST':
        nome = request.POST.get('nome')
        cpf_raw = request.POST.get('cpf') or ''
        cpf = ''.join(filter(str.isdigit, cpf_raw))
        telefone = request.POST.get('telefone') or None
        email = request.POST.get('email') or None
        endereco = request.POST.get('endereco') or None
        observacao = request.POST.get('observacao') or None

        # Validações (mesmas do cadastro)
        if not nome or not cpf: erro = "Nome e CPF são obrigatórios."
        elif not validar_cpf(cpf): erro = "CPF inválido."
        elif email:
            try: validate_email(email)
            except ValidationError: erro = "E-mail inválido."

        if erro is None:
            with connection.cursor() as cursor:
                # Verifica duplicidade — EXCLUINDO o próprio cliente atual
                cursor.execute("""
                    SELECT id_cliente FROM cliente WHERE cpf = %s AND id_usuario = %s AND id_cliente != %s;
                """, [cpf, usuario_id, id_cliente])
                if cursor.fetchone():
                    erro = "Já existe outro cliente seu com este CPF."
                else:
                    try:
                        cursor.execute("""
                            UPDATE cliente SET nome = %s, cpf = %s, telefone = %s, email = %s, endereco = %s, observacao = %s
                            WHERE id_cliente = %s AND id_usuario = %s;
                        """, [nome, cpf, telefone, email, endereco, observacao, id_cliente, usuario_id])
                        return redirect('lista_clientes')
                    except IntegrityError:
                        erro = "Este CPF já está cadastrado no sistema."

    # GET: carrega os dados do cliente para preencher o form
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_cliente, nome, cpf, telefone, email, endereco, observacao 
            FROM cliente WHERE id_cliente = %s AND id_usuario = %s;
        """, [id_cliente, usuario_id])
        cliente = cursor.fetchone()
    if cliente is None: return redirect('lista_clientes')
    return render(request, 'clientes/cliente-form.html', {
        'cliente': cliente, 'erro': erro, 'is_admin': request.session.get('usuario_perfil') == 'A',
    })


@require_POST
def deletar_cliente(request, id_cliente):
    """
    Cliente SEM contrato/projeto → é apagado de verdade.
    Cliente COM contrato ou projeto → só é INATIVADO (status 'I'), para não perder o histórico.
    O WHERE com id_usuario garante que ninguém mexe em cliente dos outros.
    """
    if not request.session.get('usuario_id'): return redirect('login')
    usuario_id = request.session.get('usuario_id')
    with connection.cursor() as cursor:
        cursor.execute("SELECT nome FROM cliente WHERE id_cliente = %s AND id_usuario = %s;", [id_cliente, usuario_id])
        cliente = cursor.fetchone()
        if cliente is None: return redirect('lista_clientes')

        cursor.execute("""
            SELECT (SELECT COUNT(*) FROM contrato WHERE id_cliente = %s)
                 + (SELECT COUNT(*) FROM projeto WHERE id_cliente = %s);
        """, [id_cliente, id_cliente])
        qtd_vinculos = cursor.fetchone()[0]

        if qtd_vinculos > 0:
            cursor.execute("UPDATE cliente SET status = 'I' WHERE id_cliente = %s AND id_usuario = %s;", [id_cliente, usuario_id])
            messages.success(request, f'{cliente[0]} possui contrato(s) ou projeto(s), por isso foi INATIVADO e não excluído.')
        else:
            cursor.execute("DELETE FROM cliente WHERE id_cliente = %s AND id_usuario = %s;", [id_cliente, usuario_id])
            messages.success(request, f'{cliente[0]} foi excluído.')
    return redirect('lista_clientes')


@require_POST
def reativar_cliente(request, id_cliente):
    """Volta um cliente inativo para ativo (status 'A')."""
    if not request.session.get('usuario_id'): return redirect('login')
    usuario_id = request.session.get('usuario_id')
    with connection.cursor() as cursor:
        cursor.execute("UPDATE cliente SET status = 'A' WHERE id_cliente = %s AND id_usuario = %s AND status = 'I';", [id_cliente, usuario_id])
        if cursor.rowcount:
            messages.success(request, 'Cliente reativado.')
    return redirect('lista_clientes')