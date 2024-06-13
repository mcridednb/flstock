import io
import json
import uuid
from datetime import datetime, timedelta

import html2text
import pdfkit
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from openai import OpenAI
from yookassa import Configuration, Payment as YooKassaPayment


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
    class TypeChoices(models.TextChoices):
        RESPONSE = "response", _("Отклик")
        ANALYZE = "analyze", _("Анализ")

    model = models.ForeignKey(GPTModel, on_delete=models.PROTECT, related_name="prompts")
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    text = models.TextField()
    response_format = models.JSONField()
    type = models.CharField(max_length=50, choices=TypeChoices.choices, default=TypeChoices.ANALYZE)
    tokens = models.PositiveIntegerField(default=2)

    class Meta:
        unique_together = ("model", "category", "type")
        verbose_name = "GPT-промпт"
        verbose_name_plural = "GPT-промпты"

    def __str__(self):
        return f"{self.category} -> {dict(self.TypeChoices.choices)[self.type]}"


class Subscription(models.Model):
    title = models.CharField("Название", max_length=255)
    tokens = models.IntegerField("Цена")
    days_count = models.IntegerField(default=30)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Тарифный план"
        verbose_name_plural = "Тарифные планы"


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

    created_at = models.DateTimeField(auto_now_add=True)

    stop_words = models.CharField(max_length=2048, null=True, blank=True)
    keywords = models.CharField(max_length=2048, null=True, blank=True)
    min_price = models.IntegerField(null=True, blank=True)

    referrer = models.ForeignKey("TelegramUser", models.PROTECT, related_name="referrals", null=True, blank=True)
    registration_completed = models.BooleanField(default=False)

    tokens = models.PositiveIntegerField(default=10)
    subscription_until = models.DateField(null=True, blank=True)

    phone = models.CharField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    @property
    def subscription(self):
        return self.subscription_until.strftime('%d.%m.%Y')

    def delete_message(self, delete_message_id):
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/deleteMessage"
        data = {
            'chat_id': self.chat_id,
            'message_id': delete_message_id
        }
        response = requests.post(url, data=data)
        return response.json()

    def send_message(self, text, keyboard=None):
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'Markdown',
        }
        if keyboard:
            keyboard = {
                "inline_keyboard": [
                    [{"text": button_text, "callback_data": callback_data}]
                    for button_text, callback_data in keyboard
                ]
            }
            data["reply_markup"] = json.dumps(keyboard)

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

        response = requests.post(url, data=data)
        return response.json()

    def send_bonus(self, reason: str, value: int):
        self.tokens += value
        self.save()
        return self.send_message(
            f"*{reason}:*\n"
            f"🥳 *+{value} токенов!*\n"
            f"🪙 *Текущий баланс: {self.tokens}*",
            keyboard=[("❌ Закрыть", "close")]
        )

    @property
    def is_pro(self):
        return bool(self.subscription_until and self.subscription_until >= datetime.today().date())

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
    class TypeChoices(models.TextChoices):
        RESPONSE = "response", _("Отклик")
        ANALYZE = "analyze", _("Анализ")
        SALE_PLAN = "sale_plan", _("План продажи")

    class StatusChoices(models.TextChoices):
        ACCEPTED = "accepted", _("Принят")
        COMPLETED = "completed", _("Выполнен")
        DELIVERED = "delivered", _("Отправлен пользователю")

    status = models.CharField(
        max_length=100,
        choices=StatusChoices.choices,
        default=StatusChoices.ACCEPTED,
    )
    type = models.CharField(
        max_length=100,
        choices=TypeChoices.choices,
        default=TypeChoices.ANALYZE,
    )

    prompt = models.ForeignKey(GPTPrompt, on_delete=models.PROTECT, related_name="gpt_requests")
    user = models.ForeignKey(TelegramUser, on_delete=models.PROTECT, related_name="gpt_requests")
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="gpt_requests")
    name = models.CharField(max_length=255, blank=True, null=True)
    skills = models.CharField(max_length=512, blank=True, null=True)
    summary = models.CharField(max_length=1024, blank=True, null=True)
    experience = models.CharField(max_length=1024, blank=True, null=True)
    hourly_rate = models.IntegerField(blank=True, null=True)
    additional_info = models.CharField(max_length=2048, null=True, blank=True)

    input_tokens = models.IntegerField(null=True, blank=True)  # $5
    output_tokens = models.IntegerField(null=True, blank=True)  # $15

    gpt_request = models.TextField(null=True, blank=True)
    gpt_response = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def _generate_gpt_request(self):
        text = (
            "Вот информация о фрилансере и заказе:\n"
            "Фрилансер:\n"
            "- Имя: ```{name}```\n"
            "- О себе: ```{summary}```\n"
            "- Навыки: ```{skills}```\n"
            "- Опыт: ```{experience}```\n"
            "Заказ:\n"
            "- Заголовок: ```{title}```\n"
            "- Описание: ```{description}```\n"
            "- Цена: ```{price}```\n"
            "- Максимальная цена: ```{price_max}```\n"
            "Твоя задача:\n"
            "{prompt}\n"
            "Примечание от фрилансера (приоритет):\n"
            "```{additional_info}```\n\n"
            "Сформируй ответ исключительно! в структуре JSON, как в примере ниже:\n"
            "{response_format}"
        ).format(
            name=self.user.name or "Не указано",
            skills=self.user.skills or "Не указано",
            summary=self.user.summary or "Не указано",
            experience=self.user.experience or "Не указано",
            title=self.project.title,
            description=self.project.description,
            price=self.project.price or "Не указана",
            price_max=self.project.price_max or "Не указана",
            prompt=self.prompt.text,
            additional_info=self.additional_info,
            response_format=self.prompt.response_format,
        )

        self.name = self.user.name
        self.skills = self.user.skills
        self.summary = self.user.summary
        self.experience = self.user.experience
        self.hourly_rate = self.user.hourly_rate
        self.gpt_request = text
        self.save()

        return text

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
        response = json.loads(response_content)
        self.gpt_response = response
        self.input_tokens = completion.usage.prompt_tokens
        self.output_tokens = completion.usage.completion_tokens
        self.save()
        return response

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

    def _send_response(self, message_id, delete_message_id):
        response = self._openai_request()

        keyboard = {
            "inline_keyboard": [
                # [{"text": "✅ Продолжить диалог", "callback_data": f"gpt:{self.id}:answer:::::"}],
                [{"text": "⚠️ Сообщить об ошибке", "callback_data": f"gpt:{self.id}:complain::{self.project.id}:::"}],
            ]
        }
        keyboard_json = json.dumps(keyboard)

        data = {
            'chat_id': self.user.chat_id,
            'text': f"*Ваш отклик:*\n\n{response['response']}",
            'parse_mode': 'Markdown',
            'reply_to_message_id': message_id,
            'reply_markup': keyboard_json,
        }

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, data=data)
        self._delete_message(delete_message_id)
        transaction = Transaction.objects.create(
            type=Transaction.TypeChoices.GPT_REQUEST,
            user=self.user,
            project=self.project,
            gpt_request=self,
            tokens=self.prompt.tokens,
        )
        transaction.update_user()
        return response.json()

    def _send_analyze(self, message_id, delete_message_id):
        response, pdf_buffer = self._generate_pdf()
        files = {
            'document': (f'report.pdf', pdf_buffer, 'application/pdf')
        }
        keyboard = {
            "inline_keyboard": [
                # [{"text": "✅ Продолжить диалог", "callback_data": f"gpt:{self.id}:answer:::::"}],
                [{"text": "⚠️ Сообщить об ошибке", "callback_data": f"gpt:{self.id}:complain::{self.project.id}:::"}],
            ]
        }
        keyboard_json = json.dumps(keyboard)
        data = {
            'chat_id': self.user.chat_id,
            'text': f"*Отчёт по заказу: {self.project.title}*",
            'parse_mode': 'Markdown',
            'reply_to_message_id': message_id,
            'reply_markup': keyboard_json,
        }
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
        response = requests.post(url, data=data, files=files)
        self._delete_message(delete_message_id)
        transaction = Transaction.objects.create(
            type=Transaction.TypeChoices.GPT_REQUEST,
            user=self.user,
            project=self.project,
            gpt_request=self,
            tokens=self.prompt.tokens,
        )
        transaction.update_user()
        return response.json()

    def _send_sales_plan(self, message_id, delete_message_id):
        ...

    def send_user_response(self, message_id, delete_message_id):
        send_function = {
            self.TypeChoices.RESPONSE: self._send_response,
            self.TypeChoices.ANALYZE: self._send_analyze,
            self.TypeChoices.SALE_PLAN: self._send_sales_plan,
        }[self.type]
        return send_function(message_id, delete_message_id)


