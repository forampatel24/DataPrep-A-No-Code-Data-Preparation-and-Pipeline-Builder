from django.urls import path
from . import views

app_name = 'pipelines'

urlpatterns = [
    path('', views.pipeline_list, name='list'),
    path('create/<int:dataset_id>/', views.create_pipeline, name='create'),
    path('<int:pipeline_id>/', views.edit_pipeline, name='edit'),
    path('<int:pipeline_id>/delete/', views.delete_pipeline, name='delete'),
    path('<int:pipeline_id>/execute/', views.execute_pipeline_view, name='execute'),
    path('<int:pipeline_id>/results/<int:history_id>/', views.pipeline_results, name='results'),
    path('<int:pipeline_id>/results/<int:history_id>/data/', views.results_data_json, name='results_data'),
    path('<int:pipeline_id>/export/', views.export_pipeline, name='export_pipeline'),
    path('history/', views.processing_history, name='history'),
    path('download/<int:history_id>/', views.download_processed, name='download'),
    path('export/', views.export_page, name='export_page'),
    path('import/', views.import_pipeline, name='import_pipeline'),
]
