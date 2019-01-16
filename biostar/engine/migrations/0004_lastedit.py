# Generated by Django 2.1.2 on 2018-12-04 15:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('engine', '0003_summary'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='lastedit_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='analysis',
            name='lastedit_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='analysis_editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='data',
            name='lastedit_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='data',
            name='lastedit_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='data_editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='job',
            name='lastedit_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='job',
            name='lastedit_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='job_editor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='project',
            name='lastedit_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='project',
            name='lastedit_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='proj_editor', to=settings.AUTH_USER_MODEL),
        ),
    ]