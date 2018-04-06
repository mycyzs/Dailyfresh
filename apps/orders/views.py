from time import sleep

from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from datetime import datetime

# Create your views here.

# 确认订单，购物车界面post请求，把参数传递过来，只需要商品id即可
from django_redis import get_redis_connection

from apps.goods.models import GoodsSKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address
from utils.login_required import LoginReqiuredMixin

# 购物车界面去结算，逻辑实现
class OrderPayView(LoginReqiuredMixin,View):
    # 判断用户是否登录
    def post(self,request):
        # 获取sku_ids，一建多值
        sku_ids = request.POST.getlist('sku_ids')

#         把商品id转成字符串，提交订单的时候传得是字符串，多个id
        sku_ids_str = ','.join(sku_ids)

#         验证参数的合法性，如果没有参数，则重定向到购物车界面，重新选择商品
        if not sku_ids:
            return redirect(reverse('cart:info'))

        #         redis中获取商品的数量
        strict_redis = get_redis_connection()
        key = 'cart_%s' % request.user.id
        # 定义商品列表，所有商品的总价，所有商品的总数
        skus = []
        total_amout = 0
        total_num = 0
        trans_cost = 10


#       查询商品
        for sku_id in sku_ids:
            try:
                sku = GoodsSKU.objects.get(id = sku_id)
            except GoodsSKU.DoesNotExist:
                return redirect(reverse('cart:info'))
            # 获取商品数量
            num = strict_redis.hget(key, sku_id)

            # 判断库存
            try:
                if int(num) > sku.stock:
                    return redirect(reverse('cart:info'))
            except Exception:
                return redirect(reverse('goods:index'))

            # 给实例对象添加属性
            sku.num = int(num)
            sku.amount = int(num) * sku.price

            # 根据循环得到所有商品的总价
            total_amout += int(num) * sku.price
            total_num += int(num)

            skus.append(sku)

#         实付金额，加上邮费
            total_money = total_amout + trans_cost

#             查询用户地址,获取最新地址,捕获一下异常
        try:
            address = Address.objects.filter(user=request.user).latest('create_time')
        except Address.DoesNotExist:
            address = None


#         构造上下文
        data = {
            'skus':skus,
            'total_money':total_money,
            'trans_cost':trans_cost,
            'address':address,
            'total_num':total_num,
            'total_amount':total_amout,
            'sku_ids_str':sku_ids_str,

        }

        return render(request,'place_order.html',data)

# 提交订单，逻辑实现，获取用户地址，商品的id，支付方式，后台跟前台是通过ajax联通，故判断用户是否登录不可以重定向
class OrderCommitView(View):
    # 创建订单
    # 开启事务
    # 在执行sql语句时，如果不添加装饰器，会默认开启事务，自动提交
    @transaction.atomic
    def post(self,request):

#         判断用户是否登录
        if not request.user.is_authenticated():
            return JsonResponse({'code':1,'errmsg':'倾向登录'})

#         获取用户地址，商品id，支付方式,sku_id是字符串格式   '1,2,3'
        address_id = request.POST.get('address_id')
        sku_ids_str = request.POST.get('sku_ids_str')
        pay_method = request.POST.get('pay_method')
        # 把字符串的商品id转成列表
        sku_ids = sku_ids_str.split(',')

# 验证参数合法性
        if not all([address_id,sku_ids_str,pay_method]):
            return JsonResponse({'code':1,'errmsg':'参数不合法'})


#         判断用户地址是否存在
        try:
            address = Address.objects.get(id = address_id)

        except Address.DoesNotExist:
            return JsonResponse({'code':1,'errmsg':'地址不存在'})

#         开始创建订单信息表
        user = request.user

#         1.手动生成订单的id号
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

#       编辑订单信息字段赋值，total_count,total_amount根据每种商品的数量和总价再来修改

        total_count = 0
        total_amount = 0
        trans_cost = 10

# 创建一个保存点，后面如果发生类异常就回滚到这个保存点,可以创建多个
        poit = transaction.savepoint()

#         创建订单信息表
        try:
            order = OrderInfo.objects.create(

                order_id = order_id,
                total_amount = 0,
                total_count = 0,
                trans_cost = trans_cost,
                pay_method = pay_method,
                user = user,
                address = address,
            )

    #         链接redis根据商品id查询相关商品信息
            strict_redis = get_redis_connection()
            key = 'cart_%s'%user.id

    #         遍历商品id列表
            for sku_id in sku_ids:

    #             判断商品是否存在
                try:
                    sku = GoodsSKU.objects.get(id = sku_id)
                except GoodsSKU.DoesNotExist:
                    transaction.savepoint_rollback(poit)    #发生异常就回滚
                    return JsonResponse({'code':1,'errmsg':'商品不存在'})

    #             获取商品的数量
                sku_num = strict_redis.hget(key,sku_id)
                sku_num = int(sku_num)     #bite--->整数

    #         判断库存
                if sku_num > sku.stock:
                    transaction.savepoint_rollback(poit)    #回滚
                    return JsonResponse({'code':1,'errmsg':'库存不足'})



    #           保存订单商品到订单商品表，一个订单可以有多种商品，一对多的关系
    #           一个订单商品表只保存一种商品，创建订单商品表
                OrderGoods.objects.create(
                    count = sku_num,
                    price = sku.price,
                    order = order,
                    sku = sku,
                )

    #         相对应的提交了订单，商品的库存应该减少,销量应该增加
                sku.stock -= sku_num
                sku.sales += sku_num
                sku.save()

    #          计算所有商品的总价和数量

                total_count += sku_num
                total_amount += (sku_num * sku.price)

        except Exception as e:
            transaction.savepoint_rollback(poit)
            return JsonResponse({'code':1,'errmsg':'创建订单失败'})

