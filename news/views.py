from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.core.cache import cache

from .models import Category, Tag, Author, News, MediaFile, NewsRead
from .serializers import (
    CategorySerializer, TagSerializer, AuthorSerializer,
    NewsListSerializer, NewsDetailSerializer, NewsCreateUpdateSerializer
)
from utils.responses import (
    success_response, error_response, created_response,
    validation_error_response, not_found_response
)
from .utils import get_user_identifier, get_client_ip, get_read_news_ids


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination class"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryListView(APIView):
    """
    GET: List all active categories
    POST: Create a new category (admin only)
    """

    def get(self, request):
        try:
            categories = Category.objects.filter(is_active=True).order_by('name')
            serializer = CategorySerializer(categories, many=True)
            return success_response(
                data=serializer.data,
                message="Categories retrieved successfully"
            )
        except Exception as e:
            return error_response(message="Failed to retrieve categories", errors=str(e))

    def post(self, request):
        try:
            serializer = CategorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return created_response(
                    data=serializer.data,
                    message="Category created successfully"
                )
            return validation_error_response(errors=serializer.errors)
        except Exception as e:
            return error_response(message="Failed to create category", errors=str(e))


class CategoryDetailView(APIView):
    """
    GET: Retrieve a single category
    PUT: Update a category
    DELETE: Delete a category
    """

    def get(self, request, slug):
        try:
            category = Category.objects.get(slug=slug, is_active=True)
            serializer = CategorySerializer(category)
            return success_response(
                data=serializer.data,
                message="Category retrieved successfully"
            )
        except Category.DoesNotExist:
            return not_found_response(message="Category not found")
        except Exception as e:
            return error_response(message="Failed to retrieve category", errors=str(e))


class TagsByCategoryView(APIView):
    """
    GET: Get all tags for a specific category
    """

    def get(self, request, category_id):
        try:
            tags = Tag.objects.filter(
                category_id=category_id,
                is_active=True
            ).select_related('category').order_by('name')

            serializer = TagSerializer(tags, many=True)
            return success_response(
                data=serializer.data,
                message="Tags retrieved successfully"
            )
        except Exception as e:
            return error_response(message="Failed to retrieve tags", errors=str(e))


class AuthorListView(APIView):
    """
    GET: List all active authors
    """

    def get(self, request):
        try:
            authors = Author.objects.filter(is_active=True).order_by('name')
            serializer = AuthorSerializer(authors, many=True, context={'request': request})
            return success_response(
                data=serializer.data,
                message="Authors retrieved successfully"
            )
        except Exception as e:
            return error_response(message="Failed to retrieve authors", errors=str(e))


class NewsListView(APIView):
    """
    GET: List news with filters
    Query params:
    - category: filter by category slug
    - tag: filter by tag slug
    - read: filter by read status (true/false)
    - search: search in title
    - page: page number
    - page_size: items per page
    """

    def get(self, request):
        try:
            """Base queryset - only published news"""
            queryset = News.objects.filter(
                status='PUBLISHED'
            ).select_related(
                'category', 'author'
            ).prefetch_related(
                'tags',
                Prefetch(
                    'media_files',
                    queryset=MediaFile.objects.filter(is_featured=True, file_type='IMAGE')
                )
            )

            """Filter by category"""
            category_slug = request.GET.get('category')
            if category_slug:
                queryset = queryset.filter(category__slug=category_slug)

            """Filter by tag"""
            tag_slug = request.GET.get('tag')
            if tag_slug:
                queryset = queryset.filter(tags__slug=tag_slug)

            """Search by title"""
            search = request.GET.get('search')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) | Q(excerpt__icontains=search)
                )

            """Get read news IDs from client"""
            read_news_ids = get_read_news_ids(request)

            """Filter by read status"""
            read_filter = request.GET.get('read')
            if read_filter:
                if read_filter.lower() == 'true':
                    queryset = queryset.filter(id__in=read_news_ids)
                elif read_filter.lower() == 'false':
                    queryset = queryset.exclude(id__in=read_news_ids)

            """Apply ordering based on pinning and category"""
            if category_slug:
                """Category view: show category-pinned first"""
                queryset = queryset.order_by(
                    '-is_pinned_category',
                    'pin_order_category',
                    '-published_at',
                    '-created_at'
                )
            else:
                """Global view: show globally-pinned first"""
                queryset = queryset.order_by(
                    '-is_pinned_global',
                    'pin_order_global',
                    '-published_at',
                    '-created_at'
                )

            """Pagination"""
            paginator = StandardResultsSetPagination()
            paginated_queryset = paginator.paginate_queryset(queryset, request)

            serializer = NewsListSerializer(
                paginated_queryset,
                many=True,
                context={'request': request, 'read_news_ids': read_news_ids}
            )

            return success_response(
                data={
                    'results': serializer.data,
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link()
                },
                message="News retrieved successfully"
            )
        except Exception as e:
            return error_response(message="Failed to retrieve news", errors=str(e))


