/**
 * BIS AI Assistant - Production Frontend Client Logic (Phase 5).
 * Connects to /api/v1/query, /api/v1/chain, /api/v1/timeline, and /api/v1/evidence/stats.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Form Elements
    const queryForm = document.getElementById('queryForm');
    const queryInput = document.getElementById('queryInput');
    const asOfDateSelect = document.getElementById('asOfDateSelect');
    const customDateInput = document.getElementById('customDateInput');
    const topKSelect = document.getElementById('topKSelect');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    const samplesContainer = document.getElementById('samplesContainer');
    
    // Top Bar Stat Elements
    const statEvidence = document.getElementById('statEvidence');
    const statEdges = document.getElementById('statEdges');
    const statProducts = document.getElementById('statProducts');

    // Response Elements
    const resultsCard = document.getElementById('resultsCard');
    const groundingBadge = document.getElementById('groundingBadge');
    const intentBadge = document.getElementById('intentBadge');
    const schemeBadge = document.getElementById('schemeBadge');
    const confidenceVal = document.getElementById('confidenceVal');
    const warningsBanner = document.getElementById('warningsBanner');
    
    const verdictBox = document.getElementById('verdictBox');
    const chainStepper = document.getElementById('chainStepper');
    const answerText = document.getElementById('answerText');
    
    const testsSection = document.getElementById('testsSection');
    const testsTableBody = document.getElementById('testsTableBody');
    
    const timelineSection = document.getElementById('timelineSection');
    const timelineEvents = document.getElementById('timelineEvents');
    
    const citationsList = document.getElementById('citationsList');

    // Catalog Elements
    const standardsList = document.getElementById('standardsList');
    const catalogCount = document.getElementById('catalogCount');
    const catalogSearch = document.getElementById('catalogSearch');
    const domainTabs = document.getElementById('domainTabs');

    let allStandards = [];
    let currentDomain = 'all';

    // 1. Toggle Custom Date Input
    if (asOfDateSelect) {
        asOfDateSelect.addEventListener('change', () => {
            if (asOfDateSelect.value === 'custom') {
                customDateInput.classList.remove('hidden');
            } else {
                customDateInput.classList.add('hidden');
            }
        });
    }

    // 2. Fetch Live Stats
    async function loadStats() {
        try {
            const [evRes, covRes] = await Promise.all([
                fetch('/api/v1/evidence/stats'),
                fetch('/api/v1/coverage/stats')
            ]);
            if (evRes.ok) {
                const data = await evRes.json();
                if (statEvidence) statEvidence.textContent = data.total_evidence_records.toLocaleString();
                if (statEdges) statEdges.textContent = data.total_graph_edges.toLocaleString();
            }
            if (covRes.ok) {
                const covData = await covRes.json();
                const statPSCoverage = document.getElementById('statPSCoverage');
                if (statPSCoverage) {
                    statPSCoverage.textContent = `${covData.overall_ps_coverage_pct}%`;
                }
            }
        } catch (e) {
            console.warn('Could not load live stats:', e);
        }
    }

    // 3. Quick Sample Buttons Listener
    if (samplesContainer) {
        samplesContainer.querySelectorAll('.sample-chip').forEach(btn => {
            btn.addEventListener('click', () => {
                const q = btn.getAttribute('data-q');
                if (q) {
                    queryInput.value = q;
                    if (asOfDateSelect) asOfDateSelect.value = '';
                    if (customDateInput) customDateInput.classList.add('hidden');
                    handleQuerySubmit();
                }
            });
        });
    }

    // 4. Standards Catalog Loader
    async function loadCatalog() {
        try {
            const res = await fetch('/api/standards');
            if (res.ok) {
                allStandards = await res.json();
                renderCatalog();
            }
        } catch (err) {
            if (standardsList) standardsList.innerHTML = `<div class="error">Failed to load catalog.</div>`;
        }
    }

    function renderCatalog() {
        if (!standardsList) return;
        const query = (catalogSearch ? catalogSearch.value : '').toLowerCase().trim();
        const filtered = allStandards.filter(std => {
            const matchDomain = currentDomain === 'all' || std.product_domain === currentDomain;
            const title = (std.title || '').toLowerCase();
            const isNum = (std.standard_number || '').toLowerCase();
            const matchSearch = !query || isNum.includes(query) || title.includes(query);
            return matchDomain && matchSearch;
        });

        if (catalogCount) catalogCount.textContent = `${filtered.length} Standards`;

        if (filtered.length === 0) {
            standardsList.innerHTML = `<div class="empty-state">No matching Indian Standards found.</div>`;
            return;
        }

        standardsList.innerHTML = filtered.slice(0, 50).map(std => `
            <div class="standard-item" data-code="${std.standard_number}">
                <div class="std-header">
                    <span class="std-number">${std.standard_number}</span>
                    <span class="std-badge ${std.mandatory ? 'mandatory' : 'voluntary'}">
                        ${std.mandatory ? 'MANDATORY' : 'VOLUNTARY'}
                    </span>
                </div>
                <div class="std-title">${std.title || 'Indian Standard Specification'}</div>
                <div class="std-footer">
                    <span>${std.product_domain || 'General'}</span>
                    <span>${std.edition || 'Current'}</span>
                </div>
            </div>
        `).join('');

        standardsList.querySelectorAll('.standard-item').forEach(item => {
            item.addEventListener('click', () => {
                const code = item.getAttribute('data-code');
                queryInput.value = `What are the mandatory requirements and compliance tests for ${code}?`;
                handleQuerySubmit();
            });
        });
    }

    if (domainTabs) {
        domainTabs.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                domainTabs.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentDomain = btn.getAttribute('data-domain');
                renderCatalog();
            });
        });
    }

    if (catalogSearch) {
        catalogSearch.addEventListener('input', renderCatalog);
    }

    // 5. Query Submission Handler
    async function handleQuerySubmit() {
        const query = queryInput.value.trim();
        if (!query) return;

        let asOfDate = asOfDateSelect ? asOfDateSelect.value : null;
        if (asOfDate === 'custom' && customDateInput && customDateInput.value) {
            asOfDate = customDateInput.value;
        } else if (!asOfDate || asOfDate === 'custom') {
            asOfDate = null;
        }

        const topK = topKSelect ? parseInt(topKSelect.value, 10) : 5;

        // UI Loading State
        submitBtn.disabled = true;
        btnText.textContent = 'Analyzing Regulatory Corpus...';
        btnSpinner.classList.remove('hidden');

        try {
            const res = await fetch('/api/v1/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, as_of_date: asOfDate, top_k: topK })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'API execution failed');
            }

            const data = await res.json();
            renderResponse(data);

        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            submitBtn.disabled = false;
            btnText.textContent = 'Execute Intelligence Query';
            btnSpinner.classList.add('hidden');
        }
    }

    if (queryForm) {
        queryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleQuerySubmit();
        });
    }

    // 6. Response Renderer
    function renderResponse(data) {
        resultsCard.classList.remove('hidden');
        resultsCard.scrollIntoView({ behavior: 'smooth' });

        // Status & Confidence
        if (groundingBadge) {
            groundingBadge.textContent = data.status === 'VERIFIED' ? '🟢 VERIFIED' : (data.status === 'REFUSAL' ? '🔴 REFUSAL' : '🟡 ' + data.status);
            groundingBadge.className = data.status === 'VERIFIED' ? 'badge-success' : (data.status === 'REFUSAL' ? 'badge-danger' : 'badge-warning');
        }

        if (intentBadge && data.parsed_query) {
            intentBadge.textContent = (data.parsed_query.intents || ['GENERAL_KYS']).join(' + ');
        }

        if (schemeBadge && data.verdict) {
            schemeBadge.textContent = data.verdict.scheme || 'SCHEME-I';
        }

        if (confidenceVal) {
            confidenceVal.textContent = (data.confidence || 0.95).toFixed(2);
        }

        // Warnings
        if (warningsBanner) {
            if (data.warnings && data.warnings.length > 0) {
                warningsBanner.innerHTML = data.warnings.map(w => `<div>${w}</div>`).join('');
                warningsBanner.classList.remove('hidden');
            } else {
                warningsBanner.classList.add('hidden');
            }
        }

        // Executive Verdict Box
        if (verdictBox && data.verdict) {
            const v = data.verdict;
            const mandClass = v.is_mandatory ? 'mandatory' : 'voluntary';
            const mandText = v.is_mandatory ? 'MANDATORY (QCO Enforced)' : 'VOLUNTARY';
            
            verdictBox.innerHTML = `
                <h3>🏛️ BIS Executive Verdict: <span class="${mandClass}">${mandText}</span></h3>
                <div class="verdict-grid">
                    <div class="verdict-item">
                        <div class="label">Governed Commodity</div>
                        <div class="value">${v.product || 'Indian Standard Scope'}</div>
                    </div>
                    <div class="verdict-item">
                        <div class="label">Indian Standard</div>
                        <div class="value">${v.standard || 'IS Standard'}</div>
                    </div>
                    <div class="verdict-item">
                        <div class="label">Conformity Scheme</div>
                        <div class="value">${v.scheme || 'SCHEME-I'}</div>
                    </div>
                    <div class="verdict-item">
                        <div class="label">Chain Completeness</div>
                        <div class="value">${v.chain_status || 'COMPLETE'}</div>
                    </div>
                </div>
            `;
        }

        // Certification Chain Stepper
        if (chainStepper) {
            if (data.certification_chain && data.certification_chain.nodes) {
                const nodes = data.certification_chain.nodes;
                chainStepper.innerHTML = nodes.map((n, idx) => `
                    <div class="chain-node ${n.is_present ? 'verified' : 'missing'}">
                        <div class="chain-node-type">${n.node_type}</div>
                        <div class="chain-node-title" title="${n.title}">${n.title}</div>
                    </div>
                    ${idx < nodes.length - 1 ? '<span class="chain-arrow">──►</span>' : ''}
                `).join('');
            } else {
                chainStepper.innerHTML = `<span class="text-muted">No explicit multi-hop certification chain resolved.</span>`;
            }
        }

        // Detailed Markdown Explanation
        if (answerText) {
            answerText.innerHTML = renderMarkdown(data.answer_markdown || '');
        }

        // Normative Compliance Tests Table
        if (testsSection && testsTableBody) {
            if (data.test_requirements && data.test_requirements.length > 0) {
                testsSection.classList.remove('hidden');
                testsTableBody.innerHTML = data.test_requirements.map(t => `
                    <tr>
                        <td><strong>${t.test_name}</strong></td>
                        <td>${t.requirement}</td>
                        <td><code>${t.test_method}</code></td>
                        <td>${t.clause_page}</td>
                    </tr>
                `).join('');
            } else {
                testsSection.classList.add('hidden');
            }
        }

        // Regulatory Timeline Milestones
        if (timelineSection && timelineEvents) {
            if (data.timeline && data.timeline.events && data.timeline.events.length > 0) {
                timelineSection.classList.remove('hidden');
                timelineEvents.innerHTML = data.timeline.events.slice(0, 8).map(e => `
                    <div class="timeline-item">
                        <div class="timeline-header">
                            <span>${e.date}</span>
                            <span>${e.event_type}</span>
                        </div>
                        <div class="timeline-title">${e.title}</div>
                        <div class="text-muted" style="font-size:0.75rem;">${e.description}</div>
                    </div>
                `).join('');
            } else {
                timelineSection.classList.add('hidden');
            }
        }

        // Citations & Provenance Ledger
        if (citationsList) {
            if (data.evidence_records && data.evidence_records.length > 0) {
                citationsList.innerHTML = data.evidence_records.map(ev => `
                    <div class="citation-card">
                        <div class="cit-header">
                            <span class="cit-authority">${ev.source_authority || 'BIS'}</span>
                            <span class="cit-badge">${ev.evidentiary_strength || 'VERIFIED'}</span>
                        </div>
                        <div class="cit-title">${ev.citation_title || 'Indian Standard Specification'}</div>
                        <div class="cit-meta">
                            <span>Locator: <code>${ev.locator_value || 'Clause 1'}</code></span>
                            <span>Clause: ${ev.clause_number || 'Scope'}</span>
                            <span>Page: ${ev.page_number || 1}</span>
                        </div>
                        <div class="cit-hash">
                            SHA-256: <code>${ev.document_sha256 ? ev.document_sha256.substring(0, 20) + '...' : 'Registry-Indexed'}</code>
                        </div>
                    </div>
                `).join('');
            } else {
                citationsList.innerHTML = `<span class="text-muted">No explicit evidence records attached.</span>`;
            }
        }
    }

    // Lightweight Markdown Parser
    function renderMarkdown(md) {
        if (!md) return '';
        return md
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/gim, '<em>$1</em>')
            .replace(/`([^`]+)`/gim, '<code>$1</code>')
            .replace(/\n\n/gim, '<br><br>')
            .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');
    }

    // Initialize
    loadStats();
    loadCatalog();
});
