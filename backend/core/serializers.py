from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.models import (
    TelegramUser,
    Category,
    CategorySubscription,
    Project,
    Subcategory,
    SourceSubscription,
    Source,
    Payment, Transaction, Subscription,
)
from core.tasks import send_limit_exceeded_message


class TelegramUserSerializer(serializers.ModelSerializer):
    referrer = serializers.CharField(write_only=True, required=False, allow_null=True)
    subscription = serializers.CharField(read_only=True)

    def create(self, validated_data):
        referrer = validated_data.pop("referrer", None)
        if referrer:
            try:
                validated_data["referrer"] = TelegramUser.objects.get(chat_id=referrer)
            except TelegramUser.DoesNotExist:
                pass

        return super().create(validated_data)

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

            "phone",
            "email",

            "stop_words",
            "keywords",
            "min_price",

            "referrer",
            "registration_completed",

            "tokens",
            "subscription",
        ]
        read_only_fields = ("tokens", "subscription_until", "registration_completed")


class CategorySerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        chat_id = self.context.get('chat_id')
        if chat_id:
            try:
                user = TelegramUser.objects.get(chat_id=chat_id)
                return CategorySubscription.objects.filter(user=user, subcategory__category=obj).exists()
            except TelegramUser.DoesNotExist:
                return False
        return False

    class Meta:
        model = Category
        fields = ["title", "code", "is_subscribed"]


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
        fields = ["title", "code", "is_subscribed"]


class SourceSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        chat_id = self.context.get('chat_id')
        if chat_id:
            try:
                user = TelegramUser.objects.get(chat_id=chat_id)
                return SourceSubscription.objects.filter(user=user, source=obj).exists()
            except TelegramUser.DoesNotExist:
                return False
        return False

    class Meta:
        model = Source
        fields = ["title", "code", "is_subscribed"]


class CategorySubscriptionSerializer(serializers.ModelSerializer):
    chat_id = serializers.CharField(write_only=True)
    subcategory_title = serializers.CharField(read_only=True, source="subcategory.title")
    subcategory_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CategorySubscription
        fields = ["id", "chat_id", "category", "subcategory", "subcategory_title", "subcategory_code"]
        extra_kwargs = {
            "category": {"required": False, "allow_null": True},
            "subcategory": {"required": False, "allow_null": True}
        }

    def create(self, validated_data):
        chat_id = validated_data.pop("chat_id", None)
        user = self.validate_chat_id(chat_id)

        subcategory_code = validated_data.pop("subcategory_code", None)
        if subcategory_code:
            try:
                subcategory = Subcategory.objects.get(code=subcategory_code)
            except Subcategory.DoesNotExist:
                raise ValidationError(f"Подкатегория не найдена")
        else:
            raise ValidationError(f"Пустой код подкатегории.")

        if not user.is_pro:
            exist = CategorySubscription.objects.filter(user=user, subcategory=subcategory)
            if not exist and CategorySubscription.objects.filter(user=user).count() >= 3:
                raise ValidationError("🚫 Вы не можете указать больше 3-х категорий.")

        try:
            subscription, created = CategorySubscription.objects.update_or_create(
                user=user,
                subcategory=subcategory,
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


class SourceSubscriptionSerializer(serializers.ModelSerializer):
    chat_id = serializers.CharField(write_only=True)
    source_title = serializers.CharField(read_only=True, source="source.title")
    source_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = SourceSubscription
        fields = ["id", "chat_id", "source", "source_title", "source_code"]

    def create(self, validated_data):
        chat_id = validated_data.pop("chat_id", None)
        user = self.validate_chat_id(chat_id)

        source_code = validated_data.pop("source_code", None)
        if source_code:
            try:
                source = Source.objects.get(code=source_code)
            except Source.DoesNotExist:
                raise ValidationError(f"Источник не найден")
        else:
            raise ValidationError(f"Пустой код источника")

        if not user.is_pro:
            exist = SourceSubscription.objects.filter(user=user, source=source)
            if not exist and SourceSubscription.objects.filter(user=user).count() >= 2:
                raise ValidationError("🚫 Вы не можете указать больше 2-х источников.")

        try:
            subscription, created = SourceSubscription.objects.update_or_create(
                user=user,
                source=source,
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


class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(write_only=True)
    url = serializers.ReadOnlyField()

    def create(self, validated_data):
        chat_id = validated_data.pop("user")
        validated_data["user"] = self.validate_chat_id(chat_id)
        instance = super().create(validated_data)
        instance.generate_bill()
        return instance

    def validate_chat_id(self, value):
        if isinstance(value, TelegramUser):
            return value
        try:
            return TelegramUser.objects.get(chat_id=str(value))
        except TelegramUser.DoesNotExist:
            raise serializers.ValidationError("User does not exist with the provided chat_id")

    class Meta:
        model = Payment
        fields = [
            "user",
            "tokens",
            "value",
            "url",
            "delete_message_id",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.CharField(write_only=True)
    delete_message_id = serializers.CharField(write_only=True)
    value = serializers.IntegerField(write_only=True)

    def create(self, validated_data):
        chat_id = validated_data.pop("user")
        tokens = validated_data.get("tokens")
        value = validated_data.pop("value")
        delete_message_id = validated_data.pop("delete_message_id")
        user = self.validate_chat_id(chat_id)

        if user.tokens < tokens:
            send_limit_exceeded_message(user.chat_id, delete_message_id)
            raise serializers.ValidationError("Not enough tokens")

        validated_data["user"] = user
        value_title_map = {
            30: "👍 1 месяц",
            90: "💪 3 месяца",
            180: "🚀 6 месяцев",
        }
        subscription, _ = Subscription.objects.get_or_create(
            title=value_title_map[value],
            tokens=tokens,
            days_count=value,
        )
        validated_data["subscription"] = subscription
        instance = super().create(validated_data)
        instance.update_user()
        user.delete_message(delete_message_id)
        user.send_message(
            "🎉 *Поздравляем!*\n\n"
            f"*Подписка активирована до: {user.subscription_until.strftime('%d.%m.%Y')}*",
            keyboard=[("❌ Закрыть", "close")]
        )
        return instance

    def validate_chat_id(self, value):
        if isinstance(value, TelegramUser):
            return value
        try:
            return TelegramUser.objects.get(chat_id=str(value))
        except TelegramUser.DoesNotExist:
            raise serializers.ValidationError("User does not exist with the provided chat_id")

    class Meta:
        model = Transaction
        fields = [
            "user",
            "type",
            "subscription",
            "tokens",
            "value",
            "delete_message_id",
        ]
