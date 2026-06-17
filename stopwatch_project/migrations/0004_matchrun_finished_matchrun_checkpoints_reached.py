from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stopwatch_project', '0003_calibrationsession'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchrun',
            name='finished',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='matchrun',
            name='checkpoints_reached',
            field=models.IntegerField(default=0),
        ),
    ]
