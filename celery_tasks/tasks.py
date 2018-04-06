# import os
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()

from django.core.mail import send_mail

from dailyfresh import settings
from celery import Celery
from django.template import loader

from apps.goods.models import GoodsCategory, IndexSlideGoods, IndexPromotion, IndexCategoryGoods

# 创建celery应用对象，把函数装饰成celery任务
app = Celery('dailyfresh', broker='redis://127.0.0.1:6379/1')


@app.task
def send_active_email(username, email, token):
    subject = '天天生鲜用户'  # 标题
    message = ''  # 邮件正文（纯文本）
    sender = settings.EMAIL_FROM  # 发件人
    recivers = [email]  # 接受人，需要是列表
    # 邮件正文，带html样式
    html_message = '<h2>尊敬的%s，感谢注册天天生鲜</h2>' \
                   '<p>请点击次链接激活你的证号' \
                   '<a href="http://127.0.0.1:8000/users/active/%s">http://127.0.0.1:8000/users/active/%s</a>' \
                   % (username, token, token)

    send_mail(subject, message, sender, recivers, html_message=html_message)


@app.task
def generate_create_index():

    # # 查询首页商品类别数据
    # catogarys = GoodsCategory.objects.all()
    #
    # # 查询轮播商品
    # slide_skus = IndexSlideGoods.objects.all().order_by('index')
    #
    # # 查询促销商品
    # promots = IndexPromotion.objects.all().order_by('index')
    #
    # # 查询商品类别数据
    # for catogary in catogarys:
    #     text_type = IndexCategoryGoods.objects.filter(category=catogary,display_type=0).order_by('index')
    #     photo_type = IndexCategoryGoods.objects.filter(category=catogary,display_type=1).order_by('index')
    #     catogary.text_type = text_type
    #     catogary.photo_type = photo_type
    #
    #     data = {
    #         'catogarys':catogarys,
    #         'slide_skus':slide_skus,
    #         'promots':promots,
    #     }

    catogarys = GoodsCategory.objects.all()
    # 2.显示轮播商品
    slide_skus = IndexSlideGoods.objects.all().order_by('index')
    # 3.显示促销商品
    promots = IndexPromotion.objects.all().order_by('index')
    # 4.显示商品数据，这个类别中商品属于sku，只是规定商品是以图片或者文字显示
    for catogary in catogarys:
        text_type = IndexCategoryGoods.objects.filter(category=catogary, display_type=0).order_by('index')
        photo_type = IndexCategoryGoods.objects.filter(category=catogary, display_type=1).order_by('index')
        #     动态把商品类别中以文字或者图片显示的商品添加到类别文字或者图片中
        catogary.text_type = text_type
        catogary.photo_type = photo_type


        # 用户未登录的时候

        # 定义购物车中的数量为0

    data = {
        'catogarys': catogarys,
        'slide_skus': slide_skus,
        'promots': promots,

    }

    template = loader.get_template('index.html')
    html_str = template.render(data)
    with open('/home/python/Desktop/static/index.html', 'w') as f:
        f.write(html_str)
