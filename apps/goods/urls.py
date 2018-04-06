
from django.conf.urls import include, url
from django.contrib import admin

from apps.goods import views

urlpatterns = [
    url(r'^index$', views.IndexView.as_view(),name='index'),
    url(r'^detail/(?P<sku_id>\d+)$', views.DetailView.as_view(),name='detail'),
    # 定义每一个类别所有商品的列表
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)$', views.ListView.as_view(),name='list'),
]
