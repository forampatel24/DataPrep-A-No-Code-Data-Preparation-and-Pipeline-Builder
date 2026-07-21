import pandas as pd
import time
from . import cleaning
from . import transformation
from . import validation
from . import conversion
from . import merging
from . import outliers
from . import datetime_ops
from . import numeric
from . import encoding
from . import feature_engineering
from . import statistical

OPERATION_MAP = {
    'remove_duplicates': cleaning.remove_duplicates,
    'fill_missing': cleaning.fill_missing,
    'trim_spaces': cleaning.trim_spaces,
    'normalize_text': cleaning.normalize_text,
    'standardize_capitalization': cleaning.standardize_capitalization,
    'rename_columns': cleaning.rename_columns,
    'convert_dtype': transformation.convert_dtype,
    'auto_detect_dtypes': transformation.auto_detect_dtypes,
    'boolean_conversion': transformation.boolean_conversion,
    'format_dates': transformation.format_dates,
    'uppercase': transformation.uppercase,
    'lowercase': transformation.lowercase,
    'title_case': transformation.title_case,
    'remove_special_chars': transformation.remove_special_chars,
    'add_derived_column': transformation.add_derived_column,
    'regex_replace': transformation.regex_replace,
    'extract_year': datetime_ops.extract_year,
    'extract_month': datetime_ops.extract_month,
    'extract_day': datetime_ops.extract_day,
    'extract_weekday': datetime_ops.extract_weekday,
    'extract_quarter': datetime_ops.extract_quarter,
    'calculate_age': datetime_ops.calculate_age,
    'days_between_dates': datetime_ops.days_between_dates,
    'add_days': datetime_ops.add_days,
    'subtract_days': datetime_ops.subtract_days,
    'normalize_minmax': numeric.normalize_minmax,
    'standardize_zscore': numeric.standardize_zscore,
    'log_transform': numeric.log_transform,
    'sqrt_transform': numeric.sqrt_transform,
    'absolute_value': numeric.absolute_value,
    'round_values': numeric.round_values,
    'floor_values': numeric.floor_values,
    'ceiling_values': numeric.ceiling_values,
    'clip_values': numeric.clip_values,
    'scale_by_constant': numeric.scale_by_constant,
    'label_encode': encoding.label_encode,
    'one_hot_encode': encoding.one_hot_encode,
    'ordinal_encode': encoding.ordinal_encode,
    'binary_encode': encoding.binary_encode,
    'frequency_encode': encoding.frequency_encode,
    'conditional_column': feature_engineering.conditional_column,
    'bin_values': feature_engineering.bin_values,
    'percentage_column': feature_engineering.percentage_column,
    'average_columns': feature_engineering.average_columns,
    'count_non_null': feature_engineering.count_non_null,
    'compute_mean': statistical.compute_mean,
    'compute_median': statistical.compute_median,
    'compute_mode': statistical.compute_mode,
    'compute_std': statistical.compute_std,
    'compute_variance': statistical.compute_variance,
    'compute_skewness': statistical.compute_skewness,
    'compute_kurtosis': statistical.compute_kurtosis,
    'correlation_matrix': statistical.correlation_matrix,
    'validate_emails': validation.validate_email_column,
    'validate_phones': validation.validate_phone_column,
    'validate_dates': validation.validate_date_column,
    'detect_outliers_iqr': outliers.detect_outliers_iqr,
    'detect_outliers_zscore': outliers.detect_outliers_zscore,
    'merge_datasets': merging.merge_datasets,
}


def execute_pipeline(df: pd.DataFrame, steps: list, secondary_datasets: dict = None) -> dict:
    start_time = time.time()
    current_df = df.copy()
    summary = []
    converted_output = None
    converted_content_type = None
    converted_extension = None

    for step in steps:
        operation = step.get('operation')
        config = step.get('config', {})

        if operation == 'convert_format':
            target_format = config.get('target_format', 'csv')
            converted_output, converted_content_type, converted_extension = conversion.convert_dataframe(current_df, target_format)
            summary.append({
                'operation': operation,
                'status': 'completed',
                'message': f'Converted to {target_format}',
            })
            continue

        func = OPERATION_MAP.get(operation)
        if not func:
            summary.append({
                'operation': operation,
                'status': 'skipped',
                'message': f'Unknown operation: {operation}',
            })
            continue

        try:
            if operation in ('merge_datasets',):
                if secondary_datasets and config.get('dataset_key') in secondary_datasets:
                    result = func(current_df, secondary_datasets[config['dataset_key']], **config)
                    current_df = result
                else:
                    summary.append({
                        'operation': operation,
                        'status': 'skipped',
                        'message': 'Secondary dataset not provided',
                    })
                    continue
            else:
                result = func(current_df, **config)
                current_df = result

            summary.append({
                'operation': operation,
                'status': 'completed',
                'message': f'{step.get("label", operation)} completed',
            })

        except Exception as e:
            summary.append({
                'operation': operation,
                'status': 'error',
                'message': str(e),
            })

    runtime = time.time() - start_time

    result = {
        'success': True,
        'runtime': round(runtime, 3),
        'summary': summary,
        'dataframe': current_df,
    }

    if converted_output is not None:
        result['output'] = converted_output
        result['output_content_type'] = converted_content_type
        result['output_extension'] = converted_extension

    return result
