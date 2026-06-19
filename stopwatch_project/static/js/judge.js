/**
 * Judge Portal — Form handling, penalty counter, active run management
 */

// ============================================================
// PENALTY COUNTERS
// ============================================================
let trackDamageCount = 0;
let humanPenaltyCount = 0;

function changePenalty(type, delta) {
    if (type === 'track') {
        trackDamageCount = Math.max(0, trackDamageCount + delta);
        document.getElementById('track-penalty-count').textContent = trackDamageCount;
    } else {
        humanPenaltyCount = Math.max(0, humanPenaltyCount + delta);
        document.getElementById('human-penalty-count').textContent = humanPenaltyCount;
    }
    
    const totalPenaltySeconds = (trackDamageCount * 4.0) + (humanPenaltyCount * 2.0);
    document.getElementById('total-penalty-time').textContent = `+${totalPenaltySeconds.toFixed(1)}s`;
}

// ============================================================
// LOAD TEAMS INTO DROPDOWNS
// ============================================================
let allTeams = [];

async function loadTeams() {
    try {
        const response = await fetch('/api/teams/');
        const data = await response.json();
        allTeams = data.teams;
        populateTeamSelect();
    } catch (err) {
        console.error('Failed to load teams:', err);
        showToast('Failed to load teams', 'error');
    }
}

function populateTeamSelect() {
    const roundType = document.querySelector('input[name="round"]:checked')?.value || 'round1';
    const select = document.getElementById('team-select');
    const placeholder = select.options[0];
    select.innerHTML = '';
    select.appendChild(placeholder);

    const teamsToShow = roundType === 'round2' ? allTeams.filter(t => t.qualified) : allTeams;
    for (const team of teamsToShow) {
        const option = document.createElement('option');
        option.value = team.id;
        option.textContent = team.team_name;
        select.appendChild(option);
    }
}

