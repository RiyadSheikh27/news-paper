from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Tag, Author, News, MediaFile, NewsRead


class TagInline(admin.TabularInline):
    model = Tag
    extra = 1
    fields = ("name", "slug", "is_active")


class MediaFileInline(admin.TabularInline):
    model = MediaFile
    extra = 1
    fields = ("file", "file_type", "caption", "is_featured", "order")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "tag_count", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TagInline]

    def tag_count(self, obj):
        return obj.tags.count()

    tag_count.short_description = "Tags"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug", "is_active", "created_at")
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("name", "category__name")
    prepopulated_fields = {"slug": ("name",)}

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            kwargs["queryset"] = Category.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone",
        "designation",
        "is_active",
        "news_count",
        "created_at",
    )
    list_filter = ("is_active", "designation", "created_at")
    search_fields = ("name", "email", "designation")

    fieldsets = (
        ("Basic Information", {"fields": ("name", "email", "phone", "designation")}),
        ("Details", {"fields": ("bio", "profile_picture", "is_active")}),
    )

    def news_count(self, obj):
        return obj.news.count()

    news_count.short_description = "News Count"


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "subtitle",
        "category",
        "author",
        "status",
        "priority",
        "published_at",
        "created_at",
    )
    list_filter = ("status", "category", "created_at", "published_at")
    search_fields = ("title", "subtitle", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [MediaFileInline]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "subtitle", "slug", "excerpt", "content")},
        ),
        ("Classification", {"fields": ("category", "tags", "author")}),
        ("Publishing", {"fields": ("status", "published_at", "priority")}),
        (
            "SEO",
            {
                "fields": ("seo_title", "seo_excerpt", "seo_content", "seo_index"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "tags":
            """This will be handled dynamically in the frontend"""
            kwargs["queryset"] = Tag.objects.filter(is_active=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            kwargs["queryset"] = Category.objects.filter(is_active=True)
        if db_field.name == "author":
            kwargs["queryset"] = Author.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = (
        "news",
        "file_type",
        "caption",
        "is_featured",
        "order",
        "created_at",
    )
    list_filter = ("file_type", "is_featured", "created_at")
    search_fields = ("news__title", "caption")


@admin.register(NewsRead)
class NewsReadAdmin(admin.ModelAdmin):
    list_display = (
        "news",
        "short_identifier",
        "ip_address",
        "read_count",
        "last_read_at",
        "created_at",
    )
    list_filter = ("created_at", "last_read_at")
    search_fields = ("news__title", "user_identifier", "ip_address")
    readonly_fields = (
        "user_identifier",
        "ip_address",
        "user_agent",
        "read_count",
        "created_at",
        "last_read_at",
    )

    def short_identifier(self, obj):
        return f"{obj.user_identifier[:30]}..."

    short_identifier.short_description = "User Identifier"

    def has_add_permission(self, request):
        return False
