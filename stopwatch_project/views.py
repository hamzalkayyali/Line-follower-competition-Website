import os
import json
# pyrefly: ignore [missing-import]
from django.http import HttpResponse, JsonResponse # pyright: ignore[reportMissingModuleSource]
# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect # pyright: ignore[reportMissingModuleSource]
# pyrefly: ignore [missing-import]
from django.views.decorators.csrf import csrf_exempt # pyright: ignore[reportMissingModuleSource]
from django.utils import timezone # pyright: ignore[reportMissingModuleSource]
from .models import Team, MatchRun, ActiveRun, CalibrationSession

JUDGE_PIN = os.environ.get('JUDGE_PIN', '1234')
ORGANIZER_PIN = os.environ.get('ORGANIZER_PIN', '0000')

# ============================================================
# IN-MEMORY STOPWATCH STATE (driven by ESP32 triggers)
# ============================================================
stopwatch_states = {
    "track1": "stop",
    "track2": "stop"
}


# ============================================================
# PAGE VIEWS — Render Templates
# ============================================================
def leaderboard_page(request):
    """Renders the leaderboard page with mini stopwatches and two ranking tables."""
    return render(request, 'leaderboard.html')


def display_page(request):
    """Renders the full-screen projector display with dual stopwatches."""
    return render(request, 'display.html')


def judge_login(request):
    """PIN login page for the judge portal."""
    if request.session.get('is_judge'):
        return redirect('judge')
    error = None
    if request.method == 'POST':
        if request.POST.get('pin') == JUDGE_PIN:
            request.session['is_judge'] = True
            return redirect('judge')
        error = 'Wrong PIN. Try again.'
    return render(request, 'judge_login.html', {'error': error})


def judge_logout(request):
    """Clears the judge session."""
    request.session.pop('is_judge', None)
    return redirect('leaderboard')


def judge_page(request):
    """Renders the judge portal form page."""
    if not request.session.get('is_judge'):
        return redirect('judge_login')
    return render(request, 'judge.html')


# ============================================================
# LEGACY — Original stopwatch page (kept for backwards compat)
# ============================================================
def stopwatch_page(request):
    """Redirects to the new display page."""
    return display_page(request)


# ============================================================
# API — Stopwatch State (ESP32 integration)
# ============================================================
def get_state(request):
    """Returns the current stopwatch state dictionary to the web page."""
    return JsonResponse(stopwatch_states)


@csrf_exempt
def trigger_event(request, track, action):
    """Receives incoming POST requests from the ESP32 units."""
    global stopwatch_states
    if request.method == 'POST' and track in stopwatch_states and action in ['start', 'stop', 'reset']:
        stopwatch_states[track] = action
        print(f"[{track.upper()}] ESP32 changed state to: {action}")
        return HttpResponse("OK", status=200)
    return HttpResponse("Bad Request", status=400)


# ============================================================
# API — Teams List
# ============================================================
def api_teams(request):
    """Returns all teams as JSON for dropdowns."""
    teams = Team.objects.all().order_by('team_number')
    data = {
        'teams': [
            {
                'id': t.id,
                'team_number': t.team_number,
                'team_name': t.team_name
            }
            for t in teams
        ]
    }
    return JsonResponse(data)


# ============================================================
# API — Leaderboard Data
# ============================================================
def api_leaderboard(request):
    """Returns all leaderboard data as JSON, sorted and structured for both rounds."""
    teams = Team.objects.all()

    round1_data = []
    round2_data = []

    for team in teams:
        # Round 1 data
        r1_try1_run = team.runs.filter(round_type='round1', try_number='try1').first()
        r1_try2_run = team.runs.filter(round_type='round1', try_number='try2').first()

        r1_try1 = r1_try1_run.total_time if r1_try1_run else None
        r1_try2 = r1_try2_run.total_time if r1_try2_run else None
        r1_best = team.round1_best

        round1_data.append({
            'team_id': team.id,
            'team_number': team.team_number,
            'team_name': team.team_name,
            'round1_try1': r1_try1,
            'round1_try2': r1_try2,
            'round1_best': r1_best,
        })

        # Round 2 data (only teams that have round 2 runs)
        r2_try1_run = team.runs.filter(round_type='round2', try_number='try1').first()
        r2_try2_run = team.runs.filter(round_type='round2', try_number='try2').first()

        if r2_try1_run or r2_try2_run:
            r2_try1 = r2_try1_run.total_time if r2_try1_run else None
            r2_try2 = r2_try2_run.total_time if r2_try2_run else None
            r2_best = team.round2_best

            round2_data.append({
                'team_id': team.id,
                'team_number': team.team_number,
                'team_name': team.team_name,
                'round1_best': r1_best,
                'round2_try1': r2_try1,
                'round2_try2': r2_try2,
                'round2_best': r2_best,
            })

    # Sort by best time (ascending)
    round1_data.sort(key=lambda x: x['round1_best'])
    round2_data.sort(key=lambda x: x['round2_best'])

    return JsonResponse({
        'round1': round1_data,
        'round2': round2_data
    })


