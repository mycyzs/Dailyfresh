import re

from django.core.mail import send_mail
from django.core.paginator import Paginator
from django_redis import get_redis_connection
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, request
from django.shortcuts import render, redirect

# Create your views here.
from pymysql import IntegrityError

from apps.goods.models import GoodsSKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import User, Address
from django.views.generic import View

from dailyfresh import settings
from celery_tasks.tasks import send_active_email
from utils.login_required import LoginReqiuredMixin
from apps.users.models import *


class RegisterView(View):
    # 定义类视图，处理注册

    def get(self, request):
        '''处理GET请求，返回注册界面'''
        return render(request, 'register.html')

    def post(self, request):
        '''处理POST请求,返回do_register函数处理注册逻辑'''
        '''注册逻辑'''
        '''获取用户注册的参数'''
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        '''校验参数的合法性'''
        '''逻辑判断0 0.0 '' None [] () {} 都返回False'''
        # all:所有的变量都为True，all函数才返回True，否则返回False

        if not all([username, password, password2, email]):
            return render(request, 'register.html', {'message': '参数不完整！！'})

        # 判断两次密码是否一致
        if password != password2:
            return render(request, 'register.html', {'message': '密码输入不一致！！'})

        # 判断是否勾选了用户协议
        if allow != 'on':
            return render(request, 'register.html', {'message': '请勾选用户协议！！'})

        # 判断邮箱输入是否有误
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'message': '邮箱格式错误！！'})

        # 把用户输入的数据保存到数据库中，create_user：是django提供的方法，会对密码加密后保存到数据库

        try:
            user = User.objects.create_user(username, email, password)

        except IntegrityError:
            return render(request, 'register.html', {'message': '用户名已存在'})

        # 邮箱验证
        # 获取token
        serizar = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 3600)
        token = serizar.dumps({'confirm': user.id})
        token = token.decode()  # 转成字符串类型

        # self.send_active_email(username,email,token)

        # 利用celery异步发送邮件
        send_active_email.delay(username, email, token)

        # 邮件验证
        user.is_active = False
        user.save()

        # todo 发送激活邮件
        # 响应返回html页面,重定向到登陆界面,反向解析
        return redirect(reverse("users:login"))

    # 定义发送邮箱的方法
    # def send_active_email(self, username, email, token):
    #     subject = '天天生鲜用户'  # 标题
    #     message = ''  # 邮件正文（纯文本）
    #     sender = settings.EMAIL_FROM  # 发件人
    #     recivers = [email]  # 接受人，需要是列表
    #     # 邮件正文，带html样式
    #     html_message = '<h2>尊敬的%s，感谢注册天天生鲜</h2>' \
    #                    '<p>请点击次链接激活你的证号' \
    #                    '<a href="http://127.0.0.1:8000/users/active/%s">http://127.0.0.1:8000/users/active/%s</a>' \
    #                    % (username, token, token)
    #
    #     send_mail(subject, message, sender, recivers, html_message=html_message)


class LoginView(View):
    def get(self, request):
        '''进入登陆界面'''
        return render(request, 'login.html')

    def post(self, request):
        '''登陆逻辑实现,验证用户的信息是否正确'''
        # 获取登陆的参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        # 利用all方法验证参数合法性
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '参数有误！！'})

        # 通过django提供的anthenticate方法可以验证用户名和密码是否跟注册时一致！！user就是当前的用户
        user = authenticate(username=username, password=password)

        # 用户名或者密码不正确时
        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名或密码有误，请重新输入！！'})

        # 验证邮箱是否激活
        if not user.is_active:
            return render(request, 'login.html', {'errmsg': '请先激活邮箱'})

        login(request, user)
        # 通过django提供的login方法，保存登陆用户状态,登录就是要保持状态，保存在session中（底层是使用session保存数据）
        #内置方法保存用户的信息，session键值对数据
        # 用户是否勾选,set_expiry可以设置session数据的过期时间

        if remember != 'on':
            request.session.set_expiry(0)

        else:
            request.session.set_expiry(None)

        '''登陆成功直接返回首页'''
        next_url = request.GET.get('next')
        if next_url is None:
            return redirect(reverse("goods:index"))
        else:
            """从哪里来回到哪里去"""
            return redirect(next_url)


