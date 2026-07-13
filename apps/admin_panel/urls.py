from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # ── Dashboard ──────────────────────────────────────────────────────────
    path('',                            views.dashboard,          name='dashboard'),
    path('kpis/',                       views.dashboard_kpis,     name='kpis'),

    # ── User Management ────────────────────────────────────────────────────
    path('users/',                      views.user_list,          name='user_list'),
    path('users/<int:pk>/',             views.user_detail,        name='user_detail'),
    path('users/<int:pk>/edit/',        views.user_edit,          name='user_edit'),

    # ── Employee Management ────────────────────────────────────────────────
    path('employees/',                  views.emp_list,           name='emp_list'),
    path('employees/add/',              views.emp_add,            name='emp_add'),
    path('employees/<int:pk>/',         views.emp_detail,         name='emp_detail'),
    path('employees/<int:pk>/edit/',    views.emp_edit,           name='emp_edit'),
    path('employees/<int:pk>/delete/',  views.emp_delete,         name='emp_delete'),
    path('employees/departments/',      views.dept_list,          name='dept_list'),

    # ── Attendance ─────────────────────────────────────────────────────────
    path('attendance/',                 views.attendance_overview, name='attendance'),

    # ── Salary ─────────────────────────────────────────────────────────────
    path('salary/',                     views.salary_list,        name='salary_list'),
    path('salary/add/',                 views.salary_add,         name='salary_add'),

    # ── Leave ──────────────────────────────────────────────────────────────
    path('leave/',                      views.leave_list,         name='leave_list'),
    path('leave/<int:pk>/action/',      views.leave_action,       name='leave_action'),

    # ── Orders ─────────────────────────────────────────────────────────────
    path('orders/',                     views.order_list,         name='order_list'),
    path('orders/add/',                 views.order_add,          name='order_add'),
    path('orders/<str:order_id>/',      views.order_detail,       name='order_detail'),
    path('orders/<str:order_id>/edit/', views.order_edit,         name='order_edit'),
    path('orders/<str:order_id>/delete/', views.order_delete,     name='order_delete'),

    # ── Products ───────────────────────────────────────────────────────────
    path('products/',                   views.product_list,       name='product_list'),
    path('products/add/',               views.product_add_admin,  name='product_add'),
    path('products/<int:pk>/edit/',     views.product_edit_admin, name='product_edit'),
    path('products/<int:pk>/delete/',   views.product_delete_admin, name='product_delete'),

    # ── CRM ────────────────────────────────────────────────────────────────
    path('crm/',                        views.crm_overview,       name='crm'),
    path('crm/leads/',                  views.crm_leads,          name='crm_leads'),
    path('crm/leads/<str:lead_id>/edit/', views.crm_lead_edit,   name='crm_lead_edit'),
    path('crm/opportunities/',          views.crm_opportunities,  name='crm_opportunities'),
    path('crm/calling/',                views.crm_calling,        name='crm_calling'),
    path('crm/support/',                views.crm_support,        name='crm_support'),
    path('crm/support/<str:ticket_id>/', views.crm_ticket_detail, name='crm_ticket_detail'),
    path('crm/campaigns/',              views.crm_campaigns,      name='crm_campaigns'),
    path('crm/notes/',                  views.crm_notes,          name='crm_notes'),
    path('crm/reports/',                views.crm_reports,        name='crm_reports'),

    # ── Analytics ──────────────────────────────────────────────────────────
    path('analytics/',                  views.analytics,          name='analytics'),
    path('reports/export/',             views.export_report,      name='export_report'),

    # ── Settings ───────────────────────────────────────────────────────────
    path('settings/',                   views.settings_view,      name='settings'),

    # ── Tasks ──────────────────────────────────────────────────────────────
    path('tasks/',                      views.task_list,          name='task_list'),
    path('tasks/<int:pk>/update/',      views.task_update,        name='task_update'),

    # ── Audit Log ──────────────────────────────────────────────────────────
    path('audit-log/',                  views.audit_log,          name='audit_log'),
]
