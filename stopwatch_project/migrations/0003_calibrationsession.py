from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stopwatch_project', '0002_remove_matchrun_penalties_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalibrationSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('is_running', models.BooleanField(default=False)),
                ('elapsed_before_pause', models.FloatField(default=0.0)),
                ('duration', models.FloatField(default=600.0)),
                ('team_a', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='calib_track_a', to='stopwatch_project.team')),
                ('team_b', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='calib_track_b', to='stopwatch_project.team')),
            ],
            options={
                'verbose_name': 'Calibration Session',
            },
        ),
    ]