# ============================================================
# API — Submit Run Result
# ============================================================
@csrf_exempt
def api_submit_run(request):
    """Judge submits a run result. Creates or updates a MatchRun record."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    team_id = data.get('team_id')
    round_type = data.get('round_type')
    try_number = data.get('try_number')
    track = data.get('track')
    raw_time = data.get('raw_time')
    track_damage = data.get('track_damage_penalties', 0)
    human_penalties = data.get('human_penalties', 0)
    player_confirmed = data.get('player_confirmed', False)

    # Validate
    if not all([team_id, round_type, try_number, track, raw_time is not None]):
        return JsonResponse({'error': 'Missing required fields'}, status=400)

    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return JsonResponse({'error': 'Team not found'}, status=404)

    if not player_confirmed:
        return JsonResponse({'error': 'Player must confirm the time'}, status=400)

    # Create or update the MatchRun
    run, created = MatchRun.objects.update_or_create(
        team=team,
        round_type=round_type,
        try_number=try_number,
        defaults={
            'track': track,
            'raw_time': float(raw_time),
            'track_damage_penalties': int(track_damage),
            'human_penalties': int(human_penalties),
            'player_confirmed': player_confirmed,
        }
    )

    # Reset the stopwatch and clear active run for this track
    track_key = 'track1' if track == 'A' else 'track2'
    stopwatch_states[track_key] = 'reset'

    # Clear the active team from this track
    try:
        active_run = ActiveRun.objects.get(track=track)
        active_run.team = None
        active_run.save()
    except ActiveRun.DoesNotExist:
        pass

    return JsonResponse({
        'success': True,
        'created': created,
        'total_time': run.total_time,
        'team_name': team.team_name,
        'team_number': team.team_number,
    })


@csrf_exempt
def api_delete_run(request):
    """Judge deletes a specific run for a team."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    team_id = data.get('team_id')
    round_type = data.get('round_type')
    try_number = data.get('try_number')

    if not all([team_id, round_type, try_number]):
        return JsonResponse({'error': 'team_id, round_type, and try_number are required'}, status=400)

    try:
        run = MatchRun.objects.get(team_id=team_id, round_type=round_type, try_number=try_number)
        run.delete()
        return JsonResponse({'success': True, 'message': 'Run deleted successfully'})
    except MatchRun.DoesNotExist:
        return JsonResponse({'error': 'Run not found'}, status=404)


# ============================================================
# API — Active Run (for Display page)
# ============================================================
def api_active_run(request):
    """Returns the currently active teams on each track."""
    active_runs = []
    for track_code in ['A', 'B']:
        try:
            ar = ActiveRun.objects.get(track=track_code)
            active_runs.append({
                'track': track_code,
                'team_id': ar.team.id if ar.team else None,
                'team_number': ar.team.team_number if ar.team else None,
                'team_name': ar.team.team_name if ar.team else None,
                'round_type': ar.round_type,
                'try_number': ar.try_number,
            })
        except ActiveRun.DoesNotExist:
            active_runs.append({
                'track': track_code,
                'team_id': None,
                'team_number': None,
                'team_name': None,
                'round_type': 'round1',
                'try_number': 'try1',
            })

    return JsonResponse({'active_runs': active_runs})


@csrf_exempt
def api_set_active_run(request):
    """Judge sets which team is about to play on a specific track."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    team_id = data.get('team_id')
    track = data.get('track')
    round_type = data.get('round_type', 'round1')
    try_number = data.get('try_number', 'try1')

    if not team_id or not track:
        return JsonResponse({'error': 'team_id and track are required'}, status=400)

    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return JsonResponse({'error': 'Team not found'}, status=404)

    # Reset the stopwatch state for this track when setting a new active run
    track_key = 'track1' if track == 'A' else 'track2'
    stopwatch_states[track_key] = 'stop'

    active_run, _ = ActiveRun.objects.update_or_create(
        track=track,
        defaults={
            'team': team,
            'round_type': round_type,
            'try_number': try_number,
        }
    )

    return JsonResponse({
        'success': True,
        'track': track,
        'team_name': team.team_name,
        'team_number': team.team_number,
    })


@csrf_exempt
def api_clear_active_run(request):
    """Judge clears the active team from a specific track."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    track = data.get('track')

    if not track:
        return JsonResponse({'error': 'track is required'}, status=400)

    try:
        active_run = ActiveRun.objects.get(track=track)
        active_run.team = None
        active_run.save()
    except ActiveRun.DoesNotExist:
        pass

    return JsonResponse({'success': True, 'track': track})