#         手动提交事务
        transaction.savepoint_commit(poit)

#         修改订单信息表的总价和总数字段

        order.total_amount = total_amount
        order.total_count = total_count
        order.save()

# 从redis中删除购物车中的商品
#             *[1,2]位置参数删除
        strict_redis.hdel(key,*sku_ids)

        return JsonResponse({'code':0,'message':'订单提交成功'})
#     前端ajax实现
# 订单商品表
# 1 | 2018-04-03 13:25:05.954601 | 2018-04-03 13:25:05.954634 |      0 |     2 |  56.60 |         | 2018040321250512 |      8 |
# 2 | 2018-04-03 13:25:07.803814 | 2018-04-03 13:25:07.803847 |      0 |     2 | 100.90 |         | 2018040321250512 |      9 |








# 订单支付,点击取付款，把订单号传过来,返回json数据，ajax获取数据，刷新页面,只是条用支付窗口实现
class OrderLastPayView(View):
    def post(self,request):
        # 判断登录
        if not request.user.is_authenticated():
            return JsonResponse({'code':1,'errmsg':'请先登录'})
            # 获取订单id
        order_id = request.POST.get('order_id')

            # 验证订单的合法性
        if not all([order_id]):
            return JsonResponse({'code': 1, 'errmsg': '参数不合法'})

            # 验证订单是否存在
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          status=1,
                                          user=request.user)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code': 1, 'errmsg': '订单不存在'})

            # t通过第三方sdk，调用支付宝接口，实现支付功能
            # 初始化
        from alipay import AliPay
        app_private_key_string = open("/home/python/study/dailyfresh/apps/orders/app_private_key.pem").read()
        alipay_public_key_string = open("/home/python/study/dailyfresh/apps/orders/alipay_public_key.pem").read()

        alipay = AliPay(
            appid="2016091000481266",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2   # 使用RSA测试会有问题
            debug=True  # 默认False, 如果是True表示使用沙箱环境
        )

        # 2. 调用支付接口
        # 电脑网站支付，需要跳转到:
        # https://openapi.alipay.com/gateway.do? + order_string
        # 订单的实付金额
        total_pay = order.total_amount + order.trans_cost

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单号
            total_amount=str(total_pay),  # 注意: 不能传递total_pay
            subject="天天生鲜测试订单",
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

#         响应浏览器
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string

        return JsonResponse({'code':0,'pay_url':pay_url})


# 查询支付结果，循环去查询
class OrderCheckView(View):
    def post(self,request):
        # 支付结果查询
        if not request.user.is_authenticated():
            return JsonResponse({'code':1,'errmsg':'请先登路'})

        order_id = request.POST.get('order_id')

        if not order_id:
            return JsonResponse({'code': 2, 'message': '订单id不能为空'})

            # 查询订单是否存在
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          status=1,  # 表示待支付
                                          user=request.user)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code': 3, 'message': '订单无效'})

            # t通过第三方sdk，调用支付宝接口，实现支付功能
            # 初始化
        from alipay import AliPay
        app_private_key_string = open("/home/python/study/dailyfresh/apps/orders/app_private_key.pem").read()
        alipay_public_key_string = open("/home/python/study/dailyfresh/apps/orders/alipay_public_key.pem").read()

        alipay = AliPay(
            appid="2016091000481266",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2   # 使用RSA测试会有问题
            debug=True  # 默认False, 如果是True表示使用沙箱环境
        )

        '''
                response = {
                    "trade_no": "2017032121001004070200176844",
                    "code": "10000",
                    "invoice_amount": "20.00",
                    "open_id": "20880072506750308812798160715407",
                    "fund_bill_list": [
                      {
                        "amount": "20.00",
                        "fund_channel": "ALIPAYACCOUNT"
                      }
                    ],
                    "buyer_logon_id": "csq***@sandbox.com",
                    "send_pay_date": "2017-03-21 13:29:17",
                    "receipt_amount": "20.00",
                    "out_trade_no": "out_trade_no15",
                    "buyer_pay_amount": "20.00",
                    "buyer_user_id": "2088102169481075",
                    "msg": "Success",
                    "point_amount": "0.00",
                    "trade_status": "TRADE_SUCCESS",
                    "total_amount": "20.00"
                }
                '''

        # 判断订单是否支付成功
        while(True):
            response = alipay.api_alipay_trade_query(out_trade_no=order_id)
            # 获取响应参数
            code = response.get('code')  #响应状态吗

            trade_no = response.get('trade_no')  #交易好

            trade_status = response.get('trade_status')   #订单支付状态

            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                print('888888888888888888')
                # 修改的订单的支付状态为"待评价" ("待收货")
                order.status = 4  # 待评价
                # 保存支付宝交易号到订单信息表中
                order.trade_no = trade_no
                # 修改订单
                order.save()
                # 响应请求,返回 json数据
                return JsonResponse({'code': 0, 'message': '订单支付成功'})

            elif code == '40004' or (code == '10000' and trade_status == 'WAIT_BUYER_PAY'):
                # 40004: 业务暂时处理失败,需要等待一会, 再次请求,可能就会成功
                sleep(2)

                continue
            else:
                # 支付失败
                print('code=%s' % code)
                print('trade_status=%s' % trade_status)
                return JsonResponse({'code': 1, 'errmsg': '订单支付失败'})



