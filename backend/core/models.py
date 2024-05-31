import io
import json

import html2text
import pdfkit
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from openai import OpenAI


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


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    code = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Подкатегорию"
        verbose_name_plural = "Подкатегории"


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
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.PROTECT)
    price_max = models.DecimalField(max_digits=10, decimal_places=2, null=True)
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
    response_format = models.JSONField()

    class Meta:
        unique_together = ("model", "category")
        verbose_name = "GPT-промпт"
        verbose_name_plural = "GPT-промпты"

    def __str__(self):
        return f"{self.model} -> {self.category}"


class Subscription(models.Model):
    title = models.CharField("Название", max_length=255)
    price = models.IntegerField("Цена")
    days_count = models.IntegerField(default=30)
    gpt_request_limit = models.IntegerField(default=5)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Тарифный план"
        verbose_name_plural = "Тарифные планы"


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

    user_subscription = models.ForeignKey(UserSubscription, on_delete=models.PROTECT, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    stop_words = models.CharField(max_length=2048, null=True, blank=True)
    keywords = models.CharField(max_length=2048, null=True, blank=True)

    gpt_request_limit = models.PositiveIntegerField(default=2)

    def __str__(self):
        return f"{self.name or 'Не представился'} (ID: {self.chat_id})"

    class Meta:
        verbose_name = "Телеграм-пользователь"
        verbose_name_plural = "Телеграм-пользователи"


class CategorySubscription(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="category_subscriptions")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="category_subscriptions",
        blank=True,
        null=True,
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.CASCADE,
        related_name="category_subscriptions",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

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


class SourceSubscription(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="source_subscriptions")
    source = models.ForeignKey(
        Source,
        on_delete=models.CASCADE,
        related_name="source_subscriptions",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "source")

    def __str__(self):
        return f"{self.user} -> {self.source.title}"


class GPTRequest(models.Model):
    class StatusChoices(models.TextChoices):
        ACCEPTED = "accepted", _("Принят")
        COMPLETED = "completed", _("Выполнен")
        DELIVERED = "delivered", _("Отправлен пользователю")

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.ACCEPTED,
    )

    prompt = models.ForeignKey(GPTPrompt, on_delete=models.CASCADE, related_name="gpt_requests")
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="gpt_requests")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="gpt_requests")
    name = models.CharField(max_length=255, blank=True, null=True)
    skills = models.CharField(max_length=512, blank=True, null=True)
    summary = models.CharField(max_length=1024, blank=True, null=True)
    experience = models.CharField(max_length=1024, blank=True, null=True)
    hourly_rate = models.IntegerField(blank=True, null=True)
    additional_info = models.CharField(max_length=2048, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def _generate_gpt_request(self):
        self.name = self.user.name
        self.skills = self.user.skills
        self.summary = self.user.summary
        self.experience = self.user.experience
        self.hourly_rate = self.user.hourly_rate
        self.save()

        return self.prompt.text.format(
            name=self.user.name,
            skills=self.user.skills,
            summary=self.user.summary,
            experience=self.user.experience,
            additional_info=self.additional_info,
            title=self.project.title,
            description=self.project.description,
            price=self.project.price,
            price_max=self.project.price_max,
        ) + "\n" + str(self.prompt.response_format)

    def _openai_request(self):
        request_text = self._generate_gpt_request()

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        messages = [
            {"role": "user", "content": request_text}
        ]

        completion = client.chat.completions.create(
            model=self.prompt.model.code,
            response_format={"type": "json_object"},
            messages=messages,
        )
        response_content = completion.choices[0].message.content
        return json.loads(response_content)

    @property
    def _template_name(self):
        return f"{self.project.category.code}_report.html"

    def _generate_pdf(self):
        response = self._openai_request()

        total_hours = sum(stage["time"] for stage in response["stages"])
        potential_price = total_hours * self.hourly_rate if self.hourly_rate else None

        response["hourly_rate"] = self.hourly_rate
        response["project_title"] = html2text.html2text(self.project.title).strip()
        response["project_description"] = html2text.html2text(self.project.description).strip()
        response["total_hours"] = total_hours
        response["potential_price"] = potential_price
        response["additional_info"] = self.additional_info

        html_content = render_to_string(self._template_name, {'response': response})
        options = {
            'encoding': 'UTF-8'
        }
        pdf_buffer = pdfkit.from_string(html_content, False, options=options)
        buffer = io.BytesIO(pdf_buffer)
        buffer.seek(0)
        return response, buffer

    def _delete_message(self, delete_message_id):
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/deleteMessage"
        data = {
            'chat_id': self.user.chat_id,
            'message_id': delete_message_id
        }
        response = requests.post(url, data=data)
        return response.json()

    def send_user_response(self, message_id, delete_message_id):
        response, pdf_buffer = self._generate_pdf()
        files = {
            'document': (f'report.pdf', pdf_buffer, 'application/pdf')
        }
        keyboard = {
            "inline_keyboard": [
                [{"text": "⚠️ Пожаловаться", "callback_data": f"complain:{self.id}"}]
            ]
        }
        keyboard_json = json.dumps(keyboard)
        data = {
            'chat_id': self.user.chat_id,
            'text': response["response"],
            'parse_mode': 'Markdown',
            'reply_to_message_id': message_id,
            'reply_markup': keyboard_json,
        }
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
        response = requests.post(url, data=data, files=files)
        self._delete_message(delete_message_id)
        self.user.gpt_request_limit -= 1
        self.user.save()
        return response.json()
