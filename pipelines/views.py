import json
import os
import time
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.conf import settings
from django.core.files.base import ContentFile
from .models import Pipeline, PipelineStep, ProcessingHistory
from .forms import PipelineForm
from datasets.models import Dataset
from datasets.utils import read_uploaded_file
from processing.pipeline_executor import execute_pipeline
from processing.conversion import convert_dataframe
from processing.storage_utils import (
    read_storage_to_df, save_df_to_filefield, storage_exists,
    download_to_temp, delete_storage_path
)


def _load_secondary_datasets(pipeline):
    datasets = {}
    for step in pipeline.steps.filter(operation='merge_datasets'):
        merge_path = step.config.get('merge_file_path', '')
        if merge_path:
            df = read_storage_to_df(merge_path)
            if df is not None:
                datasets[step.config.get('dataset_key', 'secondary')] = df
    return datasets


@login_required
def pipeline_list(request):
    pipelines = Pipeline.objects.filter(user=request.user)
    return render(request, 'pipelines/list.html', {'pipelines': pipelines})


@login_required
def create_pipeline(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)

    if request.method == 'POST':
        form = PipelineForm(request.POST)
        if form.is_valid():
            pipeline = form.save(commit=False)
            pipeline.user = request.user
            pipeline.save()
            messages.success(request, 'Pipeline created. Add steps to configure it.')
            return redirect('pipelines:edit', pipeline_id=pipeline.id)
    else:
        initial_data = {
            'name': f'Process {dataset.original_name}',
            'output_format': dataset.file_format,
        }
        form = PipelineForm(initial=initial_data)

    return render(request, 'pipelines/create.html', {'form': form, 'dataset': dataset})


@login_required
def edit_pipeline(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id, user=request.user)
    steps = pipeline.steps.all()

    draft_key = f'pipeline_draft_{pipeline_id}'
    is_steps_submit = request.method == 'POST' and 'operation' in request.POST

    if request.method == 'POST' and is_steps_submit:
        step_order = 0
        operations = request.POST.getlist('operation')
        configs = request.POST.getlist('config')
        step_ids_to_keep = []

        for idx, (op, cfg) in enumerate(zip(operations, configs)):
            if op:
                step_order += 1
                step_data = {'operation': op}
                try:
                    config_data = json.loads(cfg) if cfg.strip() else {}
                except json.JSONDecodeError:
                    config_data = {}

                if op == 'merge_datasets':
                    merge_file = request.FILES.get(f'merge_file_{idx}')
                    if merge_file:
                        safe_name = f'{step_order}_{merge_file.name}'
                        merge_storage_path = f'merge_uploads/{pipeline.id}/{safe_name}'
                        from django.core.files.storage import default_storage
                        default_storage.save(merge_storage_path, ContentFile(merge_file.read()))
                        config_data['merge_file_path'] = merge_storage_path
                        config_data['merge_file_name'] = merge_file.name
                    config_data['how'] = request.POST.get(f'merge_how_{idx}', config_data.get('how', 'inner'))
                    config_data['left_on'] = request.POST.get(f'merge_left_on_{idx}', config_data.get('left_on', ''))
                    config_data['right_on'] = request.POST.get(f'merge_right_on_{idx}', config_data.get('right_on', ''))
                    config_data['dataset_key'] = 'secondary'

                existing = PipelineStep.objects.filter(pipeline=pipeline, step_order=step_order).first()
                if existing and not config_data and existing.config:
                    config_data = existing.config
                step_data['config'] = config_data

                if existing:
                    PipelineStep.objects.filter(pk=existing.pk).update(**step_data)
                    step_ids_to_keep.append(existing.pk)
                else:
                    step = PipelineStep.objects.create(pipeline=pipeline, step_order=step_order, **step_data)
                    step_ids_to_keep.append(step.pk)

        pipeline.steps.exclude(pk__in=step_ids_to_keep).delete()
        messages.success(request, 'Steps saved.')

        if draft_key in request.session:
            del request.session[draft_key]

        return redirect('pipelines:edit', pipeline_id=pipeline.id)

    if request.method == 'POST' and not is_steps_submit:
        form = PipelineForm(request.POST, instance=pipeline)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pipeline settings updated.')
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, f'{field}: {err}')
        return redirect('pipelines:edit', pipeline_id=pipeline.id)

    form = PipelineForm(instance=pipeline)
    operation_choices = PipelineStep.OPERATION_CHOICES

    has_draft = draft_key in request.session
    if has_draft:
        messages.info(request, 'Unsaved draft restored. Save to keep changes.')

    return render(request, 'pipelines/edit.html', {
        'form': form,
        'pipeline': pipeline,
        'steps': steps,
        'operation_choices': operation_choices,
        'has_draft': has_draft,
    })


