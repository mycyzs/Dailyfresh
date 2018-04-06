from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View
# Create your views here.
from django_redis import get_redis_connection
from redis.client import StrictRedis

from apps.goods.models import GoodsSKU

# 添加商品到购物车
from utils.login_required import LoginReqiuredMixin

# 添加商品到购物车
class AddView(View):
    #  购物车
    def post(self, request):
        #      获取前端页面传过来的用户id，商品id，商品数量，先查找购物车同种商品的数量，
        # 比较库存，再跟购物车所有的数量相加，把总数两返回到前端显示在购物车
        # 成功响应就范会{'code':0}

        #      判断用户是否登录
        if not request.user.is_authenticated():
            return JsonResponse({'code': 1, 'errmsg': '请先登录'})

            #      获取前端传过来的参数
        user_id = request.user.id
        sku_id = request.POST.get('sku_id')
        num = request.POST.get('num')

        # 验证数据的合法性，空的，0,0.0
        if not all([sku_id, num]):
            return JsonResponse({'code': 2, 'errmsg': '数据不合法'})

            #  验证num是否为整数,捕获一下异常
        try:
            num = int(num)
        except Exception:
            return JsonResponse({'code': 3, 'errmsg': '数量不合法'})

            #      验证商品是否存在数据库，也要捕获异常
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 4, 'errmsg': '商品不存在'})

            #      用户购物车的商品存在redis数据中，把用户在redis的商品取出来
            #      首先要链接redis数据，才能操作redis数据库，根据建取值，cart_用户id
        strict_redis = get_redis_connection()

        # strict_redis = StrictRedis()
        key = 'cart_%s' % user_id

        #      取到同种商品在redis中的数量
        sku_nums = strict_redis.hget(key, sku_id)

        #      跟用户刚传过来的同种商品数量相加，再进行库存校验
        if sku_nums:
            num += int(sku_nums)

        if num > sku.stock:
            return JsonResponse({'code': 5, 'errmsg': '库存不足'})

            #  更新商品的数量
        strict_redis.hset(key, sku_id, num)

        #      取出购物车中所有的商品数量,一个列表
        vals = strict_redis.hvals(key)
        count = 0
        for val in vals:
            count += int(val)

            #  构造上下文
        data = {
            'code': 0,
            'message': '成功添加商品到数据库',
            'count': count

        }
        return JsonResponse(data)
        # 前端利用ajax来获取数据

# 显示购物车界面
class CartNifoView(LoginReqiuredMixin,View):
    # 那拿数据get方法就好
    def get(self,request):
    #     判断用户是否登录，用django提供的检验登录状态的方法,继承LoginReqiuredMixin
    #     链接redis数据库，取出所有商品的id和数量
        strict_redis = get_redis_connection()
        user_id = request.user.id
        key = 'cart_%s'%user_id
        # 根据用户id拿到所有的商品，getall拿到的是字典{商品id，num}
        goods_dict = strict_redis.hgetall(key)

        skus = []
        total_num = 0
        total_price = 0

        for sku_id,num in goods_dict.items():
            # 渠道商品
            sku = GoodsSKU.objects.get(id = sku_id)
            #  商品对应的数量

            # 给实例对象新增两个属性
            sku.num = int(num)
            sku.amount = sku.price *sku.num

            #    所有商品的总价
            total_price += sku.amount
                #  所有商品的数量
            total_num += sku.num

            skus.append(sku)

#         构造上下文
        data = {
            'skus':skus,
            'total_price':total_price,
            'total_num':total_num,

        }

        return render(request,'cart.html',data)

# 当用户在购物车页面点击加减时数据需要保存到数据库，不是单纯的页面修改，要跟数据库作库存比较
class UpdateCartView(View):
#     获取页面传过来的商品id和商品数量，获取最终的数量传过来

    def post(self,request):
    # 判断用户是否登录
        if not request.user.is_authenticated():
            # 定义code，用来区分响应成功与失败
            return JsonResponse({'code':1,'errmsg':'请先登录'})

        #  获取参数
        sku_id = request.POST.get('sku_id')
        num = request.POST.get('num')
        user_id = request.user.id

        #  判断参数的合法性
        if not all([sku_id,num]):
            return JsonResponse({'code':2,'errmsg':'参数不合法'})

        #  判断数量格式是否正确，异常
        try:
            num = int(num)
        except Exception:
            return JsonResponse({'code':3,'errmsg':'数量不合法'})

        # 验证商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code':4,'errmsg':'商品不存才'})

            # 判断库存
        if num > sku.stock:
            return JsonResponse({'code':5,'errmsg':'库存不足'})

            # 链接redis数据库
        strict_redis = get_redis_connection()

        # 更新商品再redis中数量
        key = 'cart_%s'%user_id
        strict_redis.hset(key,sku_id,num)

        # 获取所有商品的总数量
        count = 0
        vals = strict_redis.hvals(key)
        for val in vals:
            count += int(val)


        #  构造上下文
        data = {
            'code':0,
            'message':'修改数量成功',
            'count':count,
        }
        return JsonResponse(data)

# 根据用户要删除的商品id要把购物车中的商品删除掉
class DeleteCartView(View):
    def post(self,request):
    #     判断用户是否登录
        if not request.user.is_authenticated():
            return JsonResponse({'code':1,'errmsg':'请先登类'})

    #     获取商品id
        sku_id = request.POST.get('sku_id')

    #     判断商品id
        if not sku_id:
            return JsonResponse({'code':1,'errmsg':'商品id部位空'})

    # 验证商品是否存在
        try:
            sku = GoodsSKU.objects.get(id = sku_id)
        except Exception:
            return JsonResponse({'code':1,'errmsg':'商品不存在'})

    #     链接redis数据库
        strict_redis = get_redis_connection()
        key = 'cart_%s'%request.user.id

    #     根据商品id删除
        strict_redis.hdel(key,sku_id)

        return JsonResponse({'code':0,'message':'删除商品成功'})
    # 前端编写js代码
