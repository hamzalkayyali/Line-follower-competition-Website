from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stopwatch_project', '0004_matchrun_finished_matchrun_checkpoints_reached'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchrun',
            name='round_type',
            field=models.CharField(choices=[('round1', 'Qualification Stage (All)'), ('round2', 'Finals (Top 8)')], max_length=10),
        ),
    ]
