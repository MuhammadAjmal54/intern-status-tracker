/* ─────────────────────────────────────────────────
   Configuration
   ───────────────────────────────────────────────── */
const API_BASE = '/api';

/* ─────────────────────────────────────────────────
   State
   ───────────────────────────────────────────────── */
// name lookup: candidateId -> full_name
let candidateMap = {};

/* ─────────────────────────────────────────────────
   Init
   ───────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('dashboard-date').value = today;
    document.getElementById('status-date').value = today;

    loadDashboard();
    loadCandidates();
    loadStatuses();
});

/* ─────────────────────────────────────────────────
   Tab Navigation
   ───────────────────────────────────────────────── */
function showTab(tabId) {
    document.querySelectorAll('.tab-panel').forEach(p => {
        p.classList.remove('active');
        p.classList.add('hidden');
    });
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    const panel = document.getElementById(tabId);
    panel.classList.remove('hidden');
    panel.classList.add('active');

    // Find the button that targets this tab
    document.querySelectorAll('.tab-btn').forEach(b => {
        if (b.getAttribute('onclick')?.includes(tabId)) b.classList.add('active');
    });
}

/* ─────────────────────────────────────────────────
   Alert
   ───────────────────────────────────────────────── */
function showAlert(message, isError = false) {
    const banner = document.getElementById('alert-banner');
    banner.textContent = message;
    banner.className = `alert ${isError ? 'error' : 'success'}`;
    banner.classList.remove('hidden');
    clearTimeout(banner._timer);
    banner._timer = setTimeout(() => banner.classList.add('hidden'), 5000);
}

/* ─────────────────────────────────────────────────
   Loading helpers
   ───────────────────────────────────────────────── */
function showLoading(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('hidden');
}
function hideLoading(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}

/* ─────────────────────────────────────────────────
   API helpers
   ───────────────────────────────────────────────── */
async function apiFetch(url, options = {}) {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
    }
    return res.json();
}

/* ═══════════════════════════════════════════════════════════
   DASHBOARD
   ═══════════════════════════════════════════════════════════ */
async function loadDashboard() {
    const dateVal = document.getElementById('dashboard-date').value;

    // Show spinners (white — card backgrounds are now colored)
    ['metric-active','metric-submitted','metric-missing','metric-avg'].forEach(id => {
        document.getElementById(id).innerHTML = '<span class="spinner-sm"></span>';
    });
    document.getElementById('submitted-list').innerHTML =
        '<div class="loading-placeholder"><span class="spinner-sm"></span> Loading…</div>';
    document.getElementById('missing-list').innerHTML =
        '<div class="loading-placeholder"><span class="spinner-sm"></span> Loading…</div>';

    try {
        const data = await apiFetch(
            `${API_BASE}/dashboard/summary?date=${dateVal}`
        );

        document.getElementById('metric-active').textContent    = data.total_active_candidates;
        document.getElementById('metric-submitted').textContent = data.submitted_count;
        document.getElementById('metric-missing').textContent   = data.missing_count;
        document.getElementById('metric-avg').textContent       = `${data.average_completion_percentage}%`;

        // Submitted candidates list
        const submittedEl = document.getElementById('submitted-list');
        if (data.submitted_candidates.length === 0) {
            submittedEl.innerHTML = '<p class="empty-row">No submissions yet.</p>';
        } else {
            submittedEl.innerHTML = data.submitted_candidates
                .map(c => {
                    // Find completion for this date from submitted statuses
                    const ls = c.latest_status;
                    const pct = ls ? ls.completion_percentage : 0;
                    const pctClass = pct >= 80 ? 'high' : pct >= 40 ? 'medium' : 'low';
                    return `
                        <div class="cand-card">
                            <span class="cand-card-pct">${pct}%</span>
                            <div class="cand-card-name">${escHtml(c.full_name)}</div>
                            <div class="cand-card-meta">${escHtml(c.training_track)} · ${escHtml(c.email)}</div>
                        </div>`;
                })
                .join('');
        }

        // Missing candidates list
        const missingEl = document.getElementById('missing-list');
        if (data.missing_candidates.length === 0) {
            missingEl.innerHTML = '<p class="empty-row" style="color:var(--success)">🎉 All candidates submitted!</p>';
        } else {
            missingEl.innerHTML = data.missing_candidates
                .map(c => `
                    <div class="cand-card missing">
                        <div class="cand-card-name">${escHtml(c.full_name)}</div>
                        <div class="cand-card-meta">${escHtml(c.training_track)} · ${escHtml(c.email)}</div>
                    </div>`)
                .join('');
        }
    } catch (err) {
        showAlert('Failed to load dashboard data: ' + err.message, true);
        document.getElementById('submitted-list').innerHTML = '';
        document.getElementById('missing-list').innerHTML = '';
    }
}

