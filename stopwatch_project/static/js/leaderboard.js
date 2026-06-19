/**
 * Leaderboard Page — Auto-refresh + Mini Stopwatches
 * Polls /api/leaderboard/ every 3 seconds and /api/state/ every 100ms for stopwatches.
 */

// ============================================================
// MINI STOPWATCHES (Track A & B at the top of leaderboard)
// ============================================================
const miniTracks = {
    track1: {
        lastState: 'stop',
        startTime: 0,
        interval: null,
        elapsedTime: 0,
        timeEl: 'mini-sw-a-time',
        containerEl: 'mini-sw-a',
        teamEl: 'mini-sw-a-team',
        hasEverStarted: false
    },
    track2: {
        lastState: 'stop',
        startTime: 0,
        interval: null,
        elapsedTime: 0,
        timeEl: 'mini-sw-b-time',
        containerEl: 'mini-sw-b',
        teamEl: 'mini-sw-b-team',
        hasEverStarted: false
    }
};

function updateMiniTime(trackKey) {
    const t = miniTracks[trackKey];
    const timePassed = Date.now() - t.startTime + t.elapsedTime;
    const minutes = Math.floor(timePassed / 60000).toString().padStart(2, '0');
    const seconds = Math.floor((timePassed % 60000) / 1000).toString().padStart(2, '0');
    const ms = Math.floor((timePassed % 1000) / 10).toString().padStart(2, '0');
    document.getElementById(t.timeEl).textContent = `${minutes}:${seconds}.${ms}`;
}

async function checkMiniStates() {
    try {
        const response = await fetch('/api/state/');
        const data = await response.json();

        for (const key of ['track1', 'track2']) {
            const t = miniTracks[key];
            const serverState = data[key];
            const container = document.getElementById(t.containerEl);

            if (serverState === 'start' && t.lastState !== 'start') {
                // Reset and start fresh
                t.elapsedTime = 0;
                document.getElementById(t.timeEl).textContent = '00:00.00';
                t.hasEverStarted = true;
                t.startTime = Date.now();
                if (t.interval) clearInterval(t.interval);
                t.interval = setInterval(() => updateMiniTime(key), 10);
                container.classList.add('running');
                t.lastState = 'start';
            } else if (serverState === 'stop' && t.lastState === 'start') {
                if (t.interval) {
                    clearInterval(t.interval);
                    t.interval = null;
                    t.elapsedTime += Date.now() - t.startTime;
                }
                container.classList.remove('running');
                t.lastState = 'stop';
            } else if (serverState === 'reset') {
                // Judge submitted — reset to zero
                if (t.interval) {
                    clearInterval(t.interval);
                    t.interval = null;
                }
                t.elapsedTime = 0;
                t.startTime = 0;
                t.hasEverStarted = false;
                document.getElementById(t.timeEl).textContent = '00:00.00';
                container.classList.remove('running');
                t.lastState = 'reset';
            }
        }
    } catch (err) {
        // Silently retry
    }
}

// Also fetch active run info for mini stopwatch labels
async function fetchActiveRunForMini() {
    try {
        const response = await fetch('/api/active-run/');
        const data = await response.json();

        for (const run of data.active_runs) {
            const trackKey = run.track === 'A' ? 'track1' : 'track2';
            const teamEl = document.getElementById(miniTracks[trackKey].teamEl);
            if (run.team_name) {
                teamEl.textContent = run.team_name;
                teamEl.style.color = 'var(--accent-gold)';
            } else {
                teamEl.textContent = '—';
                teamEl.style.color = '';
            }
        }
    } catch (err) { /* ignore */ }
}

// ============================================================
// LEADERBOARD DATA — Auto-refresh
// ============================================================

function getRankClass(rank) {
    if (rank === 1) return 'rank-1';
    if (rank === 2) return 'rank-2';
    if (rank === 3) return 'rank-3';
    return 'rank-default';
}

