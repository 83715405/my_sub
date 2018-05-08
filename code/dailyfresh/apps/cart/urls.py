from django.conf.urls import url

from apps.cart import views

urlpatterns = [
    # 添加商品到购物车
    url(r'^add$', views.AddCartView.as_view(), name='add'),
    # 更新购物车
    url(r'^update$', views.CartUpdateView.as_view(), name='update'),
    # 删除购物车数据
    url(r'^delete$', views.CartDeleteView.as_view(), name='delete'),
    # 添加商品到购物车
    url(r'^$', views.CartInfoView.as_view(), name='info'),
]
