
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required

from apps.users import views

urlpatterns = [
    # 1.视图函数方法
    # url(r'^register$',views.register,name='register'),
    # url(r'^do_register$',views.do_register,name='do_register'),

#     2.类视图方法
    url(r'^register$',views.RegisterView.as_view(), name='register'),
    url(r'^login$',views.LoginView.as_view(), name='login'),
    url(r'^logout$',views.LogoutView.as_view(), name='logout'),
    url(r'^active/(?P<token>.+)$',views.ActiveView.as_view(), name='active'),
    # 用户中心
    url(r'^order/(?P<page_num>\d+)$', views.UserOrderView.as_view(), name='order'),
    url(r'^address$', views.UserAddressrView.as_view(), name='address'),
    url(r'^$', views.UserInfoView.as_view(), name='info'),

]