class NewsDetailView(APIView):
    """
    GET: Retrieve a single news article by slug
    """

    def get(self, request, slug):
        try:
            news = News.objects.select_related(
                'category', 'author'
            ).prefetch_related(
                'tags', 'media_files'
            ).get(slug=slug, status='PUBLISHED')

            """Track read"""
            user_identifier = get_user_identifier(request)
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            """Update or create NewsRead record"""
            news_read, created = NewsRead.objects.get_or_create(
                news=news,
                user_identifier=user_identifier,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent
                }
            )

            if not created:
                news_read.read_count += 1
                news_read.ip_address = ip_address
                news_read.user_agent = user_agent
                news_read.save(update_fields=['read_count', 'ip_address', 'user_agent', 'last_read_at'])

            """Increment views count"""
            news.increment_views()

            """Get read news IDs"""
            read_news_ids = get_read_news_ids(request)

            serializer = NewsDetailSerializer(
                news,
                context={'request': request, 'read_news_ids': read_news_ids}
            )

            return success_response(
                data=serializer.data,
                message="News retrieved successfully"
            )
        except News.DoesNotExist:
            return not_found_response(message="News not found")
        except Exception as e:
            return error_response(message="Failed to retrieve news", errors=str(e))


class NewsCreateView(APIView):
    """
    POST: Create a new news article
    """

    def post(self, request):
        try:
            serializer = NewsCreateUpdateSerializer(data=request.data)
            if serializer.is_valid():
                news = serializer.save()

                """Return detailed response"""
                detail_serializer = NewsDetailSerializer(
                    news,
                    context={'request': request}
                )

                return created_response(
                    data=detail_serializer.data,
                    message="News created successfully"
                )
            return validation_error_response(errors=serializer.errors)
        except Exception as e:
            return error_response(message="Failed to create news", errors=str(e))


class NewsUpdateView(APIView):
    """
    PUT: Update a news article
    PATCH: Partial update a news article
    """

    def put(self, request, slug):
        return self._update(request, slug, partial=False)

    def patch(self, request, slug):
        return self._update(request, slug, partial=True)

    def _update(self, request, slug, partial):
        try:
            news = News.objects.get(slug=slug)
            serializer = NewsCreateUpdateSerializer(
                news,
                data=request.data,
                partial=partial
            )

            if serializer.is_valid():
                news = serializer.save()

                detail_serializer = NewsDetailSerializer(
                    news,
                    context={'request': request}
                )

                return success_response(
                    data=detail_serializer.data,
                    message="News updated successfully"
                )
            return validation_error_response(errors=serializer.errors)
        except News.DoesNotExist:
            return not_found_response(message="News not found")
        except Exception as e:
            return error_response(message="Failed to update news", errors=str(e))


class NewsPinView(APIView):
    """
    POST: Pin/Unpin a news article
    Body: {
        "pin_type": "global" or "category",
        "is_pinned": true/false,
        "pin_order": 1 (optional)
    }
    """

    def post(self, request, slug):
        try:
            news = News.objects.get(slug=slug)
            pin_type = request.data.get('pin_type')
            is_pinned = request.data.get('is_pinned', False)
            pin_order = request.data.get('pin_order', 0)

            if pin_type == 'global':
                news.is_pinned_global = is_pinned
                news.pin_order_global = pin_order if is_pinned else 0
                news.save(update_fields=['is_pinned_global', 'pin_order_global'])
            elif pin_type == 'category':
                news.is_pinned_category = is_pinned
                news.pin_order_category = pin_order if is_pinned else 0
                news.save(update_fields=['is_pinned_category', 'pin_order_category'])
            else:
                return error_response(message="Invalid pin_type. Use 'global' or 'category'")

            return success_response(
                data={'slug': news.slug, 'pin_type': pin_type, 'is_pinned': is_pinned},
                message=f"News {'pinned' if is_pinned else 'unpinned'} successfully"
            )
        except News.DoesNotExist:
            return not_found_response(message="News not found")
        except Exception as e:
            return error_response(message="Failed to pin/unpin news", errors=str(e))


class PinnedNewsView(APIView):
    """
    GET: Get pinned news
    Query params:
    - type: "global" or "category"
    - category: category slug (required if type=category)
    """

    def get(self, request):
        try:
            pin_type = request.GET.get('type', 'global')

            if pin_type == 'global':
                """Get globally pinned news (max 5)"""
                queryset = News.objects.filter(
                    status='PUBLISHED',
                    is_pinned_global=True
                ).select_related(
                    'category', 'author'
                ).prefetch_related(
                    'tags',
                    Prefetch(
                        'media_files',
                        queryset=MediaFile.objects.filter(is_featured=True, file_type='IMAGE')
                    )
                ).order_by('pin_order_global')[:5]

            elif pin_type == 'category':
                category_slug = request.GET.get('category')
                if not category_slug:
                    return error_response(message="Category slug is required for category pins")

                """Get category object to check max_pinned_news"""
                try:
                    category = Category.objects.get(slug=category_slug)
                    max_pinned = category.max_pinned_news
                except Category.DoesNotExist:
                    return not_found_response(message="Category not found")

                """Get category pinned news"""
                queryset = News.objects.filter(
                    status='PUBLISHED',
                    category__slug=category_slug,
                    is_pinned_category=True
                ).select_related(
                    'category', 'author'
                ).prefetch_related(
                    'tags',
                    Prefetch(
                        'media_files',
                        queryset=MediaFile.objects.filter(is_featured=True, file_type='IMAGE')
                    )
                ).order_by('pin_order_category')[:max_pinned]
            else:
                return error_response(message="Invalid type. Use 'global' or 'category'")

            """Get read news IDs"""
            read_news_ids = get_read_news_ids(request)

            serializer = NewsListSerializer(
                queryset,
                many=True,
                context={'request': request, 'read_news_ids': read_news_ids}
            )

            return success_response(
                data=serializer.data,
                message="Pinned news retrieved successfully"
            )
        except Exception as e:
            return error_response(message="Failed to retrieve pinned news", errors=str(e))