# ============================================================
# API — Team Management
# ============================================================
@csrf_exempt
def api_add_team(request):
    """Add a new team to the database."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    team_number = data.get('team_number')
    team_name = data.get('team_name', '').strip()

    if not team_number or not team_name:
        return JsonResponse({'error': 'Team number and name are required'}, status=400)

    # Check for duplicate team number
    if Team.objects.filter(team_number=team_number).exists():
        return JsonResponse({'error': f'Team #{team_number} already exists'}, status=400)

    team = Team.objects.create(team_number=int(team_number), team_name=team_name)

    return JsonResponse({
        'success': True,
        'id': team.id,
        'team_number': team.team_number,
        'team_name': team.team_name,
    })


@csrf_exempt
def api_edit_team(request):
    """Edit an existing team's name and/or number."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    team_id = data.get('team_id')
    team_number = data.get('team_number')
    team_name = data.get('team_name', '').strip()

    if not team_id or not team_number or not team_name:
        return JsonResponse({'error': 'team_id, team_number, and team_name are required'}, status=400)

    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return JsonResponse({'error': 'Team not found'}, status=404)

    # Check for duplicate team number if it was changed
    if int(team_number) != team.team_number:
        if Team.objects.filter(team_number=team_number).exists():
            return JsonResponse({'error': f'Team #{team_number} already exists. Team numbers must be unique.'}, status=400)

    team.team_number = int(team_number)
    team.team_name = team_name
    team.save()

    return JsonResponse({
        'success': True,
        'id': team.id,
        'team_number': team.team_number,
        'team_name': team.team_name,
    })


@csrf_exempt
def api_delete_team(request):
    """Delete a team and all its runs from the database."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    team_id = data.get('team_id')
    if not team_id:
        return JsonResponse({'error': 'team_id is required'}, status=400)

    try:
        team = Team.objects.get(id=team_id)
        team_name = team.team_name
        team.delete()
        return JsonResponse({'success': True, 'deleted': team_name})
    except Team.DoesNotExist:
        return JsonResponse({'error': 'Team not found'}, status=404)


# ============================================================
# CALIBRATION — Organizer Login / Logout
# ============================================================
def calibration_login(request):
    if request.session.get('is_organizer'):
        return redirect('calibration_control')
    error = None
    if request.method == 'POST':
        if request.POST.get('pin') == ORGANIZER_PIN:
            request.session['is_organizer'] = True
            return redirect('calibration_control')
        error = 'Wrong PIN. Try again.'
    return render(request, 'calibration_login.html', {'error': error})


def calibration_logout(request):
    request.session.pop('is_organizer', None)
    return redirect('leaderboard')


# ============================================================
# CALIBRATION — Pages
# ============================================================
def calibration_display(request):
    return render(request, 'calibration_display.html')


def calibration_control(request):
    if not request.session.get('is_organizer'):
        return redirect('calibration_login')
    teams = Team.objects.all().order_by('team_number')
    return render(request, 'calibration_control.html', {'teams': teams})


# ============================================================
# CALIBRATION — API
# ============================================================
def _get_session():
    session, _ = CalibrationSession.objects.get_or_create(id=1)
    return session


def api_calibration_state(request):
    s = _get_session()
    team_a = s.team_a
    team_b = s.team_b
    return JsonResponse({
        'is_running': s.is_running,
        'is_finished': s.is_finished,
        'remaining': s.remaining_seconds,
        'team_a': {'id': team_a.id, 'number': team_a.team_number, 'name': team_a.team_name} if team_a else None,
        'team_b': {'id': team_b.id, 'number': team_b.team_number, 'name': team_b.team_name} if team_b else None,
    })


@csrf_exempt
def api_calibration_start(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    s = _get_session()
    if not s.is_running and not s.is_finished:
        s.started_at = timezone.now()
        s.is_running = True
        s.save()
    return JsonResponse({'success': True})


@csrf_exempt
def api_calibration_pause(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    s = _get_session()
    if s.is_running and s.started_at:
        s.elapsed_before_pause += (timezone.now() - s.started_at).total_seconds()
        s.is_running = False
        s.started_at = None
        s.save()
    return JsonResponse({'success': True})


@csrf_exempt
def api_calibration_reset(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    s = _get_session()
    s.is_running = False
    s.started_at = None
    s.elapsed_before_pause = 0.0
    s.save()
    return JsonResponse({'success': True})


@csrf_exempt
def api_calibration_set_teams(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    s = _get_session()
    team_a_id = data.get('team_a_id')
    team_b_id = data.get('team_b_id')
    s.team_a = Team.objects.get(id=team_a_id) if team_a_id else None
    s.team_b = Team.objects.get(id=team_b_id) if team_b_id else None
    s.save()
    return JsonResponse({'success': True})