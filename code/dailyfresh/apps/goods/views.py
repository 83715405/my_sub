from django.contrib.redirects.models import Redirect
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django.views.generic.base import View
from django_redis import get_redis_connection
from redis.client import StrictRedis

from apps.goods.models import *


class BaseCartView(View):
    def get_cart_count(self, request):
        cart_count = 0
        if request.user.is_authenticated():
            strict_redis = get_redis_connection()  # type: StrictRedis
            key = 'cart_%s' % request.user.id
            vals = strict_redis.hvals(key)
            for count in vals:
                cart_count += int(count)
        return cart_count


class IndexView(BaseCartView):
    def get(self, request):
        context = cache.get('index_page_data')
        if not context:
            print('没有缓存')
            # 查询商品类别数据
            categories = GoodsCategory.objects.all()
            # 查询商品轮播轮数据
            slide_skus = IndexSlideGoods.objects.all().order_by('index')
            # 查询商品促销活动数据
            promotions = IndexPromotion.objects.all().order_by('index')[0:2]
            for c in categories:
                text_sku = IndexCategoryGoods.objects.filter(display_type=0, category=c)
                image_sku = IndexCategoryGoods.objects.filter(display_type=1, category=c)[0:4]
                c.text_sku = text_sku
                c.image_sku = image_sku
            context = {'categories': categories,
                       'slide_skus': slide_skus,
                       'promotions': promotions,
                       }
            cache.set('index_page_data', context, 60 * 30)
        else:
            print('使用缓存')
        cart_count = self.get_cart_count(request)
        context['cart_count'] = cart_count
        return render(request, 'index.html', context)


class DetailView(BaseCartView):
    def get(self, request, sku_id):
        # 查询商品SKU信息
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return Redirect(reverse('goods:index'))

        # 查询所有商品分类信息
        categories = GoodsCategory.objects.all()
        # 查询最新商品推荐
        try:
            news_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[0:2]
        except:
            news_skus = None
        # 如果已登录，查询购物车信息
        cart_count = self.get_cart_count(request)
        # 查询其他规格商品
        other_skus = GoodsSKU.objects.filter(
            spu=sku.spu).exclude(id=sku_id)

        # 保存用户的浏览记录
        if request.user.is_authenticated():
            strict_redis = get_redis_connection()  # StrictRedis
            key = 'history_%s' % request.user.id
            strict_redis.lrem(key, 0, sku_id)
            strict_redis.lpush(key, sku_id)
            strict_redis.ltrim(key, 0, 4)
        context = {
            'sku': sku,
            'categories': categories,
            'news_skus': news_skus,
            'cart_count': cart_count,
            'other_skus': other_skus
        }
        return render(request, 'detail.html', context)


class ListView(BaseCartView):
    def get(self, request, category_id, page_num):
        '''

        :param request:
        :param category_id: 商品类别id
        :param page_num: 页码
        :return:
        '''
        # 获取请求参数(排序方式)
        sort = request.GET.get('sort')
        # 校验参数合法性
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return Redirect(reverse('goods:index'))
        categories = GoodsCategory.objects.all()
        try:
            new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[0:2]
        except GoodsSKU.DoesNotExist:
            new_skus = None
        if sort == 'price':
            skus = GoodsSKU.objects.filter(category=category).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')
        else:
            skus = GoodsSKU.objects.filter(category=category)
            sort = 'default'
        # 分页内容
        # 分页显示
        # 参数1:一页显示多少条数据
        # 参数2 要分页的数据
        paginator = Paginator(skus, 2)
        try:
            page = paginator.page(page_num)
        except EmptyPage:
            # 页码不存在
            page = paginator.page(1)
        cart_count = self.get_cart_count(request)
        context = {
            'category': category,
            'categories': categories,
            'sort': sort,
            'new_skus': new_skus,
            'page': page,
            'page_range': paginator.page_range,
            'cart_count': cart_count
        }
        return render(request, 'list.html', context)
