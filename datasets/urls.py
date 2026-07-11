from django.urls import path
from . import views

app_name = 'datasets'

urlpatterns = [
    path('', views.dataset_list, name='list'),
    path('upload/', views.upload_dataset, name='upload'),
    path('samples/', views.sample_gallery, name='samples'),
    path('<int:dataset_id>/', views.dataset_overview, name='overview'),
    path('<int:dataset_id>/preview/', views.dataset_preview, name='preview'),
    path('<int:dataset_id>/delete/', views.delete_dataset, name='delete'),
]
