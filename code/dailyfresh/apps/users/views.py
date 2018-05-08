import re

from django.contrib.auth import authenticate, login, logout
from django.core.signing import SignatureExpired
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from django_redis import get_redis_connection

from itsdangerous import TimedJSONWebSignatureSerializer

from apps.goods.models import GoodsSKU
from apps.users.models import User, Address
from celery_task.tasks import send_active_email
from dailyfresh import settings
from utils.loginque import LoginRequiredView


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 获取注册信息
        name = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 校验信息是否为空
        if not all([name, password, password2, email]):
            return render(request, 'register.html', {'errmsg': '参数不能为空'})
        if password != password2:
            return render(request, 'register.html', {'errmsg': '两次密码不一致'})
        if not re.match('^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱不合法'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请勾选用户协议'})

        # 业务处理
        # 保存用户信息到数据库
        user = None
        try:
            user = User.objects.create_user(name, email, password)  # type: User
            user.is_active = False
            user.save()
        except IntegrityError:
            return render(request, 'register.html', {'errmsg': '用户名重复'})
        token = user.generate_active()
        send_active_email.delay(name, email, token)
        return HttpResponse('注册成功,返回登陆页面')


class ActiveView(View):
    def get(self, requset, token: str):
        ''' :param requset:
        :param token: 对字典{'confiRm':用户id}加密的字符串
        :return: '''

        try:
            s = TimedJSONWebSignatureSerializer(settings.SECRET_KEY)
            dict_data = s.loads(token.encode())

        except SignatureExpired:
            return HttpResponse('激活链接失效')
        user_id = dict_data.get("confirm")
        User.objects.filter(id=user_id).update(is_active=True)
        return HttpResponse('激活成功,进入登陆界面')


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        if not all([username, password]):
            return render(request, 'login.html', {'revmsg': '参数不能为空'})
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'revmsg': '用户不存在'})
        if user.is_active == False:
            return render(request, 'login.html', {'revmsg': '用户未激活'})
        if remember == 'on':
            request.session.set_expiry(None)
        else:
            request.session.set_expiry(0)
        login(request, user)
        next = request.GET.get('next')
        if next:
            return redirect(next)
        else:
            return redirect(reverse('goods:index'))


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


class UserOrdersView(LoginRequiredView, View):
    def get(self, request):
        context = {'which_page': 1,

                   }
        return render(request, 'user_center_order.html', context)


class UserAddressView(LoginRequiredView, View):
    def get(self, request):
        try:
            address = Address.objects.filter(user=request.user).order_by('-create_time')[0]
        except Exception:
            address = None
        context = {
            'address': address,
            'which_page': 2,
        }
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        recver = request.POST.get('recver')
        send_add = request.POST.get('send_add')
        pos_id = request.POST.get('pos_id')
        cel = request.POST.get('cel')
        if not all([recver, send_add, cel]):
            return render(request, 'user_center_site.html', {'errmsg': '参数不能为空'})
        Address.objects.create(receiver_name=recver,
                               receiver_mobile=cel,
                               detail_addr=send_add,
                               zip_code=pos_id,
                               user=request.user, )
        return redirect(reverse('users:address'))


class UserInfoView(LoginRequiredView, View):
    def get(self, request):
        # 获取strict_redis对象
        strict_redis = get_redis_connection() # type: strict_redis
        key = 'history_%s' % request.user.id
        # 0, 4 表示之获取前五个元素
        sku_ids = strict_redis.lrange(key, 0, 4)
        sku_list = []
        for sku_id in sku_ids:
            skus = GoodsSKU.objects.get(id=int(sku_id))
            sku_list.append(skus)
        # skus = GoodsSKU.objects.filter(id__in=sku_ids)

        try:
            address = Address.objects.filter(user=request.user).order_by('-create_time')[0]
        except:
            address = None
        context = {'which_page': 3,
                   'address': address,
                   'skus': sku_list}
        return render(request, 'user_center_info.html', context)
