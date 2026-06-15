from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("inventory/", views.inventory_index, name="inventory_index"),
    path("inventory/new/", views.inventory_new, name="inventory_new"),
    path("inventory/<int:product_id>/edit/", views.inventory_edit, name="inventory_edit"),
    path("inventory/<int:product_id>/delete/", views.inventory_delete, name="inventory_delete"),
    path("inventory/api/search/", views.product_search, name="product_search"),
    path("pos/", views.pos_index, name="pos_index"),
    path("pos/complete/", views.pos_complete, name="pos_complete"),
    path("pos/ticket/<int:sale_id>/", views.pos_ticket, name="pos_ticket"),
    path("sales/", views.sales_index, name="sales_index"),
    path("sales/<int:sale_id>/", views.sales_detail, name="sales_detail"),
    path("sales/<int:sale_id>/return/", views.sale_return, name="sale_return"),
    path("users/", views.users_index, name="users_index"),
    path("users/new/", views.users_new, name="users_new"),
    path("users/<int:user_id>/edit/", views.users_edit, name="users_edit"),
    path("users/<int:user_id>/delete/", views.users_delete, name="users_delete"),
    path("perfil/", views.cambiar_password, name="perfil"),
    path("activity/", views.activity_log, name="activity_log"),
]