@login_required
def delete_pipeline(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id, user=request.user)
    try:
        from django.core.files.storage import default_storage
        merge_prefix = f'merge_uploads/{pipeline.id}/'
        if hasattr(default_storage, 'listdir'):
            try:
                dirs, files = default_storage.listdir(merge_prefix)
                for f in files:
                    default_storage.delete(merge_prefix + f)
            except Exception:
                pass
    except Exception:
        pass
    pipeline.delete()
    messages.success(request, 'Pipeline deleted.')
    return redirect('pipelines:list')


@login_required
def execute_pipeline_view(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id, user=request.user)
    dataset_id = request.GET.get('dataset_id')

    if not dataset_id:
        messages.error(request, 'Please select a dataset to process.')
        return redirect('pipelines:edit', pipeline_id=pipeline.id)

    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)

    if request.method == 'POST':
        df = read_uploaded_file(dataset.file)
        steps_data = list(pipeline.steps.values('operation', 'config'))
        secondary_datasets = _load_secondary_datasets(pipeline)

        result = execute_pipeline(df, steps_data, secondary_datasets)

        processed_df = result['dataframe']
        base_name = os.path.splitext(dataset.original_name)[0]
        timestamp = int(time.time())
        output_name = f'processed/{pipeline.id}_{timestamp}_processed_{base_name}.csv'

        history = ProcessingHistory.objects.create(
            pipeline=pipeline,
            dataset=dataset,
            runtime=result['runtime'],
            output_format=pipeline.output_format,
            summary=result['summary'],
        )

        save_df_to_filefield(history.output_file, processed_df, output_name)
        history.save(update_fields=['output_file'])

        return redirect('pipelines:results', pipeline_id=pipeline.id, history_id=history.id)

    return render(request, 'pipelines/execute.html', {
        'pipeline': pipeline,
        'dataset': dataset,
    })


@login_required
def download_processed(request, history_id):
    history = get_object_or_404(ProcessingHistory, id=history_id)
    if history.pipeline and history.pipeline.user != request.user:
        return HttpResponse(status=403)

    output_format = request.GET.get('format', history.output_format or 'csv')

    dataset = history.dataset
    if not dataset:
        return HttpResponseBadRequest('Dataset not found for this history.')

    ext_map = {'csv': '.csv', 'xlsx': '.xlsx', 'json': '.json'}
    content_type_map = {
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'json': 'application/json',
    }

    filename_base = os.path.splitext(dataset.original_name)[0]
    download_filename = f'processed_{filename_base}{ext_map.get(output_format, ".csv")}'

    if history.output_file and storage_exists(history.output_file.name):
        df = read_storage_to_df(history.output_file.name)
        if df is not None:
            content, _, _ = convert_dataframe(df, output_format)
            response = HttpResponse(content, content_type=content_type_map.get(output_format, 'application/octet-stream'))
            response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
            return response

    df = read_uploaded_file(dataset.file)
    steps_data = list(history.pipeline.steps.values('operation', 'config'))
    secondary_datasets = _load_secondary_datasets(history.pipeline)
    result = execute_pipeline(df, steps_data, secondary_datasets)
    processed_df = result['dataframe']
    content, _, _ = convert_dataframe(processed_df, output_format)
    response = HttpResponse(content, content_type=content_type_map.get(output_format, 'application/octet-stream'))
    response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
    return response


@login_required
def pipeline_results(request, pipeline_id, history_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id, user=request.user)
    history = get_object_or_404(ProcessingHistory, id=history_id, pipeline=pipeline)
    dataset = history.dataset

    if dataset:
        try:
            original_df = read_uploaded_file(dataset.file)
        except (FileNotFoundError, Exception) as e:
            messages.error(request, f'Dataset file is missing. Please re-upload the dataset.')
            return redirect('pipelines:history')
        original_stats = {
            'rows': len(original_df),
            'columns': len(original_df.columns),
            'missing': int(original_df.isnull().sum().sum()),
            'duplicates': int(original_df.duplicated().sum()),
        }
        total_rows = original_stats['rows']
    else:
        original_stats = None
        total_rows = 0

    processed_df = None
    if history.output_file and storage_exists(history.output_file.name):
        processed_df = read_storage_to_df(history.output_file.name)

    if processed_df is None:
        df = read_uploaded_file(dataset.file) if dataset else None
        steps_data = list(pipeline.steps.values('operation', 'config'))
        secondary_datasets = _load_secondary_datasets(pipeline)
        result = execute_pipeline(df, steps_data, secondary_datasets)
        processed_df = result['dataframe']

    processed_stats = {
        'rows': len(processed_df),
        'columns': len(processed_df.columns),
        'missing': int(processed_df.isnull().sum().sum()),
        'duplicates': int(processed_df.duplicated().sum()),
    }
    processed_columns = list(processed_df.columns)
    has_outlier_column = any(c in ('_outlier_iqr', '_outlier_zscore') for c in processed_columns)

    result = {
        'summary': history.summary,
        'runtime': history.runtime,
        'success': True,
    }

    return render(request, 'pipelines/results.html', {
        'pipeline': pipeline,
        'dataset': dataset,
        'history': history,
        'result': result,
        'original_stats': original_stats,
        'processed_stats': processed_stats,
        'processed_columns': processed_columns,
        'has_outlier_column': has_outlier_column,
        'total_rows': total_rows,
    })


