"""news/serializers.py"""

from rest_framework import serializers
from .models import Category, Tag, Author, News, MediaFile


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer"""

    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "slug",
            "category",
            "category_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]


class AuthorSerializer(serializers.ModelSerializer):
    """Author serializer"""

    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "bio",
            "profile_picture",
            "profile_picture_url",
            "designation",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None


class MediaFileSerializer(serializers.ModelSerializer):
    """Media file serializer"""

    # file_url = serializers.SerializerMethodField()
    class Meta:
        model = MediaFile
        fields = [
            "id",
            "file",
            "file_type",
            "caption",
            "alt_text",
            "is_featured",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    # def get_file_url(self, obj):
    #     if obj.file:
    #         request = self.context.get('request')
    #         if request:
    #             return request.build_absolute_uri(obj.file.url)
    #         return obj.file.url
    #     return None


class NewsListSerializer(serializers.ModelSerializer):
    """Serializer for news list view"""

    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    author_name = serializers.CharField(source="author.name", read_only=True)
    tags_list = serializers.SerializerMethodField()
    feature_image = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    seo = serializers.SerializerMethodField()
    og_graph = serializers.SerializerMethodField()
    twitter = serializers.SerializerMethodField()
    schema = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            "id",
            "title",
            "subtitle",
            "slug",
            "excerpt",
            "category_name",
            "category_slug",
            "author_name",
            "tags_list",
            "feature_image",
            "status",
            "seo",
            "og_graph",
            "twitter",
            "schema",
            "is_pinned_global",
            "is_pinned_category",
            "published_at",
            "views_count",
            "is_read",
            "created_at",
        ]

    def get_tags_list(self, obj):
        return [
            {"id": tag.id, "name": tag.name, "slug": tag.slug} for tag in obj.tags.all()
        ]

    def get_seo(self, obj):
        """Return SEO data in the format specified"""
        return {
            "seo_title": obj.seo_title,
            "seo_subtitle": obj.seo_subtitle,
            "seo_description": obj.seo_description,
            "seo_excerpt": obj.seo_excerpt,
            "canonical_url": obj.canonical_url,
            "seo_index": obj.seo_index,
            "seo_keywords": obj.seo_keywords,
        }
    def get_og_graph(self, obj):
        """Return Open Graph data in the format specified"""
        return {
            "og_title": obj.og_title,
            "og_subtitle": obj.og_subtitle,
            "og_excerpt": obj.og_excerpt,
            "og_description": obj.og_description,
            "og_image": obj.og_image.url if obj.og_image else None,
            "og_url": obj.og_url,
            "og_type": obj.og_type,
        }
    def get_twitter(self, obj):
        """Return Twitter Card data in the format specified"""
        return {
            "twitter_title": obj.twitter_title,
            "twitter_subtitle": obj.twitter_subtitle,
            "twitter_excerpt": obj.twitter_excerpt,
            "twitter_description": obj.twitter_description,
            "twitter_image": obj.twitter_image.url if obj.twitter_image else None,
        }

    def get_schema(self, obj):
        """Return Schema.org data in the format specified"""
        return obj.get_schema_org_data()

    def get_feature_image(self, obj):
        featured = obj.media_files.filter(is_featured=True, file_type="IMAGE").first()
        if featured and featured.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(featured.file.url)
            return featured.file.url
        return None

    def get_is_read(self, obj):
        """Check if news is read from context (passed from view)"""
        read_news_ids = self.context.get("read_news_ids", [])
        return obj.id in read_news_ids


class NewsDetailSerializer(serializers.ModelSerializer):
    """Serializer for news detail view with full SEO data"""

    category_id = serializers.IntegerField(source="category.id", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)

    tags = serializers.SerializerMethodField()

    author_id = serializers.IntegerField(source="author.id", read_only=True)
    author_name = serializers.CharField(source="author.name", read_only=True)
    author_designation = serializers.CharField(
        source="author.designation", read_only=True
    )

    feature_image = serializers.SerializerMethodField()
    media_files_list = MediaFileSerializer(
        source="media_files", many=True, read_only=True
    )

    seo = serializers.SerializerMethodField()
    og_graph = serializers.SerializerMethodField()
    twitter = serializers.SerializerMethodField()
    schema = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            "id",
            "title",
            "subtitle",
            "slug",
            "excerpt",
            "content",
            "category_id",
            "category_name",
            "category_slug",
            "tags",
            "author_id",
            "author_name",
            "author_designation",
            "feature_image",
            "media_files_list",
            "status",
            "published_at",
            "views_count",
            "is_pinned_global",
            "is_pinned_category",
            "seo",
            "og_graph",
            "twitter",
            "schema",
            "is_read",
            "created_at",
            "updated_at",
        ]

    def get_tags(self, obj):
        return [
            {"id": tag.id, "name": tag.name, "slug": tag.slug} for tag in obj.tags.all()
        ]

    def get_feature_image(self, obj):
        featured_images = obj.media_files.filter(is_featured=True, file_type="IMAGE")

        if featured_images.exists():
            return MediaFileSerializer(
                featured_images, many=True, context=self.context
            ).data

        return None

    def get_seo(self, obj):
        """Return SEO data in the format specified"""
        return {
            "seo_title": obj.seo_title,
            "seo_subtitle": obj.seo_subtitle,
            "seo_description": obj.seo_description,
            "seo_excerpt": obj.seo_excerpt,
            "canonical_url": obj.canonical_url,
            "seo_index": obj.seo_index,
            "seo_keywords": obj.seo_keywords,
        }

    def get_og_graph(self, obj):
        """Return Open Graph data in the format specified"""
        return {
            "og_title": obj.og_title,
            "og_subtitle": obj.og_subtitle,
            "og_excerpt": obj.og_excerpt,
            "og_description": obj.og_description,
            "og_image": obj.og_image.url if obj.og_image else None,
            "og_url": obj.og_url,
            "og_type": obj.og_type,
        }
    def get_twitter(self, obj):
        """Return Twitter Card data in the format specified"""
        return {
            "twitter_title": obj.twitter_title,
            "twitter_subtitle": obj.twitter_subtitle,
            "twitter_excerpt": obj.twitter_excerpt,
            "twitter_description": obj.twitter_description,
            "twitter_image": obj.twitter_image.url if obj.twitter_image else None,
        }
    def get_schema(self, obj):
        """Return Schema.org data in the format specified"""
        return obj.get_schema_org_data()

    def get_is_read(self, obj):
        """Check if news is read from context"""
        read_news_ids = self.context.get("read_news_ids", [])
        return obj.id in read_news_ids


class NewsCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating news"""

    media_files = MediaFileSerializer(many=True, required=False)

    class Meta:
        model = News
        fields = [
            "title",
            "subtitle",
            "slug",
            "excerpt",
            "content",
            "category",
            "tags",
            "author",
            "status",
            "is_pinned_global",
            "pin_order_global",
            "is_pinned_category",
            "pin_order_category",
            "published_at",
            "seo_title",
            "seo_subtitle",
            "seo_description",
            "seo_excerpt",
            "canonical_url",
            "seo_index",
            "media_files",
        ]
        read_only_fields = ["slug"]

    def validate_tags(self, value):
        """Validate that all tags belong to the selected category"""
        category = self.initial_data.get("category")
        if category:
            for tag in value:
                if tag.category_id != int(category):
                    raise serializers.ValidationError(
                        f"Tag '{tag.name}' does not belong to the selected category"
                    )
        return value

    def create(self, validated_data):
        media_files_data = validated_data.pop("media_files", [])
        tags = validated_data.pop("tags", [])

        news = News.objects.create(**validated_data)
        news.tags.set(tags)

        for media_data in media_files_data:
            MediaFile.objects.create(news=news, **media_data)

        return news

    def update(self, instance, validated_data):
        media_files_data = validated_data.pop("media_files", None)
        tags = validated_data.pop("tags", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if media_files_data is not None:
            """Clear existing media files and create new ones"""
            instance.media_files.all().delete()
            for media_data in media_files_data:
                MediaFile.objects.create(news=instance, **media_data)

        return instance
