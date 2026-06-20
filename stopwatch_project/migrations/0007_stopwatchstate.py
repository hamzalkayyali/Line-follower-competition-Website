from django.db import migrations, models


def seed_stopwatch_states(apps, schema_editor):
    StopwatchState = apps.get_model('stopwatch_project', 'StopwatchState')
    for track in ['track1', 'track2']:
        StopwatchState.objects.get_or_create(track=track, defaults={'state': 'stop'})


class Migration(migrations.Migration):

    dependencies = [
        ('stopwatch_project', '0006_team_qualified_competitionstate'),
    ]

    operations = [
        migrations.CreateModel(
            name='StopwatchState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('track', models.CharField(max_length=10, unique=True)),
                ('state', models.CharField(default='stop', max_length=10)),
            ],
        ),
        migrations.RunPython(seed_stopwatch_states, migrations.RunPython.noop),
    ]
