from django.urls import path
from core.views import (
    TelegramUserDetail,
    TelegramUserList,
    CategoryListView,
    CategorySubscriptionView,
    ProjectListView,
    ProjectDetailView,
    ProjectAnalyzeView,
)


urlpatterns = [
    path("telegram-users/", TelegramUserList.as_view(), name="telegram-user-list"),
    path("telegram-users/<str:chat_id>", TelegramUserDetail.as_view(), name="telegram-user-detail"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("category-subscribe", CategorySubscriptionView.as_view(), name="category-subscribe"),
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/<int:id>", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<int:id>/analyze", ProjectAnalyzeView.as_view(), name="project-analyze"),
]
