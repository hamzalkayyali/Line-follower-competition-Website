/**
 * Display Page — Full-Screen Stopwatches with Team Info
 * Two panels (Track A / Track B). Polls ESP32 state + active run data.
 */

// ============================================================
// STOPWATCH STATE ENGINES
// ============================================================
const displayTracks = {
    track1: {
        lastState: 'stop',
        startTime: 0,
        interval: null,
        elapsedTime: 0,
        timeEl: 'display-a-time',
        statusEl: 'display-a-status',
        hasEverStarted: false,
        hasStopped: false
    },
    track2: {
        lastState: 'stop',
        startTime: 0,
        interval: null,
        elapsedTime: 0,
        timeEl: 'display-b-time',
        statusEl: 'display-b-status',
        hasEverStarted: false,
        hasStopped: false
    }
};

function updateDisplayTime(trackKey) {
    const t = displayTracks[trackKey];
    const timePassed = Date.now() - t.startTime + t.elapsedTime;
    const minutes = Math.floor(timePassed / 60000).toString().padStart(2, '0');
    const seconds = Math.floor((timePassed % 60000) / 1000).toString().padStart(2, '0');
    const ms = Math.floor((timePassed % 1000) / 10).toString().padStart(2, '0');
    document.getElementById(t.timeEl).textContent = `${minutes}:${seconds}.${ms}`;
}

function setStatus(trackKey, status) {
    const t = displayTracks[trackKey];
    const el = document.getElementById(t.statusEl);
    const timeEl = document.getElementById(t.timeEl);

    el.className = 'display-status';
    timeEl.className = 'display-stopwatch';

    switch (status) {
        case 'running':
            el.classList.add('running');
            el.textContent = '● RUNNING';
            timeEl.classList.add('running');
            break;
        case 'finished':
            el.classList.add('finished');
            el.textContent = 'FINISHED';
            timeEl.classList.add('stopped');
            break;
        default:
            el.classList.add('waiting');
            el.textContent = 'READY';
            break;
    }
}

async function checkDisplayStates() {
    try {
        const response = await fetch('/api/state/');
        const data = await response.json();

        for (const key of ['track1', 'track2']) {
            const t = displayTracks[key];
            const serverState = data[key];

            if (serverState === 'start' && t.lastState !== 'start') {
                // Reset timer on fresh start
                t.elapsedTime = 0;
                t.hasStopped = false;
                document.getElementById(t.timeEl).textContent = '00:00.00';
                t.hasEverStarted = true;
                t.startTime = Date.now();
                if (t.interval) clearInterval(t.interval);
                t.interval = setInterval(() => updateDisplayTime(key), 10);
                setStatus(key, 'running');
                t.lastState = 'start';
            } else if (serverState === 'stop' && t.lastState === 'start') {
                if (t.interval) {
                    clearInterval(t.interval);
                    t.interval = null;
                    t.elapsedTime += Date.now() - t.startTime;
                }
                t.hasStopped = true;
                setStatus(key, 'finished');
                t.lastState = 'stop';
            } else if (serverState === 'reset') {
                // Judge submitted — reset everything back to zero
                if (t.interval) {
                    clearInterval(t.interval);
                    t.interval = null;
                }
                t.elapsedTime = 0;
                t.startTime = 0;
                t.hasEverStarted = false;
                t.hasStopped = false;
                document.getElementById(t.timeEl).textContent = '00:00.00';
                setStatus(key, 'waiting');
                t.lastState = 'reset';
            }
        }
    } catch (err) {
        // Silently retry
    }
}

// ============================================================
// ACTIVE RUN INFO — Team details on display
// ============================================================
async function fetchActiveRunDisplay() {
    try {
        const response = await fetch('/api/active-run/');
        const data = await response.json();

        for (const run of data.active_runs) {
            const prefix = run.track === 'A' ? 'display-a' : 'display-b';

            if (run.team_name) {
                document.getElementById(`${prefix}-team-num`).textContent = '';
                document.getElementById(`${prefix}-team-name`).textContent = run.team_name;

                // Show round/try info
                const roundLabel = run.round_type === 'round1' ? 'Qualification Stage' : 'Finals';
                const tryLabel = run.try_number === 'try1' ? 'Try 1' : 'Try 2';
                document.getElementById(`${prefix}-round`).textContent = `${roundLabel} — ${tryLabel}`;

                // Fetch rank from leaderboard
                fetchRankForTeam(run.team_id, run.round_type, prefix);
            } else {
                document.getElementById(`${prefix}-team-num`).textContent = '—';
                document.getElementById(`${prefix}-team-name`).textContent = 'Waiting for team...';
                document.getElementById(`${prefix}-round`).textContent = '—';
                document.getElementById(`${prefix}-rank`).textContent = '';
            }
        }
    } catch (err) { /* ignore */ }
}

async function fetchRankForTeam(teamId, roundType, prefix) {
    try {
        const response = await fetch('/api/leaderboard/');
        const data = await response.json();
        const list = roundType === 'round1' ? data.round1 : data.round2;
        const bestKey = roundType === 'round1' ? 'round1_best' : 'round2_best';

        // Sort by best time to find rank
        list.sort((a, b) => a[bestKey] - b[bestKey]);
        const rank = list.findIndex(t => t.team_id === teamId) + 1;

        const rankEl = document.getElementById(`${prefix}-rank`);
        if (rank > 0) {
            rankEl.innerHTML = `Current Rank: <span>${rank}</span> / ${list.length}`;
        } else {
            rankEl.innerHTML = `Current Rank: <span>—</span>`;
        }
    } catch (err) { /* ignore */ }
}

// ============================================================
// INIT
// ============================================================
fetchActiveRunDisplay();

// Check stopwatch state every 100ms (fast for responsiveness)
setInterval(checkDisplayStates, 100);

// Refresh active run info every 3 seconds
setInterval(fetchActiveRunDisplay, 3000);
