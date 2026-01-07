from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Category, Tag, Author, News, MediaFile, NewsRead

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "is_active",
        "news_count",
        "max_pinned_news",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "slug", "description", "is_active")}),
        ("Pin Settings", {"fields": ("max_pinned_news",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def news_count(self, obj):
        return obj.news.count()

    news_count.short_description = "Total News"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "category", "is_active", "news_count", "created_at"]
    list_filter = ["is_active", "category", "created_at"]
    search_fields = ["name", "slug", "category__name"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["category"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "slug", "category", "is_active")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def news_count(self, obj):
        return obj.news.count()

    news_count.short_description = "Tagged News"


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "designation",
        "email",
        "phone",
        "is_active",
        "news_count",
        "profile_image_preview",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "email", "designation"]
    readonly_fields = ["created_at", "updated_at", "profile_image_preview"]

    fieldsets = (
        (
            "Personal Information",
            {"fields": ("name", "email", "phone", "designation", "bio")},
        ),
        (
            "Profile",
            {"fields": ("profile_picture", "profile_image_preview", "is_active")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def news_count(self, obj):
        return obj.news.count()

    news_count.short_description = "Total News"

    def profile_image_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover; border-radius: 50%;" />',
                obj.profile_picture.url,
            )
        return "No Image"

    profile_image_preview.short_description = "Profile Preview"


class MediaFileInline(admin.TabularInline):
    model = MediaFile
    extra = 1
    fields = ["file", "file_type", "caption", "alt_text", "is_featured", "order"]
    readonly_fields = []


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "author",
        "status",
        "pinned_status",
        "views_count",
        "published_at",
        "created_at",
    ]
    list_filter = [
        "status",
        "is_pinned_global",
        "is_pinned_category",
        "category",
        "created_at",
        "published_at",
    ]
    search_fields = ["title", "subtitle", "excerpt", "slug"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at", "views_count", "canonical_url"]
    filter_horizontal = ["tags"]
    autocomplete_fields = ["category", "author"]
    inlines = [MediaFileInline]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "subtitle", "slug", "excerpt", "content")},
        ),
        ("Classification", {"fields": ("category", "tags", "author")}),
        ("Publishing", {"fields": ("status", "published_at")}),
        (
            "Pinning",
            {
                "fields": (
                    "is_pinned_global",
                    "pin_order_global",
                    "is_pinned_category",
                    "pin_order_category",
                ),
                "description": "Pin this news globally (top 5) or within its category",
            },
        ),
        (
            "SEO",
            {
                "fields": (
                    "seo_title",
                    "seo_subtitle",
                    "seo_description",
                    "seo_excerpt",
                    "canonical_url",
                    "seo_index",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Statistics", {"fields": ("views_count",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def pinned_status(self, obj):
        pins = []
        if obj.is_pinned_global:
            pins.append(
                f'<span style="color: red; font-weight: bold;">Global ({obj.pin_order_global})</span>'
            )
        if obj.is_pinned_category:
            pins.append(
                f'<span style="color: blue; font-weight: bold;">Category ({obj.pin_order_category})</span>'
            )
        return format_html(" | ".join(pins)) if pins else "-"

    pinned_status.short_description = "Pinned"

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "tags":
            category_id = request.GET.get("category")

            if category_id:
                kwargs["queryset"] = Tag.objects.filter(
                    category_id=category_id, is_active=True
                )
            elif hasattr(request, "_obj_") and request._obj_ and request._obj_.category:
                kwargs["queryset"] = Tag.objects.filter(
                    category=request._obj_.category, is_active=True
                )
            else:
                # IMPORTANT FIX
                kwargs["queryset"] = Tag.objects.filter(is_active=True)

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """Store object in request for tag filtering"""
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)

    class Media:
        js = ("admin/js/news_admin.js",)


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = [
        "news",
        "file_type",
        "caption",
        "is_featured",
        "order",
        "file_preview",
        "created_at",
    ]
    list_filter = ["file_type", "is_featured", "created_at"]
    search_fields = ["news__title", "caption", "alt_text"]
    readonly_fields = ["created_at", "updated_at", "file_preview"]
    autocomplete_fields = ["news"]

    fieldsets = (
        (
            "Media Information",
            {"fields": ("news", "file", "file_type", "caption", "alt_text")},
        ),
        ("Display Settings", {"fields": ("is_featured", "order", "file_preview")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def file_preview(self, obj):
        if obj.file_type == "IMAGE" and obj.file:
            return format_html('<img src="{}" width="200" />', obj.file.url)
        elif obj.file_type == "VIDEO" and obj.file:
            return format_html(
                '<video width="200" controls><source src="{}"></video>', obj.file.url
            )
        return "No Preview"

    file_preview.short_description = "Preview"


@admin.register(NewsRead)
class NewsReadAdmin(admin.ModelAdmin):
    list_display = [
        "news",
        "user_identifier_short",
        "read_count",
        "last_read_at",
        "ip_address",
    ]
    list_filter = ["last_read_at"]
    search_fields = ["news__title", "user_identifier", "ip_address"]
    readonly_fields = ["created_at", "updated_at", "last_read_at"]
    autocomplete_fields = ["news"]

    def user_identifier_short(self, obj):
        return f"{obj.user_identifier[:30]}..."

    user_identifier_short.short_description = "User ID"

    def has_add_permission(self, request):
        return False