// ============================================================
// MANUAL STOPWATCH CONTROL (recover stuck stopwatches)
// ============================================================
async function manualStopwatch(track, action) {
    try {
        const response = await fetch(`/api/${track}/${action}/`, { method: 'POST' });
        if (response.ok) {
            showToast(`${track === 'track1' ? 'Track A' : 'Track B'} ${action === 'stop' ? 'stopped' : 'reset'}`, 'success');
        } else {
            showToast('Failed to control stopwatch', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
}

// ============================================================
// SUBMIT RUN RESULT
// ============================================================
async function submitRun(event) {
    event.preventDefault();

    const teamId = document.getElementById('team-select').value;
    const roundType = document.querySelector('input[name="round"]:checked').value;
    const tryNumber = document.querySelector('input[name="try"]:checked').value;
    const track = document.querySelector('input[name="track"]:checked').value;
    const rawTime = parseFloat(document.getElementById('time-input').value);
    const confirmed = document.getElementById('player-confirmed').checked;
    const finished = document.getElementById('robot-finished').checked;
    const checkpoints = parseInt(document.getElementById('checkpoints-input').value) || 0;

    // Validation
    if (!teamId) {
        showToast('Please select a team', 'error');
        return;
    }
    if (isNaN(rawTime) || rawTime <= 0) {
        showToast('Please enter a valid time', 'error');
        return;
    }
    if (!confirmed) {
        showToast('Player must confirm the time', 'error');
        return;
    }

    const btn = document.getElementById('btn-submit');
    btn.disabled = true;
    btn.textContent = 'SUBMITTING...';

    try {
        const response = await fetch('/api/submit-run/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                team_id: parseInt(teamId),
                round_type: roundType,
                try_number: tryNumber,
                track: track,
                raw_time: rawTime,
                track_damage_penalties: trackDamageCount,
                human_penalties: humanPenaltyCount,
                player_confirmed: confirmed,
                finished: finished,
                checkpoints_reached: checkpoints
            })
        });

        const result = await response.json();

        if (response.ok) {
            const totalTime = rawTime + (trackDamageCount * 4.0) + (humanPenaltyCount * 2.0);
            showToast(`Run submitted! Total time: ${totalTime.toFixed(2)}s`, 'success');
            resetForm();
        } else {
            showToast(result.error || 'Failed to submit run', 'error');
        }
    } catch (err) {
        showToast('Network error — please try again', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Submit Run Result';
    }
}

async function deleteRunResult() {
    const teamSelect = document.getElementById('team-select');
    const teamId = teamSelect.value;
    const roundType = document.querySelector('input[name="round"]:checked').value;
    const tryNumber = document.querySelector('input[name="try"]:checked').value;

    if (!teamId) {
        showToast('Please select a team first', 'error');
        return;
    }

    const teamText = teamSelect.options[teamSelect.selectedIndex].text;
    const roundText = roundType === 'round1' ? 'Qualification Stage' : 'Finals';
    const tryText = tryNumber === 'try1' ? 'Try 1' : 'Try 2';

    if (!confirm(`Are you sure you want to delete the run result for ${teamText} (${roundText}, ${tryText})?\nThis action cannot be undone.`)) {
        return;
    }

    const btn = document.getElementById('btn-delete-run');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Deleting...';

    try {
        const response = await fetch('/api/delete-run/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                team_id: parseInt(teamId),
                round_type: roundType,
                try_number: tryNumber
            })
        });

        const result = await response.json();

        if (response.ok) {
            showToast('Run deleted successfully', 'success');
        } else {
            showToast(result.error || 'Failed to delete run', 'error');
        }
    } catch (err) {
        showToast('Network error — please try again', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

function toggleCheckpoints() {
    const finished = document.getElementById('robot-finished').checked;
    document.getElementById('checkpoints-row').style.display = finished ? 'none' : 'block';
}

function resetForm() {
    document.getElementById('run-form').reset();
    trackDamageCount = 0;
    humanPenaltyCount = 0;
    document.getElementById('track-penalty-count').textContent = '0';
    document.getElementById('human-penalty-count').textContent = '0';
    document.getElementById('total-penalty-time').textContent = '+0.0s';
    document.getElementById('robot-finished').checked = true;
    document.getElementById('checkpoints-row').style.display = 'none';
    document.getElementById('checkpoints-input').value = '0';
}

// ============================================================
// TEAM MANAGEMENT
// ============================================================
let editingTeamId = null;

async function loadTeamList() {
    try {
        const response = await fetch('/api/teams/');
        const data = await response.json();
        const tbody = document.getElementById('team-mgmt-body');
        const badge = document.getElementById('team-count-badge');

        badge.textContent = `${data.teams.length} teams`;

        if (data.teams.length === 0) {
            tbody.innerHTML = '<tr><td colspan="2" class="text-center text-muted" style="padding:16px;">No teams added yet. Add your first team above.</td></tr>';
            return;
        }

        tbody.innerHTML = data.teams.map((team, i) => `
            <tr style="animation-delay: ${(i * 0.04).toFixed(2)}s">
                <td>
                    <span class="team-name">${team.team_name}</span>
                </td>
                <td style="text-align:center;">
                    <button class="penalty-btn" onclick="startEditTeam(${team.id}, ${team.team_number}, '${team.team_name.replace(/'/g, "\\'")}')"
                            style="width:32px; height:32px; font-size:1rem; border-color:rgba(0,173,181,0.3); margin-right:4px;"
                            title="Edit team">✎</button>
                    <button class="penalty-btn" onclick="deleteTeam(${team.id}, '${team.team_name.replace(/'/g, "\\'")}')"
                            style="width:32px; height:32px; font-size:1rem; border-color:rgba(231,76,60,0.3);"
                            title="Delete team">✕</button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load team list:', err);
    }
}

function startEditTeam(teamId, teamNumber, teamName) {
    editingTeamId = teamId;
    document.getElementById('new-team-number').value = teamNumber;
    document.getElementById('new-team-name').value = teamName;
    document.getElementById('btn-save-team').textContent = 'Save Changes';
    document.getElementById('btn-save-team').style.background = 'var(--accent-gold)';
    document.getElementById('btn-save-team').style.borderColor = 'var(--accent-gold)';
    document.getElementById('btn-cancel-edit').style.display = 'inline-block';
}

function cancelEdit() {
    editingTeamId = null;
    document.getElementById('new-team-number').value = '';
    document.getElementById('new-team-name').value = '';
    document.getElementById('btn-save-team').textContent = '+ Add Team';
    document.getElementById('btn-save-team').style.background = '';
    document.getElementById('btn-save-team').style.borderColor = '';
    document.getElementById('btn-cancel-edit').style.display = 'none';
}

async function saveTeam() {
    const numberInput = document.getElementById('new-team-number');
    const nameInput = document.getElementById('new-team-name');
    const teamNumber = parseInt(numberInput.value);
    const teamName = nameInput.value.trim();

    if (!teamNumber || teamNumber < 1) {
        showToast('Please enter a valid team number', 'error');
        return;
    }
    if (!teamName) {
        showToast('Please enter a team name', 'error');
        return;
    }

    const endpoint = editingTeamId ? '/api/edit-team/' : '/api/add-team/';
    const payload = { team_number: teamNumber, team_name: teamName };
    if (editingTeamId) {
        payload.team_id = editingTeamId;
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            showToast(editingTeamId ? `Team updated!` : `Team #${teamNumber} added!`, 'success');
            cancelEdit();
            loadTeams();
            loadTeamList();
        } else {
            showToast(result.error || 'Failed to save team', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
}

async function deleteTeam(teamId, teamName) {
    if (!confirm(`Delete "${teamName}" and ALL their run data? This cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch('/api/delete-team/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team_id: teamId })
        });

        const result = await response.json();

        if (response.ok) {
            showToast(`"${result.deleted}" has been removed`, 'success');
            loadTeams();
            loadTeamList();
        } else {
            showToast(result.error || 'Failed to delete team', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
}

// ============================================================
// INIT
// ============================================================
loadTeams();
loadTeamList();
