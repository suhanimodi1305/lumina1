from django.db import migrations


class Migration(migrations.Migration):
    """Remove the unused results.ScanResult model.
    All scan data is stored in scanner.ScanResult directly.
    """

    dependencies = [
        ('results', '0002_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ScanResult',
        ),
    ]
