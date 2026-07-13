from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scanner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scanresult',
            name='qa_age',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scanresult',
            name='qa_water_intake',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='scanresult',
            name='qa_sleep_hours',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='scanresult',
            name='qa_stress_level',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='scanresult',
            name='qa_diet',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='scanresult',
            name='qa_outdoor_hours',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='scanresult',
            name='qa_skin_concerns',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='scanresult',
            name='qa_completed',
            field=models.BooleanField(default=False),
        ),
    ]