class LogoutView(View):
    def get(self, request):

        logout(request)

        return redirect(reverse('goods:index'))


class ActiveView(View):
    """激活用户状态"""
    def get(self, requset, token):
        try:
            seriazer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 3600)
            my_dict = seriazer.loads(token)
            user_id = my_dict['confirm']
        except SignatureExpired:
            return HttpResponse('激活链接已过期')

        # 把数据库的激活状态改为以激活
        User.objects.filter(id=user_id).update(is_active=True)
        return redirect(reverse('users:login'))

# 进入订单界面,购物车提交订单返回订单显示界面,订单界面分页显示
class UserOrderView(LoginReqiuredMixin, View):
    # get方法取值
    def get(self, request,page_num):

        # 查询用户所有的订单,最新的订单最先显示
        orders = OrderInfo.objects.filter(user=request.user).order_by('-create_time')

        # 循环所有的订单
        for order in orders:
        #     查看一个订单所有的商品，订单商品表查看
            order_skus = OrderGoods.objects.filter(order=order)
        #     循环每个商品
            for order_sku in order_skus:
        #         获取每个商品的小计金额，
                order_sku_amount = order_sku.count * order_sku.price
        #         给新增属性
                order_sku.amount = order_sku_amount

        # 订单的总价格，加上邮费,新增订单属性
            order.total_pay = order.total_amount + order.trans_cost
            order.skus = order_skus
            order.status_desc = OrderInfo.ORDER_STATUS.get(order.status)


        # 订单页面分页显示
        #     创建分页器
            paginator = Paginator(orders,2)

        #     每页显示的数据,捕获异常，没有的页数默认显示第一页
            try:
                page = paginator.page(page_num)
            except Exception as e:
                page = paginator.page(1)
        # 页数列表
            page_range = paginator.page_range

        #     构造上下文

        data = {
                'page_num':page_num,
                'orders':orders,
                'page':page,
                'page_range':page_range,
                'num':1,


                }

        return render(request, 'user_center_order.html', data)


class UserAddressrView(LoginReqiuredMixin, View):
    def get(self, request):
        user = request.user
        try:
            # 拿到用户添加的最新地址，根据地址创建时间
            address = user.address_set.latest('create_time')
        except Exception:
            address1 = None

        data = {
            'num': 2,
            'address': address,

        }

        return render(request, 'user_center_site.html', data)

    def post(self, request):

        user = request.user
        name = request.POST.get('username')
        address = request.POST.get('useraddress')
        email = request.POST.get('useremail')
        moble = request.POST.get('usermoble')
        # 验证参数的合法性
        if not all([name, address, moble]):
            return render(request, 'user_center_site.html', {'errmsg': '参数不为空'})

        # 保存数据到数据库，对应地址表单,django的create方法
        Address.objects.create(
            receiver_name=name,
            receiver_mobile=moble,
            detail_addr=address,
            zip_code=email,
            user=user,
        )

        return redirect(reverse('users:address'))


class UserInfoView(LoginReqiuredMixin, View):
    def get(self, request):
        user = request.user
        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None
        # django网站链接redis数据库，从中取出客户浏览过的商品记录
        strict_redis = get_redis_connection('default')
        # 根据用户id显示最近浏览的商品
        key = 'history_%s' % request.user.id
        # 查询最近浏览的5条数据
        good_ids = strict_redis.lrange(key, 0, 4)
        # 获取到的商品id用list方式存储
        # good_ids = [1,2,3,5,4]
        # 为了防止用filter查找出商品id的时候顺序会改变，所以定义一个空的列表，一个一个添加
        skus = []
        for id in good_ids:
            try:

                goods = GoodsSKU.objects.get(id=id)
                skus.append(goods)
            except GoodsSKU.DoesNotExist:
                pass

        data = {
            'num': 3,
            'address': address,
            'skus': skus,
        }
        return render(request, 'user_center_info.html', data)