/* ═══════════════════════════════════════════════════════════
   CANDIDATES
   ═══════════════════════════════════════════════════════════ */
async function loadCandidates() {
    showLoading('candidates-loading');

    const isActive = document.getElementById('filter-active').value;
    let url = `${API_BASE}/candidates?limit=500`;
    if (isActive !== '') url += `&is_active=${isActive}`;

    try {
        const candidates = await apiFetch(url);

        // Build lookup map
        candidateMap = {};
        candidates.forEach(c => { candidateMap[c.id] = c.full_name; });

        // Populate candidate table
        const tbody = document.getElementById('candidates-list');
        if (candidates.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-row">No candidates found.</td></tr>';
        } else {
            tbody.innerHTML = candidates.map(c => `
                <tr>
                    <td>${c.id}</td>
                    <td><strong>${escHtml(c.full_name)}</strong></td>
                    <td>${escHtml(c.email)}</td>
                    <td>${escHtml(c.training_track)}</td>
                    <td><span class="badge ${c.is_active ? 'badge-active' : 'badge-inactive'}">${c.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td>${formatDate(c.created_at)}</td>
                    <td>
                        <button class="btn-sm btn-secondary" onclick='editCandidate(${JSON.stringify(c)})'>Edit</button>
                        <button class="btn-sm btn-danger" onclick="deleteCandidate(${c.id})">Delete</button>
                    </td>
                </tr>`).join('');
        }

        // Populate dropdowns
        const statusSelect   = document.getElementById('status-candidate');
        const filterSelect   = document.getElementById('filter-candidate');
        const currentStatus  = statusSelect.value;
        const currentFilter  = filterSelect.value;

        statusSelect.innerHTML = '<option value="">-- Select Candidate --</option>';
        filterSelect.innerHTML = '<option value="">All Candidates</option>';

        candidates.forEach(c => {
            if (c.is_active) {
                statusSelect.innerHTML += `<option value="${c.id}">${escHtml(c.full_name)}</option>`;
            }
            filterSelect.innerHTML += `<option value="${c.id}">${escHtml(c.full_name)}</option>`;
        });

        // Restore previous selections
        if (currentStatus) statusSelect.value = currentStatus;
        if (currentFilter) filterSelect.value = currentFilter;

    } catch (err) {
        showAlert('Failed to load candidates: ' + err.message, true);
    } finally {
        hideLoading('candidates-loading');
    }
}

async function handleCandidateSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('candidate-id').value;
    const body = {
        full_name:      document.getElementById('cand-name').value.trim(),
        email:          document.getElementById('cand-email').value.trim(),
        training_track: document.getElementById('cand-track').value.trim(),
        is_active:      document.getElementById('cand-active').checked,
    };

    // Client-side validation
    if (!body.full_name || !body.email || !body.training_track) {
        showAlert('Please fill in all required fields.', true);
        return;
    }

    const url    = id ? `${API_BASE}/candidates/${id}` : `${API_BASE}/candidates`;
    const method = id ? 'PUT' : 'POST';

    try {
        await apiFetch(url, { method, body: JSON.stringify(body) });
        showAlert(id ? 'Candidate updated successfully ✓' : 'Candidate added successfully ✓');
        resetCandidateForm();
        loadCandidates();
        loadDashboard();
    } catch (err) {
        showAlert(err.message, true);
    }
}

