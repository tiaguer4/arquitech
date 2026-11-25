from django.shortcuts import render, redirect
from django.urls import reverse
from django.db import connection
import os
import uuid
from django.conf import settings


def lista_documentacao(request):
    """
    Lista os documentos dos projetos do usuário logado.
    Se a URL trouxer ?projeto=ID, mostra SÓ os documentos daquele projeto.
    """
    if not request.session.get('usuario_id'):
        return redirect('login')
    usuario_id = request.session.get('usuario_id')

    # Filtro opcional (vem do link "ver documentações" na tela do projeto)
    try:
        id_projeto_filtro = int(request.GET.get('projeto'))
    except (TypeError, ValueError):
        id_projeto_filtro = None  # sem filtro, ou valor inválido → mostra todos

    # O texto do SQL só ganha trechos FIXOS; os valores continuam indo em %s (seguro)
    sql = """
        SELECT d.id_documentacao, d.tp_documentacao, d.status, d.observacao, 
               p.id_projeto, p.endereco_projeto, d.arquivo
        FROM documentacao d
        JOIN projeto p ON d.id_projeto = p.id_projeto
        WHERE p.id_usuario = %s
    """
    params = [usuario_id]
    if id_projeto_filtro is not None:
        sql += " AND d.id_projeto = %s"
        params.append(id_projeto_filtro)
    sql += " ORDER BY d.id_documentacao DESC;"

    projeto_filtrado = None
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        documentos = cursor.fetchall()

        # Busca o endereço do projeto filtrado (para mostrar no título da tela)
        if id_projeto_filtro is not None:
            cursor.execute("""
                SELECT p.id_projeto, p.endereco_projeto FROM projeto p
                WHERE p.id_projeto = %s AND p.id_usuario = %s;
            """, [id_projeto_filtro, usuario_id])
            projeto_filtrado = cursor.fetchone()

    return render(request, 'documentacao/documentacao.html', {
        'documentos': documentos,
        'projeto_filtrado': projeto_filtrado,  # None = mostrando todos
    })


