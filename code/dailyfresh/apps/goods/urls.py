from django.conf.urls import url


from apps.goods import views

urlpatterns = [
    url('^index$', views.IndexView.as_view(), name='index'),
    # 商品详情表 127.0.0.1:8000/goods/detail/商品id
    url('^detail/(\d+)$', views.DetailView.as_view(), name='detail'),
    # 商品列表 127.0.0.1:8000/goods/list/categories_id/page_num?=default
    url('^list/(\d+)/(\d+)$', views.ListView.as_view(), name='list'),
]