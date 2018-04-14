"""
Django settings for dailyfresh project.

Generated by 'django-admin startproject' using Django 1.8.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

from django.conf.global_settings import STATICFILES_DIRS, DEFAULT_FILE_STORAGE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '*z6w35u#&1yj$_q&-9cz$l*1q+tkjm9z!vpzc@l6)j=sj_#=we'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = 'False'

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.users',
    'apps.orders',
    'apps.goods',
    'apps.cart',
    'tinymce',
    'haystack',
)

# 配置搜索引擎后端
HAYSTACK_CONNECTIONS = {
    'default': {
        # 使用whoosh引擎：提示，如果不需要使用jieba框架实现分词，就使用whoosh_backend
        # 'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
            # 使用whoosh搜索引擎(使用jiebar中文分词工具)
        'ENGINE': 'haystack.backends.whoosh_cn_backend.WhooshEngine',
        # 索引文件路径
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
    }
}
# 当添加、修改、删除数据时，自动生成索引
# /home/python/.virtualenvs/django_py3/lib/python3.5/site-packages

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# 设置全文检索结果每页显示2条数据
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 1

TINYMCE_DEFAULT_CONFIG = {
    'theme': 'advanced',  # 丰富样式
    'width': 600,
    'height': 400,
}

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'dailyfresh.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dailyfresh.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dg_dailyfresh',
        'USER': 'root',
        'PASSWORD': 'mysql',
        'HOST': 'localhost',
        'PORT': '3306'
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

DEFAULT_FILE_STORAGE = 'utils.fdfs.storage.FdfsStorage'

AUTH_USER_MODEL = 'users.User'

# todo 注册完邮箱改参数
# 邮件发送配置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # 导入邮件模块
EMAIL_HOST = 'smtp.163.com'  # 发邮件主机
EMAIL_PORT = 25  # 发邮件端口
EMAIL_HOST_USER = 'mycyzs@163.com'  # 发件人邮件
EMAIL_HOST_PASSWORD = 'lhf123'  # 邮箱授权时获得授权码，非注册登录密码
EMAIL_FROM = '天天生鲜<mycyzs@163.com>'  # 邮件中的显示的发件人, 邮箱需要与发件人邮箱一致

LOGIN_URL = '/users/login'

# 配置缓存数据到redis数据库，django和redis数据库的交互
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/7",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": ""  # Redis密码，默认为空
        }
    }
}

STATIC_ROOT = '/home/python/Desktop/static'

# session数据缓存到Redis中
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"