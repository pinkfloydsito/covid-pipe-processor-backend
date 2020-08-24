from django.urls import path
from entities.views import PipeCreate, PipeDelete, PipeUpdate

urlpatterns = [
    path('pipe/add/', PipeCreate.as_view(), name='pipe-add'),
    path('pipe/<int:pk>/', PipeUpdate.as_view(), name='pipe-update'),
    path('pipe/<int:pk>/delete/', PipeDelete.as_view(), name='pipe-delete'),
]