function editCandidate(c) {
    document.getElementById('candidate-id').value   = c.id;
    document.getElementById('cand-name').value      = c.full_name;
    document.getElementById('cand-email').value     = c.email;
    document.getElementById('cand-track').value     = c.training_track;
    document.getElementById('cand-active').checked  = c.is_active;

    document.getElementById('cand-form-title').textContent = 'Edit Candidate';
    document.getElementById('cand-btn').textContent        = 'Update Candidate';
    document.getElementById('cand-cancel').classList.remove('hidden');

    // Scroll to form
    document.getElementById('candidate-form').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function resetCandidateForm() {
    document.getElementById('candidate-id').value          = '';
    document.getElementById('candidate-form').reset();
    document.getElementById('cand-active').checked         = true;
    document.getElementById('cand-form-title').textContent = 'Add New Candidate';
    document.getElementById('cand-btn').textContent        = 'Add Candidate';
    document.getElementById('cand-cancel').classList.add('hidden');
}

async function deleteCandidate(id) {
    const name = candidateMap[id] || `ID ${id}`;
    if (!confirm(`Delete candidate "${name}"?\n\nThis will also delete all their status records.`)) return;
    try {
        await apiFetch(`${API_BASE}/candidates/${id}`, { method: 'DELETE' });
        showAlert('Candidate deleted.');
        loadCandidates();
        loadDashboard();
        loadStatuses();
    } catch (err) {
        showAlert(err.message, true);
    }
}

/* ═══════════════════════════════════════════════════════════
   DAILY STATUS
   ═══════════════════════════════════════════════════════════ */
async function loadStatuses() {
    showLoading('statuses-loading');

    const candidateId = document.getElementById('filter-candidate').value;
    const dateFrom    = document.getElementById('filter-date-from').value;
    const dateTo      = document.getElementById('filter-date-to').value;

    const params = new URLSearchParams({ limit: '500' });
    if (candidateId) params.append('candidate_id', candidateId);
    if (dateFrom)    params.append('date_from', dateFrom);
    if (dateTo)      params.append('date_to', dateTo);

    try {
        const statuses = await apiFetch(`${API_BASE}/statuses?${params}`);
        const tbody = document.getElementById('statuses-list');

        if (statuses.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="empty-row">No status records found.</td></tr>';
        } else {
            tbody.innerHTML = statuses.map(s => {
                const pct      = s.completion_percentage;
                const pctClass = pct >= 80 ? 'high' : pct >= 40 ? 'medium' : 'low';
                const name     = escHtml(candidateMap[s.candidate_id] || `#${s.candidate_id}`);
                return `
                <tr>
                    <td>${name}</td>
                    <td style="white-space:nowrap">${s.status_date}</td>
                    <td><div class="text-truncate" title="${escHtml(s.work_completed)}">${escHtml(s.work_completed)}</div></td>
                    <td><div class="text-truncate" title="${escHtml(s.topics_learned)}">${escHtml(s.topics_learned)}</div></td>
                    <td><div class="text-truncate" title="${escHtml(s.blockers || '')}">${s.blockers ? escHtml(s.blockers) : '<span style="color:var(--text-muted)">—</span>'}</div></td>
                    <td><div class="text-truncate" title="${escHtml(s.next_day_plan)}">${escHtml(s.next_day_plan)}</div></td>
                    <td>
                        <div class="pct-bar-wrap">
                            <div class="pct-bar"><div class="pct-fill ${pctClass}" style="width:${pct}%"></div></div>
                            <span>${pct}%</span>
                        </div>
                    </td>
                    <td>
                        <button class="btn-sm btn-secondary" onclick='editStatus(${JSON.stringify(s)})'>Edit</button>
                        <button class="btn-sm btn-danger" onclick="deleteStatus(${s.id})">Delete</button>
                    </td>
                </tr>`;
            }).join('');
        }
    } catch (err) {
        showAlert('Failed to load statuses: ' + err.message, true);
    } finally {
        hideLoading('statuses-loading');
    }
}

async function handleStatusSubmit(e) {
    e.preventDefault();
    const id          = document.getElementById('status-id').value;
    const candidateId = parseInt(document.getElementById('status-candidate').value);

    // Client-side validation
    if (!candidateId) {
        showAlert('Please select a candidate.', true);
        return;
    }

    const body = {
        candidate_id:          candidateId,
        status_date:           document.getElementById('status-date').value,
        work_completed:        document.getElementById('status-work').value.trim(),
        topics_learned:        document.getElementById('status-topics').value.trim(),
        blockers:              document.getElementById('status-blockers').value.trim() || null,
        next_day_plan:         document.getElementById('status-plan').value.trim(),
        completion_percentage: parseInt(document.getElementById('status-completion').value),
    };

    if (!body.status_date) { showAlert('Please select a date.', true); return; }
    if (!body.work_completed) { showAlert('Work Completed is required.', true); return; }
    if (!body.topics_learned) { showAlert('Topics Learned is required.', true); return; }
    if (!body.next_day_plan)  { showAlert('Next Day Plan is required.', true); return; }
    if (isNaN(body.completion_percentage) || body.completion_percentage < 0 || body.completion_percentage > 100) {
        showAlert('Completion % must be between 0 and 100.', true);
        return;
    }

    const url    = id ? `${API_BASE}/statuses/${id}` : `${API_BASE}/statuses`;
    const method = id ? 'PUT' : 'POST';

    try {
        await apiFetch(url, { method, body: JSON.stringify(body) });
        showAlert(id ? 'Status updated successfully ✓' : 'Status submitted successfully ✓');
        resetStatusForm();
        loadStatuses();
        loadDashboard();
    } catch (err) {
        showAlert(err.message, true);
    }
}

function editStatus(s) {
    document.getElementById('status-id').value             = s.id;
    document.getElementById('status-candidate').value      = s.candidate_id;
    document.getElementById('status-date').value           = s.status_date;
    document.getElementById('status-completion').value     = s.completion_percentage;
    document.getElementById('status-work').value           = s.work_completed;
    document.getElementById('status-topics').value         = s.topics_learned;
    document.getElementById('status-blockers').value       = s.blockers || '';
    document.getElementById('status-plan').value           = s.next_day_plan;

    document.getElementById('status-form-title').textContent = 'Edit Daily Status';
    document.getElementById('status-btn').textContent        = 'Update Status';
    document.getElementById('status-cancel').classList.remove('hidden');

    // Switch to Status tab and scroll to form
    showTab('tab-status');
    document.getElementById('status-form').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function resetStatusForm() {
    document.getElementById('status-id').value                = '';
    document.getElementById('status-form').reset();
    document.getElementById('status-date').value              = new Date().toISOString().split('T')[0];
    document.getElementById('status-form-title').textContent  = 'Submit Daily Status';
    document.getElementById('status-btn').textContent         = 'Submit Status';
    document.getElementById('status-cancel').classList.add('hidden');
}

function clearStatusFilters() {
    document.getElementById('filter-candidate').value  = '';
    document.getElementById('filter-date-from').value  = '';
    document.getElementById('filter-date-to').value    = '';
    loadStatuses();
}

async function deleteStatus(id) {
    if (!confirm('Delete this status entry? This cannot be undone.')) return;
    try {
        await apiFetch(`${API_BASE}/statuses/${id}`, { method: 'DELETE' });
        showAlert('Status entry deleted.');
        loadStatuses();
        loadDashboard();
    } catch (err) {
        showAlert(err.message, true);
    }
}

/* ─────────────────────────────────────────────────
   Utilities
   ───────────────────────────────────────────────── */
function escHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function formatDate(isoStr) {
    if (!isoStr) return '';
    try {
        return new Date(isoStr).toLocaleDateString(undefined, {
            year: 'numeric', month: 'short', day: 'numeric',
        });
    } catch { return isoStr; }
}