from django.conf.urls import url, include

from apps.users import views

urlpatterns = [
    # 注册界面 127.0.0.1:8000/users/register
    url(r'^register$', views.RegisterView.as_view(), name='register'),
    # 激活邮件
    url(r'^active/(.+)$', views.ActiveView.as_view(), name='active'),
    # 登陆页面的实现 127.0.0.1:8000/users/login
    url(r'^login$', views.LoginView.as_view(), name='login'),
    # 注销用户页面的实现 127.0.0.1:8000/users/logout
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),

    # 用户订单 127.0.0.1:8000/users/order
    url(r'^orders$', views.UserOrdersView.as_view(), name='order'),
    # 用户地址 127.0.0.1:8000/users/address
    url(r'^address$', views.UserAddressView.as_view(), name='address'),
    # 用户中心 127.0.0.1:8000/users
    url(r'^$', views.UserInfoView.as_view(), name='info')

]