def cadastrar_documento(request):
    """
    Cria um documento. Pode ser SEM arquivo (cria pendência)
    ou COM arquivo (upload imediato).
    """
    if not request.session.get('usuario_id'):
        return redirect('login')
    usuario_id = request.session.get('usuario_id')
    erro = None

    # Projeto PRÉ-SELECIONADO: vem de ?projeto=ID (botão "Novo documento" na tela do projeto).
    # Se o form não tiver "action", o POST mantém essa query string e o valor continua aqui.
    try:
        id_fixo = int(request.GET.get('projeto'))
    except (TypeError, ValueError):
        id_fixo = None

    if request.method == 'POST':
        tp_documentacao = request.POST.get('tp')
        status = request.POST.get('status')
        id_projeto = request.POST.get('projeto')
        observacao = request.POST.get('obs') or None
        arquivo = request.FILES.get('arquivo')  # FILES = arquivos enviados

        if not tp_documentacao or not status or not id_projeto:
            erro = "Preencha todos os campos obrigatórios."
        else:
            with connection.cursor() as cursor:
                # SEGURANÇA: verifica se o projeto é do usuário logado
                cursor.execute("""
                    SELECT 1 FROM projeto p
                    WHERE p.id_projeto = %s AND p.id_usuario = %s;
                """, [id_projeto, usuario_id])

                if not cursor.fetchone():
                    erro = "Projeto inválido ou não pertence a você."
                else:
                    caminho_arquivo = None
                    if arquivo:
                        # Cria a pasta media/documentos/ se não existir
                        pasta = os.path.join(settings.MEDIA_ROOT, 'documentos')
                        os.makedirs(pasta, exist_ok=True)

                        # Salva o arquivo fisicamente no HD, em chunks (pedaços)
                        # nome único: evita sobrescrever arquivos e nomes perigosos (../)
                        ext = os.path.splitext(arquivo.name)[1].lower()
                        caminho_arquivo = f"documentos/{uuid.uuid4().hex}{ext}"
                        with open(os.path.join(settings.MEDIA_ROOT, caminho_arquivo), 'wb+') as destino:
                            for chunk in arquivo.chunks():
                                destino.write(chunk)

                    # INSERT no banco, guardando só o CAMINHO do arquivo
                    cursor.execute("""
                        INSERT INTO documentacao (tp_documentacao, status, observacao, id_projeto, arquivo)
                        VALUES (%s, %s, %s, %s, %s);
                    """, [tp_documentacao, status, observacao, id_projeto, caminho_arquivo])
                    # Veio da tela de um projeto? Volta para os documentos DELE
                    if id_fixo is not None:
                        return redirect(f"{reverse('lista_documentacao')}?projeto={id_fixo}")
                    return redirect('lista_documentacao')

    # GET: carrega a lista de projetos do usuário pro <select> do form
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.id_projeto, p.endereco_projeto FROM projeto p
            WHERE p.id_usuario = %s ORDER BY p.endereco_projeto;
        """, [usuario_id])
        projetos = cursor.fetchall()

    # projeto_fixo = (id, endereço) SE o id da URL for de um projeto do usuário; senão None.
    # (Como "projetos" só tem projetos do usuário, isso já valida a posse.)
    projeto_fixo = None
    if id_fixo is not None:
        projeto_fixo = next((pr for pr in projetos if pr[0] == id_fixo), None)

    return render(request, 'documentacao/documentacao-form.html', {
        'erro': erro, 'projetos': projetos, 'projeto_fixo': projeto_fixo,
    })


def editar_documento(request, id_documentacao):
    """
    Edita um documento existente. Se um NOVO arquivo for enviado,
    substitui o antigo. Se nenhum arquivo for enviado, mantém o atual.
    """
    if not request.session.get('usuario_id'):
        return redirect('login')
    usuario_id = request.session.get('usuario_id')
    erro = None

    # Primeiro carrega o documento atual (só se for do usuário)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT d.id_documentacao, d.tp_documentacao, d.status, d.observacao, 
                   d.id_projeto, d.arquivo
            FROM documentacao d
            JOIN projeto p ON d.id_projeto = p.id_projeto
            WHERE d.id_documentacao = %s AND p.id_usuario = %s;
        """, [id_documentacao, usuario_id])
        documento = cursor.fetchone()

    if documento is None:
        return redirect('lista_documentacao')

    if request.method == 'POST':
        tp_documentacao = request.POST.get('tp')
        status = request.POST.get('status')
        id_projeto = request.POST.get('projeto')
        observacao = request.POST.get('obs') or None
        arquivo = request.FILES.get('arquivo')

        if not tp_documentacao or not status or not id_projeto:
            erro = "Preencha todos os campos obrigatórios."
        else:
            with connection.cursor() as cursor:
                # Verifica se o projeto escolhido é do usuário
                cursor.execute("""
                    SELECT 1 FROM projeto p
                    WHERE p.id_projeto = %s AND p.id_usuario = %s;
                """, [id_projeto, usuario_id])

                if not cursor.fetchone():
                    erro = "Projeto inválido ou não pertence a você."
                else:
                    # Começa com o arquivo ATUAL; se veio novo, sobrescreve
                    caminho_arquivo = documento[5]
                    if arquivo:
                        pasta = os.path.join(settings.MEDIA_ROOT, 'documentos')
                        os.makedirs(pasta, exist_ok=True)
                        # nome único: evita sobrescrever arquivos e nomes perigosos (../)
                        ext = os.path.splitext(arquivo.name)[1].lower()
                        caminho_arquivo = f"documentos/{uuid.uuid4().hex}{ext}"
                        with open(os.path.join(settings.MEDIA_ROOT, caminho_arquivo), 'wb+') as destino:
                            for chunk in arquivo.chunks():
                                destino.write(chunk)

                    cursor.execute("""
                        UPDATE documentacao 
                        SET tp_documentacao = %s, status = %s, observacao = %s, id_projeto = %s, arquivo = %s
                        WHERE id_documentacao = %s;
                    """, [tp_documentacao, status, observacao, id_projeto, caminho_arquivo, id_documentacao])
                    return redirect('lista_documentacao')

    # GET: carrega os projetos do usuário pro <select>
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.id_projeto, p.endereco_projeto FROM projeto p
            WHERE p.id_usuario = %s ORDER BY p.endereco_projeto;
        """, [usuario_id])
        projetos = cursor.fetchall()

    return render(request, 'documentacao/documentacao-form.html', {
        'erro': erro,
        'projetos': projetos,
        'documento': documento,  # ← usado pelo template pra saber se é edição
    })


def deletar_documento(request, id_documentacao):
    """
    Deleta o documento. O subselect garante que só apaga se
    o projeto dono é do usuário logado.
    """
    if not request.session.get('usuario_id'):
        return redirect('login')
    usuario_id = request.session.get('usuario_id')

    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM documentacao 
            WHERE id_documentacao = %s 
            AND id_projeto IN (
                SELECT p.id_projeto FROM projeto p
                WHERE p.id_usuario = %s
            );
        """, [id_documentacao, usuario_id])

    return redirect('lista_documentacao')