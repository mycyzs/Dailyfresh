from audioop import reverse

from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View

# 显示首页
from django_redis import get_redis_connection

from apps.goods.models import GoodsCategory, IndexSlideGoods, IndexPromotion, IndexCategoryGoods, GoodsSKU

# 购物车逻辑函数好几个类都有用到，可以封装一个父模板，子类继承即刻
class BaseCart(View):
    def get_cart_count(self,request):
        cart_count = 0
        # 根据登录的用户，来标识购物车，购物车以哈斯类型存储数据 cart_userid good1 10 good2 20
        # todo 购物车数据
        if request.user.is_authenticated():
            user = request.user
            redis_client = get_redis_connection('default')
            user_id = user.id
            key = 'cart_%s' % user_id
            good_nums = redis_client.hvals(key)
            for value in good_nums:
                cart_count += int(value)
        return cart_count


class IndexView(BaseCart):
    def get(self, request):
        '''显示首页'''
        # 获取缓存数据
        data = cache.get('index_page_data')
        if data is None:
            print('缓存为空')
            # 1.显示商品类别
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

            data = {
                'catogarys': catogarys,
                'slide_skus': slide_skus,
                'promots': promots,

            }
            # 缓存数据:
            # 参数1: 键名
            # 参数2: 缓存的字典数据
            # 参数3: 缓存失效时间1小时

            cache.set('index_page_data', data, 3600)

        else:
            print('使用缓存')

            # 定义购物车中的数量为0
        # cart_count = 0
        # # 根据登录的用户，来标识购物车，购物车以哈斯类型存储数据 cart_userid good1 10 good2 20
        # # todo 购物车数据
        # if request.user.is_authenticated():
        #     user = request.user
        #     redis_client = get_redis_connection('default')
        #     user_id = user.id
        #     key = 'cart_%s' % user_id
        #     good_nums = redis_client.hvals(key)
        #     for value in good_nums:
        #         cart_count += int(value)

        # 继承父类获取购物车商品数量的方法即可
        cart_count = super().get_cart_count(request)

        data.update({'cart_count': cart_count})

        return render(request, 'index.html', data)

    def post(self, request):
        pass


class DetailView(BaseCart):
    # 根据商品id查询商品详情
    def get(self,request,sku_id):
        # 查看商品详情，也有可能不存早

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 查询不到商品返回首页
            return redirect(reverse('goods:index'))

        # 获取所有类别数据
        categories = GoodsCategory.objects.all()

        # 获取最新推荐，同一类别的最新创建的商品,两个商品推荐
        new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[0:2]

        # 获取其他商品，同一商品不同规格
        other_sku = sku.spu.goodssku_set.exclude(id=sku_id)

        # 链接redis数据库，从数据库中读取用户购物车的商品数量
        redis_client = get_redis_connection('default')

        # 获取购物车的数量
        cart_count = super().get_cart_count(request)

        # 用户登录状态，默认用户进入商品详情界面，就把商品添加到用户中心的最近浏览商品
        key = 'history_%s'%request.user.id
        # 移除目前商品的id，添加到左边成为最新浏览商品

        redis_client.lrem(key,0,sku.id)

        # 列表左边插入最新的数据
        redis_client.lpush(key,sku.id)

        # 在redis中最多保存5条历史浏览记录，供用户中心获取浏览记录显示，包括头尾
        redis_client.ltrim(key,0,4)

        # 定义模板数据
        data = {
            'categories':categories,
            'new_skus':new_skus,
            'other_sku':other_sku,
            'cart_count':cart_count,
            'sku':sku,
        }

        return render(request,'detail.html',data)


class ListView(BaseCart):
    # 获取每一类别所有商品的列表
    def get(self,request,category_id,page_num):

        # 判断这个是否存在
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
        #     默认返回首页
            return redirect(reverse('goods:index'))

        # 获取用户传入的sort，如果不传默认用default
        sort = request.GET.get('sort','default')

        # 获取所有商品的类别
        categories = GoodsCategory.objects.all()

        # 获取该类别新品推荐，根据创建时间排序,取两个即可
        new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[0:2]

        # 查询该类别所有商品，并且有sort选择,价格，销量，默认
        if sort == 'price':
            skus = GoodsSKU.objects.filter(category=category).order_by('price')

        elif sort == 'sales':
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')

        else:
            skus = GoodsSKU.objects.filter(category=category)
        #     把sort 设为默认
            sort = 'default'

        # 根据传入的要显示的当前页来显示商品
        page_num = int(page_num)

        # 创建分页器，根据每页显示的数据，django会帮我们算出有多少页
        paginator = Paginator(skus,2)

        # 查看当前页的数据，可能会有异常
        try:
            page = paginator.page(page_num)
        except EmptyPage:
        #     如果传入的页数有误，默认显示第一页
            page = paginator.page(1)

        # 获取页数列表，方便模板循环页数列表创建页数
        page_list = paginator.page_range

        # 获取购物车的数量
        cart_count = super().get_cart_count(request)

        # 创建上下文
        data = {
            'category':category,
            'sort':sort,
            'categories':categories,
            'new_skus':new_skus,
            'skus':skus,
            'page_list':page_list,
            'page':page,
            'cart_count':cart_count,

        }

        return render(request,'list.html',data)



