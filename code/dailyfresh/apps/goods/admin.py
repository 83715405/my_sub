from django.contrib import admin

# Register your models here.
from apps.goods.models import *
from celery_task.tasks import generate_static_index_page


class BaseAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''在管理后台新增或修改模型数据后调用'''
        super().save_model(request, obj, form, change)
        print('save_model:%s'% obj)
        generate_static_index_page.delay()

    def delete_model(self, request, obj):
        '''在管理后台删除模型数据后调用'''
        super().delete_model(request, obj)
        print('delete_model:%s' % obj)
        generate_static_index_page.delay()


class GoodsCategoryAdmin(BaseAdmin):
    pass


class GoodsSPUAdmin(BaseAdmin):
    pass


class GoodsSKUAdmin(BaseAdmin):
    pass


class IndexSlideGoodsAdmin(BaseAdmin):
    pass


class IndexPromotionAdmin(BaseAdmin):
    pass


class IndexCategoryGoodsAdmin(BaseAdmin):
    pass


admin.site.register(GoodsCategory, GoodsCategoryAdmin)
admin.site.register(GoodsSPU, GoodsSPUAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(IndexSlideGoods, IndexSlideGoodsAdmin)
admin.site.register(IndexPromotion, IndexPromotionAdmin)
admin.site.register(IndexCategoryGoods, IndexCategoryGoodsAdmin)
