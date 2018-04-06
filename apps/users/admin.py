from django.contrib import admin

from apps.goods.models import GoodsSPU
from apps.users.models import TestModel, User

admin.site.register(TestModel)
admin.site.register(GoodsSPU)
admin.site.register(User)