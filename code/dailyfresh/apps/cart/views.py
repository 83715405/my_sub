from django.http.response import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from django_redis import get_redis_connection
from redis.client import StrictRedis

from apps.goods.models import GoodsSKU


class AddCartView(View):
    def post(self, request):
        # 判断用户是否登陆
        if not request.user.is_authenticated():
            return JsonResponse({'code': 1, 'errmsg': '用户为登陆'})
        # 获取请求数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 校验是否为空
        if not all([sku_id, count]):
            return JsonResponse({'code': 2, 'errmsg': '数据不能为空'})
        # 检验商品id是否正确
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 3, 'errmsg': '商品id不存在'})
        try:
            count = int(count)
        except:
            return JsonResponse({'code': 3, 'errmsg': '商品id不存在'})

        # cart_1 = {1:2,2:3}
        strict_redis = get_redis_connection('default')  # type: StrictRedis
        key = 'cart_%s' % request.user.id
        val = strict_redis.hget(key, sku_id)  # bytes
        if val:
            count += int(val)
        # 判断库存
        if sku.stock < count:
            return JsonResponse({'code': 4, 'errmsg': '库存不足'})
        # 设置redis数据库
        strict_redis.hset(key, sku_id, count)
        # 查询购物车中的商品总数量
        total_count = 0
        vals = strict_redis.hvals(key)  # 列表 bytes
        for val in vals:
            total_count += int(val)
        return JsonResponse({'code': 0, 'total_count': total_count})


class CartInfoView(View):
    def get(self, request):
        '''显示购物车界面'''
        # 获取登陆用户id
        user_id = request.user.id
        # 定义一个列表,保存用户购物车中的所有商品
        skus = []
        # 总数量
        total_count = 0
        # 总金额
        total_amount = 0
        # 从redis中查询出当前登陆用户的商品
        # cart_1 = {1:2, 2:3}

        strict_redis = get_redis_connection()  # type StrictRedis
        key = 'cart_%s' % user_id
        # 获取所有的键(商品id) 列表(bytes)
        sku_ids = strict_redis.hkeys(key)
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=int(sku_id))  # bytes
            count = strict_redis.hget(key, sku_id)  # bytes
            amount = sku.price * int(count)
            # 给商品对象新增实例属性, 数量小计金额amount
            sku.count = int(count)
            sku.amount = amount
            # 累计总数量和总金额
            total_count += int(count)
            total_amount += amount
            skus.append(sku)
        # 定义模板数据
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
        }
        return render(request, 'cart.html', context)


class CartUpdateView(View):
    def post(self, request):
        '''修改商品数量'''
        if not request.user.is_authenticated():
            return JsonResponse({'code': 1, 'errmsg': '请先登陆'})
        # 获取参数 sku_id, count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 校验参数合法性
        if not all([sku_id, count]):
            return JsonResponse({'code': 2, 'errmsg': '参数不能为空'})
        # 判断商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 3, 'errmsg': '商品不存在'})
        # 判断是否为整数
        try:
            count = int(count)
        except:
            return JsonResponse({'code': 3, 'errmsg': 'count需为整数'})
        # 判断库存
        if count > sku.stock:
            return JsonResponse({'code': 4, 'errmsg': '库存不足'})
        # 如果用户登陆将修改redis数据
        strict_redis = get_redis_connection()  # type: StrictRedis
        key = 'cart_%s' % request.user.id
        strict_redis.hset(key, sku_id, count)
        # 查询购物车中的商品总数量
        total_count = 0
        vals = strict_redis.hvals(key)
        for val in vals:
            total_count += int(val)
        return JsonResponse({'code': 0, 'total_count': total_count})


class CartDeleteView(View):
    pass