class Payment(models.Model):
    class StatusChoices(models.TextChoices):
        ACCEPTED = "accepted", _("Принят")
        GENERATED = "generated", _("Сформирован")
        COMPLETED = "completed", _("Выполнен")

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.ACCEPTED,
    )

    user = models.ForeignKey(TelegramUser, on_delete=models.PROTECT, related_name="payments")
    tokens = models.IntegerField(default=0)
    value = models.DecimalField(decimal_places=2, max_digits=10)
    payment_uuid = models.CharField(max_length=255, null=True)
    idempotent_uuid = models.CharField(max_length=255, null=True)
    delete_message_id = models.CharField(max_length=255, null=True)
    payment = models.JSONField(null=True)
    response = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def update_user(self):
        self.user.tokens += self.tokens
        self.user.save()
        self.user.delete_message(self.delete_message_id)
        return self.user.send_message(
            f"🥳 *Вам начислено {self.tokens} токенов!*\n"
            f"🪙 *Текущий баланс: {self.user.tokens} токенов*",
            keyboard=[("❌ Закрыть", "close")]
        )

    def generate_bill(self):
        Configuration.account_id = settings.YOOKASSA_ACCOUNT_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

        self.idempotent_uuid = uuid.uuid4()
        payment = YooKassaPayment.create({
            "amount": {
                "value": self.value,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": settings.BOT_URL,
            },
            "capture": True,
            "description": f"Заказ №{self.id}",
            "receipt": {
                "customer": {
                    "email": self.user.email,
                },
                "items": [
                    {
                        "description": "Информационно-консультационные услуги",
                        "quantity": 1,
                        "amount": {
                            "value": self.value,
                            "currency": "RUB"
                        },
                        "vat_code": "1"
                    },
                ]
            }
        }, self.idempotent_uuid)

        self.payment_uuid = payment.id
        self.status = self.StatusChoices.GENERATED
        self.payment = payment.json()
        self.save()
        return payment

    @property
    def url(self):
        return json.loads(self.payment)["confirmation"]["confirmation_url"]


class Transaction(models.Model):
    class TypeChoices(models.TextChoices):
        SUBSCRIPTION = "subscription", _("Подписка")
        GPT_REQUEST = "gpt_request", _("AI-запрос")

    type = models.CharField(
        max_length=100,
        choices=TypeChoices.choices,
        default=TypeChoices.GPT_REQUEST,
    )

    user = models.ForeignKey(TelegramUser, on_delete=models.PROTECT, related_name="transactions")
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="transactions", null=True, blank=True)
    subscription = models.ForeignKey(
        Subscription, on_delete=models.PROTECT, related_name="transactions", null=True, blank=True
    )
    gpt_request = models.OneToOneField(GPTRequest, on_delete=models.PROTECT, null=True, blank=True)
    tokens = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def update_user(self):
        if self.type == self.TypeChoices.SUBSCRIPTION:
            subscription_until = datetime.today().date()
            if self.user.is_pro:
                subscription_until = self.user.subscription_until
            self.user.subscription_until = subscription_until + timedelta(days=self.subscription.days_count)
            self.user.tokens -= self.subscription.tokens

        if self.type == self.TypeChoices.GPT_REQUEST:
            self.user.tokens -= self.tokens

        self.user.save()


class Complain(models.Model):
    ...
