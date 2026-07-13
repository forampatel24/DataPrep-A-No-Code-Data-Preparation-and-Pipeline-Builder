import json
import os
import time
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, FileResponse
from django.core.paginator import Paginator
from django.conf import settings
from .models import Pipeline, PipelineStep, ProcessingHistory
from .forms import PipelineForm
from datasets.models import Dataset
from datasets.utils import read_uploaded_file
from processing.pipeline_executor import execute_pipeline
from processing.conversion import convert_dataframe


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

        for op, cfg in zip(operations, configs):
            if op:
                step_order += 1
                step_data = {'operation': op}
                try:
                    step_data['config'] = json.loads(cfg) if cfg.strip() else {}
                except json.JSONDecodeError:
                    step_data['config'] = {}

                step, created = PipelineStep.objects.get_or_create(
                    pipeline=pipeline,
                    step_order=step_order,
                    defaults=step_data,
                )
                if not created:
                    PipelineStep.objects.filter(pk=step.pk).update(**step_data)
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

        result = execute_pipeline(df, steps_data)

        processed_df = result['dataframe']
        filename = f'processed_{os.path.splitext(dataset.original_name)[0]}.csv'
        rel_path = f'processed/{pipeline.id}_{int(time.time())}_{filename}'
        abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        processed_df.to_csv(abs_path, index=False)

        history = ProcessingHistory.objects.create(
            pipeline=pipeline,
            dataset=dataset,
            runtime=result['runtime'],
            output_format=pipeline.output_format,
            summary=result['summary'],
            output_file=rel_path,
        )

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

    if history.output_file and os.path.exists(history.output_file.path):
        if output_format == 'csv':
            response = FileResponse(open(history.output_file.path, 'rb'), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
            return response
        processed_df = pd.read_csv(history.output_file.path)
    else:
        df = read_uploaded_file(dataset.file)
        steps_data = list(history.pipeline.steps.values('operation', 'config'))
        result = execute_pipeline(df, steps_data)
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

    processed_file = history.output_file
    if processed_file and os.path.exists(processed_file.path):
        processed_df = pd.read_csv(processed_file.path)
    else:
        df = read_uploaded_file(dataset.file)
        steps_data = list(pipeline.steps.values('operation', 'config'))
        result = execute_pipeline(df, steps_data)
        processed_df = result['dataframe']

    original_df = read_uploaded_file(dataset.file)
    original_stats = {
        'rows': len(original_df),
        'columns': len(original_df.columns),
        'missing': int(original_df.isnull().sum().sum()),
        'duplicates': int(original_df.duplicated().sum()),
    }
    processed_stats = {
        'rows': len(processed_df),
        'columns': len(processed_df.columns),
        'missing': int(processed_df.isnull().sum().sum()),
        'duplicates': int(processed_df.duplicated().sum()),
    }
    processed_columns = list(processed_df.columns)

    has_outlier_column = any(c in ('_outlier_iqr', '_outlier_zscore') for c in processed_columns)

    paginator = Paginator(range(len(processed_df)), 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    start = (page_obj.number - 1) * paginator.per_page
    end = start + len(page_obj.object_list)
    page_df = processed_df.iloc[start:end]
    processed_rows = page_df.values.tolist()
    original_page_df = original_df.iloc[start:min(end, len(original_df))]
    original_rows = original_page_df.values.tolist()

    outlier_indices = set()
    if has_outlier_column:
        outlier_col = '_outlier_iqr' if '_outlier_iqr' in processed_columns else '_outlier_zscore'
        col_idx = processed_columns.index(outlier_col)
        for local_idx, row in enumerate(processed_rows):
            val = row[col_idx]
            if val is True or val == 'True' or val == 1 or val == '1':
                outlier_indices.add(local_idx)

    result = {
        'summary': history.summary,
        'runtime': history.runtime,
        'success': True,
    }

    original_common_cols = [c for c in processed_columns if c in original_df.columns]
    original_col_indices = [list(processed_columns).index(c) for c in original_common_cols]

    original_common_cols = [c for c in processed_columns if c in original_df.columns]
    original_col_indices = [list(processed_columns).index(c) for c in original_common_cols]

    heatmap_rows = []
    for i, proc_row in enumerate(processed_rows):
        orig_row = original_rows[i] if i < len(original_rows) else [None] * len(original_common_cols)
        cells = []
        for ci, val in enumerate(proc_row):
            cls = ''
            if ci in original_col_indices:
                orig_idx = original_col_indices.index(ci)
                orig_val = orig_row[orig_idx] if orig_idx < len(orig_row) else None
                if orig_val is None and val is not None and not (isinstance(val, float) and pd.isna(val)):
                    cls = 'heatmap-cell-filled'
                elif orig_val is not None and (val is None or (isinstance(val, float) and pd.isna(val))):
                    cls = 'heatmap-cell-removed'
            cells.append({'value': val, 'class': cls})
        heatmap_rows.append(cells)

    return render(request, 'pipelines/results.html', {
        'pipeline': pipeline,
        'dataset': dataset,
        'history': history,
        'result': result,
        'original_stats': original_stats,
        'processed_stats': processed_stats,
        'processed_rows': processed_rows,
        'processed_columns': processed_columns,
        'heatmap_rows': heatmap_rows,
        'outlier_indices': outlier_indices,
        'has_outlier_column': has_outlier_column,
        'page_obj': page_obj,
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
