from haystack import indexes

from apps.goods.models import GoodsSKU

"""创建索引，方便搜索商品"""

class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    # 针对那张表创建的索引
    text = indexes.CharField(document=True, use_template=True)

    # 通过模板来制定要对那些字段创建索引

    def get_model(self):
        #     要查询那张表，就返回那张表的类
        return GoodsSKU

    def index_queryset(self, using=None):
        #     一般对表中所有的数据进行索引
        return self.get_model().objects.all()
