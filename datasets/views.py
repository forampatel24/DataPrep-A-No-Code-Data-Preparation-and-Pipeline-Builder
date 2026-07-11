import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
from .models import Dataset
from .forms import DatasetUploadForm
from .utils import read_uploaded_file, validate_uploaded_file
from processing.profiling import profile_dataset, generate_health_report, calculate_health_score


def _clean_json(data):
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


@login_required
def dataset_list(request):
    datasets = Dataset.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'datasets/list.html', {'datasets': datasets})


@login_required
def upload_dataset(request):
    if request.method == 'POST':
        sample_path = request.POST.get('sample_path')
        if sample_path and os.path.exists(sample_path):
            from django.core.files.base import ContentFile
            fname = os.path.basename(sample_path)
            with open(sample_path, 'rb') as f:
                file_content = f.read()
            request.FILES['file'] = ContentFile(file_content, name=fname)
        form = DatasetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            is_valid, result = validate_uploaded_file(file)

            if not is_valid:
                messages.error(request, result)
                return render(request, 'datasets/upload.html', {'form': form})

            df = result
            ext = os.path.splitext(file.name)[1].lower()
            fmt = ext.replace('.', '')

            dataset = Dataset.objects.create(
                user=request.user,
                file=file,
                original_name=file.name,
                file_format=fmt,
                file_size=file.size,
                row_count=len(df),
                column_count=len(df.columns),
            )

            profile = profile_dataset(df)
            health_report = generate_health_report(df, profile)
            health_score = calculate_health_score(health_report)

            dataset.profiling_data = _clean_json(profile)
            dataset.health_report = _clean_json(health_report)
            dataset.health_score = health_score
            dataset.save()

            messages.success(request, f'Dataset "{file.name}" uploaded successfully.')
            return redirect('datasets:overview', dataset_id=dataset.id)
    else:
        form = DatasetUploadForm()

    return render(request, 'datasets/upload.html', {'form': form})


@login_required
def dataset_overview(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
    df = read_uploaded_file(dataset.file)

    preview_rows = df.head(20).values.tolist()
    columns = list(df.columns)

    context = {
        'dataset': dataset,
        'preview': preview_rows,
        'columns': columns,
        'profiling': dataset.profiling_data,
        'health_report': dataset.health_report,
        'health_score': dataset.health_score,
    }
    return render(request, 'datasets/overview.html', context)


@login_required
def dataset_preview(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
    df = read_uploaded_file(dataset.file)
    preview = df.head(50).to_dict(orient='records')
    return JsonResponse({'preview': preview, 'columns': list(df.columns)})


SAMPLE_FILES = {
    'sales_sample.csv': 'Monthly Sales Report (10 rows, issues included)',
    'employees_sample.csv': 'Employee Directory (5 rows, basic issues)',
}


@login_required
def sample_gallery(request):
    from django.conf import settings
    samples_dir = os.path.join(settings.MEDIA_ROOT, 'samples')
    samples = []
    if os.path.exists(samples_dir):
        for fname, desc in SAMPLE_FILES.items():
            fpath = os.path.join(samples_dir, fname)
            if os.path.exists(fpath):
                samples.append({'name': fname, 'path': fpath, 'description': desc})
    return render(request, 'datasets/samples.html', {'samples': samples})


@login_required
def delete_dataset(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id, user=request.user)
    dataset.file.delete()
    dataset.delete()
    messages.success(request, 'Dataset deleted successfully.')
    return redirect('datasets:list')
