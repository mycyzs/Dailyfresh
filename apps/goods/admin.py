from django.contrib import admin
from django.core.cache import cache

from apps.goods.models import GoodsSKU, GoodsCategory, GoodsSPU, GoodsImage, IndexSlideGoods, IndexCategoryGoods, \
    IndexPromotion

from celery_tasks.tasks import generate_create_index


class BaseAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        generate_create_index.delay()
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        super().delete_model(request, obj)

        generate_create_index.delay()
        cache.delete('index_page_data')


# 定义商品类继承父类，后台数据有所改动时，会调用save和delete方法，重新celery生成静态首页，
class GoodsSKUAdmin(BaseAdmin):
    pass


class GoodsCategoryAdmin(BaseAdmin):
    pass


class IndexCategoryGoodsAdmin(BaseAdmin):
    pass


class IndexPromotionAdmin(BaseAdmin):
    pass


admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(GoodsCategory, GoodsCategoryAdmin)
# admin.site.register(GoodsSPU)
admin.site.register(GoodsImage)
admin.site.register(IndexSlideGoods)
admin.site.register(IndexCategoryGoods, IndexCategoryGoodsAdmin)
admin.site.register(IndexPromotion, IndexPromotionAdmin)


# Register your models here.
