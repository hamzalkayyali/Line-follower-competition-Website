# pyrefly: ignore [missing-import]
from django.db import models

class Team(models.Model):
    team_number = models.IntegerField(unique=True)
    team_name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"#{self.team_number} - {self.team_name}"

    @property
    def round1_best(self):
        """Calculates the best time from Round 1 trials automatically"""
        runs = self.runs.filter(round_type='round1')
        valid_times = [run.total_time for run in runs if run.total_time > 0]
        return min(valid_times) if valid_times else 9999.99

    @property
    def round2_best(self):
        """Calculates the best time from Round 2 trials automatically"""
        runs = self.runs.filter(round_type='round2')
        valid_times = [run.total_time for run in runs if run.total_time > 0]
        return min(valid_times) if valid_times else 9999.99

class MatchRun(models.Model):
    ROUND_CHOICES = [('round1', 'Round 1 (All)'), ('round2', 'Round 2 (Top 6)')]
    TRY_CHOICES = [('try1', 'Try 1'), ('try2', 'Try 2')]
    TRACK_CHOICES = [('A', 'Track A'), ('B', 'Track B')]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='runs')
    round_type = models.CharField(max_length=10, choices=ROUND_CHOICES)
    try_number = models.CharField(max_length=10, choices=TRY_CHOICES)
    track = models.CharField(max_length=1, choices=TRACK_CHOICES)
    
    raw_time = models.FloatField(default=0.0)  # Time recorded by stopwatch
    track_damage_penalties = models.IntegerField(default=0)  # Adds 4s each
    human_penalties = models.IntegerField(default=0)  # Adds 2s each
    
    player_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_time(self):
        """Automatically adds penalties directly onto total time"""
        return self.raw_time + (self.track_damage_penalties * 4.0) + (self.human_penalties * 2.0)

    class Meta:
        # Prevent duplicate entries for the same team/round/try combo
        unique_together = ['team', 'round_type', 'try_number']

    def __str__(self):
        return f"{self.team} — {self.round_type} {self.try_number} ({self.total_time}s)"


class CalibrationSession(models.Model):
    """Stores the shared calibration timer state."""
    started_at = models.DateTimeField(null=True, blank=True)
    is_running = models.BooleanField(default=False)
    elapsed_before_pause = models.FloatField(default=0.0)  # seconds accumulated before last pause
    duration = models.FloatField(default=600.0)  # 10 minutes in seconds
    team_a = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='calib_track_a')
    team_b = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='calib_track_b')

    @property
    def remaining_seconds(self):
        from django.utils import timezone
        if self.is_running and self.started_at:
            elapsed = self.elapsed_before_pause + (timezone.now() - self.started_at).total_seconds()
        else:
            elapsed = self.elapsed_before_pause
        remaining = self.duration - elapsed
        return max(remaining, 0.0)

    @property
    def is_finished(self):
        return self.remaining_seconds <= 0

    class Meta:
        verbose_name = 'Calibration Session'


class ActiveRun(models.Model):
    """Tracks which team is currently on each track for the display page"""
    TRACK_CHOICES = [('A', 'Track A'), ('B', 'Track B')]

    track = models.CharField(max_length=1, choices=TRACK_CHOICES, unique=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    round_type = models.CharField(max_length=10, default='round1')
    try_number = models.CharField(max_length=10, default='try1')

    def __str__(self):
        return f"Track {self.track}: {self.team or 'Empty'}"