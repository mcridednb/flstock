from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView

from core.models import Category, CategorySubscription, TelegramUser, Project, Subcategory, SourceSubscription, Source
from core.serializers import (
    TelegramUserSerializer,
    CategorySerializer,
    SubcategorySerializer,
    CategorySubscriptionSerializer,
    ProjectSerializer,
    SourceSubscriptionSerializer,
    SourceSerializer,
)
from core.tasks import gpt_request


class TelegramUserList(generics.CreateAPIView):
    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer


class TelegramUserDetail(generics.RetrieveUpdateAPIView):
    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer
    lookup_field = "chat_id"

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["chat_id"] = self.request.query_params.get("chat_id")
        return context


class SourceListView(generics.ListAPIView):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["chat_id"] = self.request.query_params.get("chat_id")
        return context


class SubcategoryListView(generics.ListAPIView):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer

    def get_queryset(self):
        category = self.request.query_params.get("category")
        return Subcategory.objects.filter(category__code=category)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["chat_id"] = self.request.query_params.get("chat_id")
        return context


class CategorySubscriptionView(generics.CreateAPIView):
    queryset = CategorySubscription.objects.all()
    serializer_class = CategorySubscriptionSerializer


class ProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        return Project.objects.filter(order_created__gte=day_ago.timestamp())


class ProjectDetailView(generics.RetrieveAPIView):
    serializer_class = ProjectSerializer
    lookup_field = "id"

    def get_queryset(self):
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        return Project.objects.filter(order_created__gte=day_ago.timestamp())


class ProjectAnalyzeView(APIView):
    def post(self, request, id, *args, **kwargs):
        project = get_object_or_404(Project, id=id)
        chat_id = request.data.get("chat_id")
        gpt_model_id = request.data.get("model")
        message_id = request.data.get("message_id")
        additional_info = request.data.get("additional_info")

        if not chat_id or not gpt_model_id:
            return JsonResponse({"detail": "chat_id and model are required."}, status=status.HTTP_400_BAD_REQUEST)

        gpt_request.delay(project.id, message_id, chat_id, gpt_model_id, additional_info)

        return JsonResponse({"detail": "Analysis task has been queued."}, status=status.HTTP_202_ACCEPTED)


class SourceSubscriptionView(generics.CreateAPIView):
    queryset = SourceSubscription.objects.all()
    serializer_class = SourceSubscriptionSerializer
