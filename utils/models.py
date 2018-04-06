from django.db import models

# Create your models here.

# dailyfresh/utils/models.py
class BaseModel(models.Model):
    """模型类基类"""

    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # 最后修改时间
    update_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    # 删除标识
    delete = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta(object):
        # 需要指定基类模型类为抽象的,否则迁移生成表时会出错
        abstract = True