function renderRound1(teams) {
    const tbody = document.getElementById('round1-body');
    if (!teams || teams.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted" style="padding:24px;">No teams registered yet.</td></tr>';
        return;
    }

    // Sort: best time ASC, then most checkpoints DESC as tiebreaker
    teams.sort((a, b) => a.round1_best - b.round1_best || (b.best_checkpoints || 0) - (a.best_checkpoints || 0));

    tbody.innerHTML = teams.map((team, i) => {
        const rank = i + 1;
        const try1 = team.round1_try1;
        const try2 = team.round1_try2;
        const best = team.round1_best;
        const badgeClass = rank <= 8 ? 'rank-qualified' : 'rank-default';

        const fmt1 = try1 ? (team.round1_try1_dnf ? `DNF +4:00` : formatTime(try1)) : '—';
        const fmt2 = try2 ? (team.round1_try2_dnf ? `DNF +4:00` : formatTime(try2)) : '—';
        const fmtBest = best && best < 9999 ? (team.round1_best_dnf ? `DNF +4:00` : formatTime(best)) : '—';

        return `
            <tr style="animation-delay: ${(i * 0.05).toFixed(2)}s" class="${rank <= 8 ? 'row-qualified' : ''}">
                <td><span class="rank-badge ${badgeClass}">${rank}</span></td>
                <td>
                    <div class="team-info">
                        <span class="team-name">${team.team_name}</span>
                    </div>
                </td>
                <td class="time-cell ${!try1 ? 'empty' : ''}">${fmt1}</td>
                <td class="time-cell ${!try2 ? 'empty' : ''}">${fmt2}</td>
                <td class="time-cell ${best && best < 9999 ? 'best' : 'empty'}">${fmtBest}</td>
                <td class="time-cell ${team.best_checkpoints ? '' : 'empty'}" style="text-align:center;">${team.best_checkpoints || '—'}</td>
            </tr>
        `;
    }).join('');
}

function renderRound2(teams) {
    const tbody = document.getElementById('round2-body');
    if (!teams || teams.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding:24px;">Awaiting qualified teams...</td></tr>';
        return;
    }

    // Sort: best time ASC, then most checkpoints DESC as tiebreaker
    teams.sort((a, b) => a.round2_best - b.round2_best || (b.best_checkpoints || 0) - (a.best_checkpoints || 0));

    tbody.innerHTML = teams.map((team, i) => {
        const rank = i + 1;
        const r1best = team.round1_best;
        const try1 = team.round2_try1;
        const try2 = team.round2_try2;
        const best = team.round2_best;

        const fmt1 = try1 ? (team.round2_try1_dnf ? `DNF +4:00` : formatTime(try1)) : '—';
        const fmt2 = try2 ? (team.round2_try2_dnf ? `DNF +4:00` : formatTime(try2)) : '—';
        const fmtBest = best && best < 9999 ? (team.round2_best_dnf ? `DNF +4:00` : formatTime(best)) : '—';

        return `
            <tr style="animation-delay: ${(i * 0.05).toFixed(2)}s">
                <td><span class="rank-badge ${getRankClass(rank)}">${rank}</span></td>
                <td>
                    <div class="team-info">
                        <span class="team-name">${team.team_name}</span>
                    </div>
                </td>
                <td class="time-cell">${r1best && r1best < 9999 ? formatTime(r1best) : '—'}</td>
                <td class="time-cell ${!try1 ? 'empty' : ''}">${fmt1}</td>
                <td class="time-cell ${!try2 ? 'empty' : ''}">${fmt2}</td>
                <td class="time-cell ${best && best < 9999 ? 'best' : 'empty'}">${fmtBest}</td>
                <td class="time-cell ${team.best_checkpoints ? '' : 'empty'}" style="text-align:center;">${team.best_checkpoints || '—'}</td>
            </tr>
        `;
    }).join('');
}

async function fetchLeaderboard() {
    try {
        const response = await fetch('/api/leaderboard/');
        const data = await response.json();
        renderRound1(data.round1);
        renderRound2(data.round2);
    } catch (err) {
        console.error('Failed to fetch leaderboard:', err);
    }
}

// ============================================================
// INIT
// ============================================================
// Initial load
fetchLeaderboard();
fetchActiveRunForMini();

// Refresh leaderboard every 3 seconds
setInterval(fetchLeaderboard, 3000);

// Check stopwatch state every 100ms
setInterval(checkMiniStates, 100);

// Refresh active run info every 5 seconds
setInterval(fetchActiveRunForMini, 5000);
