"""news/urls.py"""

from django.urls import path
from .views import (
    CategoryListView,
    CategoryDetailView,
    TagsByCategoryView,
    AuthorListView,
    NewsListView,
    NewsDetailView,
    NewsCreateView,
    NewsUpdateView,
    NewsPinView,
    PinnedNewsView,
)

app_name = "news"

urlpatterns = [
    # Category URLs
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path(
        "categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"
    ),
    # Tag URLs
    path(
        "categories/<int:category_id>/tags/",
        TagsByCategoryView.as_view(),
        name="tags-by-category",
    ),
    # Author URLs
    path("authors/", AuthorListView.as_view(), name="author-list"),
    # News URLs
    path("news/", NewsListView.as_view(), name="news-list"),
    path("news/create/", NewsCreateView.as_view(), name="news-create"),
    path("news/pinned/", PinnedNewsView.as_view(), name="pinned-news"),
    path("news/<slug:slug>/", NewsDetailView.as_view(), name="news-detail"),
    path("news/update/<slug:slug>/", NewsUpdateView.as_view(), name="news-update"),
    path("news/pin/<slug:slug>/", NewsPinView.as_view(), name="news-pin"),
]
