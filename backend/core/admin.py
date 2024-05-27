from django.contrib import admin
from django.db.models.fields.json import JSONField
from jsoneditor.forms import JSONEditor

from core.models import (
    Subscription, TelegramUser, Project, Category, Subcategory, CategorySubscription,
    Source, SourceCategory, GPTPrompt, SubscriptionGPTLimits, GPTModel, UserSubscription
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


class SourceCategoryAdmin(admin.TabularInline):
    model = SourceCategory


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    inlines = [SourceCategoryAdmin, ]


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


class SubscriptionGPTLimitsAdmin(admin.TabularInline):
    model = SubscriptionGPTLimits


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    inlines = [SubscriptionGPTLimitsAdmin, ]


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    pass
