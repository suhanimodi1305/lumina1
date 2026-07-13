# Generated migration for ProgressComparison model
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scanner', '0004_merge_20260708_2239'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgressComparison',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('harmony_delta', models.IntegerField(default=0, help_text='Change in harmony score (latest - baseline)')),
                ('hydration_delta', models.IntegerField(default=0)),
                ('acne_delta', models.IntegerField(default=0, help_text='Positive = more acne, negative = improvement')),
                ('pigmentation_delta', models.IntegerField(default=0)),
                ('aging_delta', models.IntegerField(default=0, help_text='Positive = more aging, negative = improvement')),
                ('elasticity_delta', models.IntegerField(default=0)),
                ('days_between', models.IntegerField(default=0, help_text='Days between baseline and latest scan')),
                ('ai_verdict', models.CharField(
                    max_length=20, default='unchanged',
                    choices=[
                        ('improved', 'Improved'),
                        ('unchanged', 'Unchanged'),
                        ('declined', 'Declined'),
                    ]
                )),
                ('ai_recommendation', models.TextField(blank=True, help_text='AI-generated recommendation based on comparison')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='progress_comparisons',
                    to=settings.AUTH_USER_MODEL
                )),
                ('baseline_scan', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='as_baseline',
                    to='scanner.scanresult'
                )),
                ('latest_scan', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='as_latest',
                    to='scanner.scanresult'
                )),
            ],
            options={
                'verbose_name': 'Progress Comparison',
                'ordering': ['-created_at'],
            },
        ),
    ]
