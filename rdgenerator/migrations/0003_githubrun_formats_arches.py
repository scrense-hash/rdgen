from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rdgenerator', '0002_githubrun_github_run_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='githubrun',
            name='formats',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='formats'),
        ),
        migrations.AddField(
            model_name='githubrun',
            name='arches',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='arches'),
        ),
    ]
