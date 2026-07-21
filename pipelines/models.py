from django.db import models
from django.conf import settings


class Pipeline(models.Model):
    OUTPUT_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('json', 'JSON'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pipelines')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    output_format = models.CharField(max_length=10, choices=OUTPUT_FORMAT_CHOICES, default='csv')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class PipelineStep(models.Model):
    OPERATION_CHOICES = [
        ('remove_duplicates', 'Remove Duplicates'),
        ('fill_missing', 'Fill Missing Values'),
        ('trim_spaces', 'Trim Spaces'),
        ('normalize_text', 'Normalize Text'),
        ('standardize_capitalization', 'Standardize Capitalization'),
        ('rename_columns', 'Rename Columns'),
        ('convert_dtype', 'Convert Data Type'),
        ('auto_detect_dtypes', 'Auto Detect Data Types'),
        ('boolean_conversion', 'Boolean Conversion'),
        ('format_dates', 'Format Dates'),
        ('uppercase', 'Uppercase'),
        ('lowercase', 'Lowercase'),
        ('title_case', 'Title Case'),
        ('remove_special_chars', 'Remove Special Characters'),
        ('regex_replace', 'Regex Find & Replace'),
        ('add_derived_column', 'Add Derived Column'),
        ('extract_year', 'Extract Year'),
        ('extract_month', 'Extract Month'),
        ('extract_day', 'Extract Day'),
        ('extract_weekday', 'Extract Weekday'),
        ('extract_quarter', 'Extract Quarter'),
        ('calculate_age', 'Calculate Age'),
        ('days_between_dates', 'Days Between Dates'),
        ('add_days', 'Add Days'),
        ('subtract_days', 'Subtract Days'),
        ('normalize_minmax', 'Normalize (Min-Max)'),
        ('standardize_zscore', 'Standardize (Z-Score)'),
        ('log_transform', 'Log Transform'),
        ('sqrt_transform', 'Square Root Transform'),
        ('absolute_value', 'Absolute Value'),
        ('round_values', 'Round Values'),
        ('floor_values', 'Floor Values'),
        ('ceiling_values', 'Ceiling Values'),
        ('clip_values', 'Clip Values'),
        ('scale_by_constant', 'Scale by Constant'),
        ('label_encode', 'Label Encoding'),
        ('one_hot_encode', 'One-Hot Encoding'),
        ('ordinal_encode', 'Ordinal Encoding'),
        ('binary_encode', 'Binary Encoding'),
        ('frequency_encode', 'Frequency Encoding'),
        ('conditional_column', 'Conditional Column (IF ELSE)'),
        ('bin_values', 'Bin Numerical Values'),
        ('percentage_column', 'Percentage Column'),
        ('average_columns', 'Average Columns'),
        ('count_non_null', 'Count Non-Null Values'),
        ('compute_mean', 'Mean'),
        ('compute_median', 'Median'),
        ('compute_mode', 'Mode'),
        ('compute_std', 'Standard Deviation'),
        ('compute_variance', 'Variance'),
        ('compute_skewness', 'Skewness'),
        ('compute_kurtosis', 'Kurtosis'),
        ('correlation_matrix', 'Correlation Matrix'),
        ('validate_emails', 'Validate Emails'),
        ('validate_phones', 'Validate Phones'),
        ('validate_dates', 'Validate Dates'),
        ('detect_outliers_iqr', 'Detect Outliers (IQR)'),
        ('detect_outliers_zscore', 'Detect Outliers (Z-Score)'),
        ('merge_datasets', 'Merge Datasets'),
    ]

    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='steps')
    step_order = models.PositiveIntegerField()
    operation = models.CharField(max_length=50, choices=OPERATION_CHOICES)
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['step_order']
        unique_together = ['pipeline', 'step_order']

    def __str__(self):
        return f'{self.pipeline.name} - Step {self.step_order}: {self.get_operation_display()}'


class ProcessingHistory(models.Model):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.SET_NULL, null=True, related_name='history')
    dataset = models.ForeignKey('datasets.Dataset', on_delete=models.SET_NULL, null=True, blank=True, related_name='processing_history')
    executed_at = models.DateTimeField(auto_now_add=True)
    runtime = models.FloatField(help_text='Execution time in seconds')
    output_format = models.CharField(max_length=10)
    summary = models.JSONField(default=dict, blank=True, help_text='Summary of operations performed')
    output_file = models.FileField(upload_to='processed/', null=True, blank=True)

    class Meta:
        ordering = ['-executed_at']
        verbose_name_plural = 'processing histories'

    def __str__(self):
        return f'{self.pipeline.name} - {self.executed_at}' if self.pipeline else f'History - {self.executed_at}'
