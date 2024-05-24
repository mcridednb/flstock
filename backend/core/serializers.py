from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.models import TelegramUser, Category, CategorySubscription, Project, Subcategory


class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = [
            "chat_id",
            "username",
            "first_name",
            "last_name",
            "name",
            "skills",
            "summary",
            "experience",
            "hourly_rate",
            "user_subscription",
        ]
        read_only_fields = ("user_subscription",)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["code", "title"]


class SubcategorySerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        chat_id = self.context.get('chat_id')
        if chat_id:
            try:
                user = TelegramUser.objects.get(chat_id=chat_id)
                return CategorySubscription.objects.filter(user=user, subcategory=obj).exists()
            except TelegramUser.DoesNotExist:
                return False
        return False

    class Meta:
        model = Subcategory
        fields = ["title", "is_subscribed"]


class CategorySubscriptionSerializer(serializers.ModelSerializer):
    chat_id = serializers.CharField(write_only=True)
    subcategory_title = serializers.CharField(read_only=True, source="subcategory.title")

    class Meta:
        model = CategorySubscription
        fields = ["id", "chat_id", "category", "subcategory", "subcategory_title"]
        extra_kwargs = {"category": {"required": False, "allow_null": True}}

    def create(self, validated_data):
        chat_id = validated_data.pop("chat_id", None)
        user = self.validate_chat_id(chat_id)
        validated_data["user"] = user

        try:
            subscription, created = CategorySubscription.objects.update_or_create(
                user=user,
                subcategory=validated_data.get("subcategory"),
                defaults={**validated_data}
            )
        except Exception as exc:
            raise ValidationError(exc)
        if not created:
            subscription.delete()
        return subscription

    def validate_chat_id(self, value):
        if isinstance(value, TelegramUser):
            return value
        try:
            return TelegramUser.objects.get(chat_id=str(value))
        except TelegramUser.DoesNotExist:
            raise serializers.ValidationError("User does not exist with the provided chat_id")


class ProjectSerializer(serializers.ModelSerializer):
    source = serializers.CharField(read_only=True, source="source.title")

    class Meta:
        model = Project
        fields = "__all__"
