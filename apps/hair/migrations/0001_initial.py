from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HairSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_key', models.CharField(blank=True, max_length=100)),
                ('hair_concerns', models.JSONField(default=list)),
                ('scalp_condition', models.CharField(blank=True, max_length=50)),
                ('root_symptoms', models.JSONField(default=list)),
                ('hair_type', models.CharField(blank=True, max_length=30)),
                ('hair_texture', models.CharField(blank=True, max_length=30)),
                ('severity_stage', models.CharField(blank=True, max_length=20)),
                ('first_name', models.CharField(blank=True, max_length=80)),
                ('age', models.PositiveSmallIntegerField(default=25)),
                ('gender', models.CharField(blank=True, max_length=20)),
                ('water_intake', models.CharField(blank=True, max_length=20)),
                ('sleep_quality', models.CharField(blank=True, max_length=20)),
                ('recommended_plan', models.CharField(
                    choices=[('basic', 'Basic'), ('advanced', 'Advanced'), ('premium', 'Premium')],
                    default='basic', max_length=20)),
                ('completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='hair_sessions',
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at'], 'verbose_name': 'Hair Session'},
        ),
    ]
