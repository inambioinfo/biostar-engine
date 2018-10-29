# Generated by Django 2.1.2 on 2018-10-28 18:46

from django.db import migrations, models


def format_summary(apps, schema_editor):
    """Add the summary as first line of text.  """

    recipes = apps.get_model('engine', 'Analysis')
    for recipe in recipes.objects.all():

        # Add summary as first line of text
        recipe.text = recipe.summary + "\n" + recipe.text
        recipe.save()

    return


class Migration(migrations.Migration):

    dependencies = [
        ('engine', '0002_bigint'),
    ]

    operations = [
        migrations.RunPython(format_summary),

        migrations.RemoveField(
            model_name='analysis',
            name='summary',
        ),

        migrations.AlterField(
            model_name='access',
            name='access',
            field=models.IntegerField(choices=[(1, 'No Access'), (2, 'Read Access'), (3, 'Write Access')], db_index=True, default=1),
        ),

    ]