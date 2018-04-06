
from django.conf.urls import include, url
from django.contrib import admin

from apps.orders import views

urlpatterns = [

    url(r'^pay$', views.OrderPayView.as_view(),name='pay' ),
    url(r'^commit$', views.OrderCommitView.as_view(),name='commit' ),
    url(r'^lastpay$', views.OrderLastPayView.as_view(),name='lastpay' ),
    url(r'^check$', views.OrderCheckView.as_view(),name='check' ),
]
