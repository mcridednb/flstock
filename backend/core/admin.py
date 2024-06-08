from django.contrib import admin
from django.db.models.fields.json import JSONField
from jsoneditor.forms import JSONEditor

from core.models import (
    Subscription, TelegramUser, Project, Category, Subcategory, CategorySubscription,
    Source, GPTPrompt, GPTModel, SourceSubscription, GPTRequest
)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    pass


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(CategorySubscription)
class CategorySubscriptionAdmin(admin.ModelAdmin):
    pass


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    pass


@admin.register(GPTModel)
class GPTModelAdmin(admin.ModelAdmin):
    pass


@admin.register(GPTPrompt)
class GPTPromptAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {
            "widget": JSONEditor(
                init_options={"mode": "code", "modes": ["code", "tree"]},
                ace_options={"readOnly": False},
            )
        }
    }
    # formfield_overrides = {
    #     JSONField: {'widget': JSONEditor},
    # }


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    pass


@admin.register(SourceSubscription)
class SourceSubscriptionAdmin(admin.ModelAdmin):
    pass


@admin.register(GPTRequest)
class GPTRequestAdmin(admin.ModelAdmin):
    pass
