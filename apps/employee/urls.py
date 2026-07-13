from django.urls import path
from . import views

app_name = 'employee'

urlpatterns = [
    # ── Main Dashboard ────────────────────────────────────────────────────────
    path('',                                views.portal,               name='portal'),

    # ── CRM ───────────────────────────────────────────────────────────────────
    path('crm/leads/',                      views.lead_list,            name='lead_list'),
    path('crm/leads/new/',                  views.lead_create,          name='lead_create'),
    path('crm/leads/<str:lead_id>/',        views.lead_detail,          name='lead_detail'),
    path('crm/customers/',                  views.customer_list,        name='customer_list'),
    path('crm/customers/<int:pk>/',         views.customer_360,         name='customer_360'),
    path('crm/opportunities/',              views.opportunity_list,     name='opportunity_list'),

    # ── Calling Center ────────────────────────────────────────────────────────
    path('calling/',                        views.call_center,          name='call_center'),
    path('calling/history/',                views.call_history,         name='call_history'),
    path('calling/log/',                    views.log_call,             name='log_call'),
    path('calling/callback/<int:pk>/resolve/', views.callback_resolve,  name='callback_resolve'),
    # Public endpoint (no staff required — customers call this)
    path('calling/request-callback/',       views.request_callback,     name='request_callback'),

    # ── Support Tickets ───────────────────────────────────────────────────────
    path('support/tickets/',                views.ticket_list,          name='ticket_list'),
    path('support/tickets/new/',            views.ticket_create,        name='ticket_create'),
    path('support/tickets/<str:ticket_id>/',views.ticket_detail,        name='ticket_detail'),

    # ── Marketing Campaigns ───────────────────────────────────────────────────
    path('marketing/campaigns/',            views.campaign_list,        name='campaign_list'),
    path('marketing/campaigns/new/',        views.campaign_create,      name='campaign_create'),
    path('marketing/campaigns/<str:camp_id>/', views.campaign_detail,   name='campaign_detail'),

    # ── Collaboration / Internal Notes ────────────────────────────────────────
    path('collab/notes/',                   views.internal_notes,       name='internal_notes'),

    # ── Orders ────────────────────────────────────────────────────────────────
    path('orders/',                         views.order_list,           name='order_list'),
    path('orders/<str:order_id>/',          views.order_detail_emp,     name='order_detail'),
    path('requirements/',                   views.requirement_list,     name='requirement_list'),
    path('requirements/<str:req_id>/',      views.requirement_detail_emp, name='requirement_detail'),

    # ── Products ──────────────────────────────────────────────────────────────
    path('products/',                       views.product_list,         name='product_list'),
    path('products/add/',                   views.product_add,          name='product_add'),
    path('products/bulk-import/',           views.bulk_import,          name='bulk_import'),
    path('products/export/',                views.export_products,      name='export_products'),
    path('products/clear/',                 views.clear_products,       name='clear_products'),
    path('products/<int:pk>/',              views.product_detail,       name='product_detail'),
    path('products/<int:pk>/edit/',         views.product_edit,         name='product_edit'),
    path('products/<int:pk>/delete/',       views.product_delete,       name='product_delete'),

    # ── Reports & Excel Export ────────────────────────────────────────────────
    path('reports/',                        views.reports,              name='reports'),
    path('reports/export/',                 views.export_report_excel,  name='export_excel'),

    # ── Team / Employees ─────────────────────────────────────────────────────
    path('team/',                           views.employee_list,        name='employee_list'),
    path('team/<int:pk>/',                  views.employee_detail,      name='employee_detail'),
    path('team/attendance/',                views.attendance_today,     name='attendance_today'),

    # ── My Profile ───────────────────────────────────────────────────────────
    path('my-profile/',                     views.my_profile,           name='my_profile'),

    # ── Memberships ───────────────────────────────────────────────────────────
    path('memberships/',                    views.memberships_proxy,    name='memberships_admin'),

    # ── Menu / Navigation Hub ─────────────────────────────────────────────────
    path('menu/',                           views.menu,                 name='menu'),
]
