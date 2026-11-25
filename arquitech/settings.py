import os
from pathlib import Path

# Caminho raiz do projeto (onde fica o manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Chave usada para criptografar sessões, CSRF, etc. EM PRODUÇÃO: usar variável de ambiente!
SECRET_KEY = 'django-insecure-...'

# DEBUG=True → mostra erros detalhados e serve arquivos de mídia
# EM PRODUÇÃO DEVE SER False
DEBUG = True

# Lista de hosts que podem acessar. Em produção, colocar o domínio.
ALLOWED_HOSTS = []

# Apps ativos no projeto: os do Django + os nossos
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Nossos apps:
    'usuarios',
    'clientes',
    'projetos',
    'financeiro',
    'documentacao',
]

# Middlewares = camada que processa cada request antes de chegar na view.
# CSRF protege contra formulários falsos. Sessions guarda o login. Etc.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'arquitech.urls'  # Arquivo principal de rotas

# Configuração do sistema de templates (HTML)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],           # Templates na raiz? Não, usamos os de cada app
        'APP_DIRS': True,     # Procura templates dentro de cada app (templates/)
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Banco de dados PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'arquitech',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Idioma e timezone
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Onde ficam arquivos estáticos (CSS, JS) e de mídia (uploads)
STATIC_URL = 'static/'
MEDIA_URL = '/media/'                              # URL pública: /media/documentos/arquivo.pdf
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')       # Pasta física no HD

# Backend de e-mail (por enquanto só imprime no console, bom pra dev)
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}