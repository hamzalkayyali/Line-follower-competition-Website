from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stopwatch_project', '0005_alter_matchrun_round_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='qualified',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='CompetitionState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('qualification_locked', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Competition State',
            },
        ),
    ]
