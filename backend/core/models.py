from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Source(models.Model):
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Источник"
        verbose_name_plural = "Источники"


class Category(models.Model):
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Категорию"
        verbose_name_plural = "Категории"


class SourceCategory(models.Model):
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="categories")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Категория источника"
        verbose_name_plural = "Категории источников"
        unique_together = ("source", "code")

    def __str__(self):
        return f"{self.source}:{self.title} ({self.code}) -> {self.category}"


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    code = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Подкатегорию"
        verbose_name_plural = "Подкатегории"


class Project(models.Model):
    class StatusChoices(models.TextChoices):
        ACCEPTED = "accepted", _("Принят")
        DISTRIBUTED = "distributed", _("Разослан")

    class TypeChoices(models.TextChoices):
        PROJECT = "project", _("Проект")
        VACANCY = "vacancy", _("Вакансия")

    project_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.PROTECT, null=True, blank=True)
    price_max = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField(max_length=200)
    offers = models.IntegerField(default=0)
    order_created = models.BigIntegerField()
    type = models.CharField(
        max_length=50,
        choices=TypeChoices.choices,
        default=TypeChoices.PROJECT,
    )
    status = models.CharField(
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.ACCEPTED,
    )
    currency_symbol = models.CharField(max_length=255, default="")

    def __str__(self):
        return f"{self.title} ({self.source})"

    class Meta:
        unique_together = ("source", "project_id")
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"


class GPTModel(models.Model):
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=255)

    class Meta:
        verbose_name = "GPT-модель"
        verbose_name_plural = "GPT-модели"

    def __str__(self):
        return self.title


class GPTPrompt(models.Model):
    model = models.ForeignKey(GPTModel, on_delete=models.PROTECT, related_name="prompts")
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    text = models.TextField()
    json_format = models.JSONField()

    class Meta:
        unique_together = ("model", "category")
        verbose_name = "GPT-промпт"
        verbose_name_plural = "GPT-промпты"

    def __str__(self):
        return f"{self.model} -> {self.category}"


class Subscription(models.Model):
    title = models.CharField("Название", max_length=255)
    price = models.IntegerField("Цена")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Тарифный план"
        verbose_name_plural = "Тарифные планы"


class SubscriptionGPTLimits(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT, related_name="gpt")
    model = models.ForeignKey(GPTModel, on_delete=models.PROTECT)
    limit = models.IntegerField()

    def __str__(self):
        return f"{self.subscription}:{self.model} -> {self.limit}"

    class Meta:
        verbose_name = "GPT-ограничение"
        verbose_name_plural = "GPT-ограничения"


class UserSubscription(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)


class TelegramUser(models.Model):
    chat_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    skills = models.CharField(max_length=512, blank=True, null=True)
    summary = models.CharField(max_length=1024, blank=True, null=True)
    experience = models.CharField(max_length=1024, blank=True, null=True)
    hourly_rate = models.IntegerField(blank=True, null=True)

    user_subscription = models.ForeignKey(UserSubscription, on_delete=models.PROTECT, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_limits(self):
        base = "gpt-3.5-turbo"
        pro = "gpt-4o"
        limit_base = 1
        limit_pro = 0

        if self.user_subscription:
            limit_base += self.user_subscription.subscription.gpt.get(model__code=base).limit,
            limit_pro += self.user_subscription.subscription.gpt.get(model__code=pro).limit,

        return {
            base: limit_base,
            pro: limit_pro,
        }

    def __str__(self):
        return f"{self.name or 'Не представился'} (ID: {self.chat_id})"

    class Meta:
        verbose_name = "Телеграм-пользователь"
        verbose_name_plural = "Телеграм-пользователи"


class CategorySubscription(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="subscriptions")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="user_subscriptions",
        blank=True,
        null=True,
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.CASCADE,
        related_name="user_subscriptions",
        blank=True,
        null=True,
    )

    class Meta:
        unique_together = ("user", "category", "subcategory")

    def clean(self):
        if not self.category and not self.subcategory:
            raise ValidationError("Either category or subcategory must be set.")
        if self.category and self.subcategory:
            raise ValidationError("Both category and subcategory cannot be set at the same time.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} -> {self.subcategory.title if self.subcategory else self.category.title}"
