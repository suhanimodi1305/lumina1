from django.urls import path
from . import views
from apps.memberships.views import memberships_admin

app_name = 'employee'

urlpatterns = [
    path('',                           views.portal,          name='portal'),
    path('products/',                  views.product_list,    name='product_list'),
    path('products/add/',              views.product_add,     name='product_add'),
    path('products/bulk-import/',      views.bulk_import,     name='bulk_import'),
    path('products/export/',           views.export_products, name='export_products'),
    path('products/clear/',            views.clear_products,  name='clear_products'),
    path('products/<int:pk>/',         views.product_detail,  name='product_detail'),
    path('products/<int:pk>/edit/',    views.product_edit,    name='product_edit'),
    path('products/<int:pk>/delete/',  views.product_delete,  name='product_delete'),
    # Employee accounts
    path('team/',                      views.employee_list,   name='employee_list'),
    path('team/<int:pk>/',             views.employee_detail, name='employee_detail'),

    # Order management
    path('orders/',                       views.order_list,         name='order_list'),
    path('orders/<str:order_id>/',        views.order_detail_emp,   name='order_detail'),

    # Requirement management
    path('requirements/',                 views.requirement_list,        name='requirement_list'),
    path('requirements/<str:req_id>/',    views.requirement_detail_emp,  name='requirement_detail'),
    path('memberships/',                  memberships_admin,              name='memberships_admin'),
]