@login_required
def results_data_json(request, pipeline_id, history_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id, user=request.user)
    history = get_object_or_404(ProcessingHistory, id=history_id, pipeline=pipeline)
    dataset = history.dataset

    if not dataset:
        return JsonResponse({'error': 'Dataset not found'}, status=400)

    processed_df = None
    if history.output_file and storage_exists(history.output_file.name):
        processed_df = read_storage_to_df(history.output_file.name)

    if processed_df is None:
        df = read_uploaded_file(dataset.file)
        steps_data = list(pipeline.steps.values('operation', 'config'))
        secondary_datasets = _load_secondary_datasets(pipeline)
        result = execute_pipeline(df, steps_data, secondary_datasets)
        processed_df = result['dataframe']

    original_df = read_uploaded_file(dataset.file)

    page = int(request.GET.get('page', 1))
    per_page = 200
    start = (page - 1) * per_page
    end = start + per_page

    page_df = processed_df.iloc[start:end]
    original_page_df = original_df.iloc[start:min(end, len(original_df))]

    processed_columns = list(processed_df.columns)
    original_common_cols = [c for c in processed_columns if c in original_df.columns]
    original_col_indices = [list(processed_columns).index(c) for c in original_common_cols]

    has_outlier_column = any(c in ('_outlier_iqr', '_outlier_zscore') for c in processed_columns)
    outlier_col_idx = None
    if has_outlier_column:
        outlier_col = '_outlier_iqr' if '_outlier_iqr' in processed_columns else '_outlier_zscore'
        outlier_col_idx = processed_columns.index(outlier_col)

    rows = []
    for i in range(len(page_df)):
        row_data = []
        is_row_outlier = False
        for ci in range(len(processed_columns)):
            val = page_df.iloc[i, ci]
            cls = ''
            if ci in original_col_indices and i < len(original_page_df):
                orig_idx = original_col_indices.index(ci)
                orig_val = original_page_df.iloc[i, orig_idx]
                if pd.isna(orig_val) and not pd.isna(val):
                    cls = 'heatmap-cell-filled'
                elif not pd.isna(orig_val) and pd.isna(val):
                    cls = 'heatmap-cell-removed'
            if outlier_col_idx is not None and ci == outlier_col_idx:
                v = val
                is_outlier = bool(v) and (v is True or str(v).lower() == 'true' or v == 1 or v == '1')
                if is_outlier:
                    cls = 'heatmap-cell-changed'
                    is_row_outlier = True
            cell_val = None if (isinstance(val, float) and pd.isna(val)) else val
            row_data.append({'v': str(cell_val) if cell_val is not None else None, 'c': cls})
        rows.append({'cells': row_data, 'is_outlier': is_row_outlier})

    return JsonResponse({
        'rows': rows,
        'columns': processed_columns,
        'has_next': end < len(processed_df),
        'total': len(processed_df),
        'page': page,
        'per_page': per_page,
    })


@login_required
def processing_history(request):
    history = ProcessingHistory.objects.filter(pipeline__user=request.user)
    return render(request, 'pipelines/history.html', {'history': history})


@login_required
def export_pipeline(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id, user=request.user)
    steps = pipeline.steps.all().values('step_order', 'operation', 'config')
    data = {
        'name': pipeline.name,
        'description': pipeline.description,
        'output_format': pipeline.output_format,
        'steps': list(steps),
    }
    response = HttpResponse(
        json.dumps(data, indent=2),
        content_type='application/json',
    )
    filename = pipeline.name.replace(' ', '_').lower()
    response['Content-Disposition'] = f'attachment; filename="{filename}_pipeline.json"'
    return response


@login_required
def export_page(request):
    pipelines = Pipeline.objects.filter(user=request.user)
    return render(request, 'pipelines/export.html', {'pipelines': pipelines})


@login_required
def import_pipeline(request):
    if request.method == 'POST' and request.FILES.get('pipeline_file'):
        try:
            data = json.loads(request.FILES['pipeline_file'].read())
            pipeline = Pipeline.objects.create(
                user=request.user,
                name=data.get('name', 'Imported Pipeline'),
                description=data.get('description', ''),
                output_format=data.get('output_format', 'csv'),
            )
            for step_data in data.get('steps', []):
                PipelineStep.objects.create(
                    pipeline=pipeline,
                    step_order=step_data.get('step_order', 1),
                    operation=step_data.get('operation', 'remove_duplicates'),
                    config=step_data.get('config', {}),
                )
            messages.success(request, f'Pipeline "{pipeline.name}" imported successfully!')
            return redirect('pipelines:edit', pipeline_id=pipeline.id)
        except Exception as e:
            messages.error(request, f'Failed to import pipeline: {str(e)}')
    return redirect('pipelines:list')
