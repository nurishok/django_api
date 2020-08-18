from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Post, Category
from .permissions import IsPostAuthor
from .serializers import PostSerializer, CategorySerializer


class CategoriesViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'


class MyCustomPagination(PageNumberPagination):
    page_size = 5


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsPostAuthor]
    pagination_class = MyCustomPagination

    def get_serializer_context(self):
        return {'request': self.request}

    def get_permissions(self):
        if self.action in ['create', 'own']:
            permissions = [IsAuthenticated, ]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permissions = [IsAuthenticated, IsPostAuthor]
        else:
            permissions = []
        return [permission() for permission in permissions]

    def get_queryset(self):
        weeks_count = self.request.query_params.get('weeks', 0)
        queryset = super().get_queryset()
        if self.action == 'own':
            queryset = queryset.filter(author=self.request.user)
        if weeks_count > 0:
            start_date = timezone.now() - timedelta(weeks=weeks_count)
            queryset = queryset.filter(created_at__gte=start_date)
        return queryset

    @action(detail=False, methods=['get'])
    def own(self, request, pk=None):
        queryset = self.get_queryset()
        queryset = queryset.filter(author=request.user)
        serializer = PostSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, method=['get'])
    def search(self, request, pk=None):
        q = request.query_params.get('q')
        queryset = self.get_queryset()
        queryset = queryset.filter(Q(title__icontains=q)|
                                   Q(text__icontains=q)|
                                   Q(category__title__icontains=q))
        serializer = PostSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

# TODO: Search F(), Q()
# TODO: Filtering
