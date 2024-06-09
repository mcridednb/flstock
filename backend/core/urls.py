from django.urls import path
from core.views import (
    TelegramUserDetail,
    TelegramUserList,
    CategoryListView,
    SubcategoryListView,
    CategorySubscriptionView,
    ProjectListView,
    ProjectDetailView,
    ProjectGPTView,
    SourceSubscriptionView,
    SourceListView,
    RegistrationSuccessView,
    PaymentsView,
    ProcessPaymentView,
    AddSubscriptionView,
)


urlpatterns = [
    path("telegram-users/", TelegramUserList.as_view(), name="telegram-user-list"),
    path("telegram-users/<str:chat_id>", TelegramUserDetail.as_view(), name="telegram-user-detail"),
    path("telegram-users/<str:chat_id>/registration-success", RegistrationSuccessView.as_view(), name="registration-success"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("sources/", SourceListView.as_view(), name="source-list"),
    path("subcategories/", SubcategoryListView.as_view(), name="subcategory-list"),
    path("category-subscribe", CategorySubscriptionView.as_view(), name="category-subscribe"),
    path("source-subscribe", SourceSubscriptionView.as_view(), name="source-subscribe"),
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/<int:id>", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<int:id>/gpt", ProjectGPTView.as_view(), name="project-gpt"),

    path("payment", PaymentsView.as_view(), name="payment"),
    path("process-payment", ProcessPaymentView.as_view(), name="process-payment"),

    path("add-subscription", AddSubscriptionView.as_view(), name="add-subscription"),
]
