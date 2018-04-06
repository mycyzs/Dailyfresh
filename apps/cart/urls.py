
from django.conf.urls import include, url
from django.contrib import admin

from apps.cart import views

urlpatterns = [
    url(r'^add$',views.AddView.as_view(),name='add'),
    # 购物车显示界面
    url(r'^$',views.CartNifoView.as_view(),name='info'),
    url(r'^updatecart$',views.UpdateCartView.as_view(),name='update'),
    url(r'^delete$',views.DeleteCartView.as_view(),name='delete'),
]
