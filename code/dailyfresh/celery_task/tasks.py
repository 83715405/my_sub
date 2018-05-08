from time import sleep

from celery import Celery
from django.core.mail import send_mail
# import django
# import os
# os.environ.setdefault('DJANGO_SETTINGS_MODULE','dailyfresh.settings')
# from dailyfresh import settings
# django.setup()
from django.template import loader

from apps.goods.models import *
from dailyfresh import settings

app = Celery('dailyfresh', broker='redis://127.0.0.1:6379/1')


@app.task
def send_active_email(user, email, token):
    subject = '天天生鲜激活邮件'  # 标题
    message = ''  # 正文
    from_mail = settings.EMAIL_FROM  # 发件人
    recipient_list = [email]  # 收件人
    html_message = '<h2>尊敬的 %s, 这是一封来自某个正在学python的苦逼小青年的来信,' \
                   '感谢注册天天生鲜</h2>' \
                   '<p>请点击此链接激活您的帐号: ' \
                   '<a href="http://127.0.0.1:8000/users/active/%s">' \
                   'http://127.0.0.1:8000/users/active/%s</a>' \
                   % (user, token, token)
    send_mail(subject, message, from_mail, recipient_list, html_message=html_message)


@app.task
def generate_static_index_page():
    sleep(2)
    # 查询商品类别数据
    categories = GoodsCategory.objects.all()
    # 查询商品轮播轮数据
    slide_skus = IndexSlideGoods.objects.all().order_by('index')
    # 查询商品促销活动数据
    promotions = IndexPromotion.objects.all().order_by('index')[0:2]
    for c in categories:
        text_sku = IndexCategoryGoods.objects.filter(display_type=0, category=c)
        image_sku = IndexCategoryGoods.objects.filter(display_type=1, category=c)[0:4]
        c.text_sku = text_sku
        c.image_sku = image_sku
    cart_count = 0
    context = {'categories': categories,
               'slide_skus': slide_skus,
               'promotions': promotions,
               'cart_count': cart_count}
    template = loader.get_template('index.html')
    html_str = template.render(context)
    path = '/home/python/Desktop/static/index.html'
    with open(path, 'w') as file:
        file.write(html_str)
