from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from utils.models import TimeStampedModel
from ckeditor.fields import RichTextField

class Category(TimeStampedModel):
    """News Category Model"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    """Pin settings for category"""
    max_pinned_news = models.IntegerField(
        default=3,
        help_text="Maximum number of pinned news in this category"
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(TimeStampedModel):
    """Tag Model - belongs to a category"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='tags'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']
        unique_together = ['name', 'category']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Author(TimeStampedModel):
    """Global Author/Journalist Model"""
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='authors/',
        blank=True,
        null=True
    )
    designation = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class News(TimeStampedModel):
    """Main News Model"""

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]

    title = models.CharField(max_length=500, db_index=True)
    subtitle = models.CharField(max_length=500, blank=True)
    slug = models.SlugField(max_length=500, unique=True, blank=True)
    excerpt = models.TextField()
    content = RichTextField()

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='news'
    )
    tags = models.ManyToManyField(Tag, related_name='news', blank=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.PROTECT,
        related_name='news'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    """Pinning system"""
    is_pinned_global = models.BooleanField(
        default=False,
        help_text="Pin this news globally (top 5)"
    )
    is_pinned_category = models.BooleanField(
        default=False,
        help_text="Pin this news in its category"
    )
    pin_order_global = models.IntegerField(
        default=0,
        help_text="Order for globally pinned news (lower = higher priority)"
    )
    pin_order_category = models.IntegerField(
        default=0,
        help_text="Order for category pinned news (lower = higher priority)"
    )

    published_at = models.DateTimeField(blank=True, null=True)
    views_count = models.IntegerField(default=0)

    """SEO Fields"""
    seo_title = models.CharField(max_length=200, blank=True)
    seo_subtitle = models.CharField(max_length=500, blank=True)
    seo_description = models.TextField(blank=True)
    seo_excerpt = models.TextField(blank=True)
    canonical_url = models.URLField(blank=True)
    seo_index = models.BooleanField(default=True)

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        ordering = ['-is_pinned_global', 'pin_order_global', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['-is_pinned_global', 'pin_order_global']),
            models.Index(fields=['category', '-is_pinned_category', 'pin_order_category']),
        ]

    def save(self, *args, **kwargs):
        """Auto-generate slug"""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while News.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        """Auto-populate SEO fields if empty"""
        if not self.seo_title:
            self.seo_title = f"{self.title} | NewsPortal"
        if not self.seo_subtitle:
            self.seo_subtitle = self.subtitle
        if not self.seo_description:
            self.seo_description = self.excerpt
        if not self.seo_excerpt:
            self.seo_excerpt = self.excerpt
        if not self.canonical_url:
            self.canonical_url = f"https://newsportal.com/news/{self.category.slug}/{self.slug}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])


class MediaFile(TimeStampedModel):
    """Media files (images/videos) for news"""

    FILE_TYPE_CHOICES = [
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
    ]

    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name='media_files'
    )
    file = models.FileField(
        upload_to='news_media/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm', 'avi']
            )
        ]
    )
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES
    )
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True, help_text="For SEO")
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Media File"
        verbose_name_plural = "Media Files"
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['news', 'is_featured']),
        ]

    def __str__(self):
        return f"{self.file_type} for {self.news.title}"


class NewsRead(TimeStampedModel):
    """Track which news has been read by which user (browser-based)"""
    news = models.ForeignKey(
        News,
        on_delete=models.CASCADE,
        related_name='reads'
    )
    user_identifier = models.CharField(
        max_length=255,
        help_text="Unique browser identifier (fingerprint or session)",
        db_index=True
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    read_count = models.IntegerField(default=1)
    last_read_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "News Read"
        verbose_name_plural = "News Reads"
        unique_together = ['news', 'user_identifier']
        ordering = ['-last_read_at']
        indexes = [
            models.Index(fields=['user_identifier']),
            models.Index(fields=['news', 'user_identifier']),
        ]

    def __str__(self):
        return f"{self.user_identifier[:20]}... read {self.news.title[:30]}..."