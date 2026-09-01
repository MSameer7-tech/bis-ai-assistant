/**
 * BIS AI Assistant - Production Frontend Client Logic (Phase 7)
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const queryForm = document.getElementById('queryForm');
    const queryInput = document.getElementById('queryInput');
    const asOfDateSelect = document.getElementById('asOfDateSelect');
    const customDateInput = document.getElementById('customDateInput');
    const topKSelect = document.getElementById('topKSelect');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    const samplesContainer = document.getElementById('samplesContainer');
    
    // Results Elements
    const resultsCard = document.getElementById('resultsCard');
    const groundingBadge = document.getElementById('groundingBadge');
    const intentBadge = document.getElementById('intentBadge');
    const temporalBadge = document.getElementById('temporalBadge');
    const confidenceVal = document.getElementById('confidenceVal');
    const entityBanner = document.getElementById('entityBanner');
    const entityTitle = document.getElementById('entityTitle');
    const entityMeta = document.getElementById('entityMeta');
    const answerText = document.getElementById('answerText');
    
    const numericalSection = document.getElementById('numericalSection');
    const numericalTableBody = document.getElementById('numericalTableBody');
    
    const claimsSection = document.getElementById('claimsSection');
    const claimsList = document.getElementById('claimsList');

    const citationsList = document.getElementById('citationsList');
    const guardrailDetails = document.getElementById('guardrailDetails');
    const evidenceCount = document.getElementById('evidenceCount');
    const evidenceList = document.getElementById('evidenceList');

    // Catalog Elements
    const standardsList = document.getElementById('standardsList');
    const catalogCount = document.getElementById('catalogCount');
    const catalogSearch = document.getElementById('catalogSearch');
    const domainTabs = document.getElementById('domainTabs');

    let allStandards = [];
    let currentDomain = 'all';
    let currentConversationId = 'session-' + Math.random().toString(36).substring(2, 9);

    // Toggle Custom Date Input
    asOfDateSelect.addEventListener('change', () => {
        if (asOfDateSelect.value === 'custom') {
            customDateInput.classList.remove('hidden');
        } else {
            customDateInput.classList.add('hidden');
        }
    });

    // 1. Load Initial Stats & Samples
    async function loadSamples() {
        try {
            const res = await fetch('/api/samples');
            const samples = await res.json();
            samplesContainer.innerHTML = '';
            samples.forEach(s => {
                const chip = document.createElement('button');
                chip.type = 'button';
                chip.className = 'sample-chip';
                chip.textContent = `${s.category.replace('Table - ', '').replace('Num - ', '').replace('Clause - ', '')}`;
                chip.title = s.query;
                chip.addEventListener('click', () => {
                    queryInput.value = s.query;
                    if (s.as_of_date) {
                        asOfDateSelect.value = s.as_of_date;
                    } else {
                        asOfDateSelect.value = '';
                    }
                    customDateInput.classList.add('hidden');
                    handleQuerySubmit();
                });
                samplesContainer.appendChild(chip);
            });
        } catch (err) {
            console.error('Error loading samples:', err);
        }
    }

    // 2. Load Standards Catalog
    async function loadCatalog() {
        try {
            const res = await fetch('/api/standards');
            allStandards = await res.json();
            renderCatalog();
        } catch (err) {
            standardsList.innerHTML = `<div class="error">Failed to load catalog.</div>`;
        }
    }

    function renderCatalog() {
        const query = catalogSearch.value.toLowerCase().trim();
        const filtered = allStandards.filter(std => {
            const matchDom = currentDomain === 'all' || std.product_domain === currentDomain;
            const matchSearch = !query || 
                (std.standard_number && std.standard_number.toLowerCase().includes(query)) ||
                (std.title && std.title.toLowerCase().includes(query)) ||
                (std.document_id && std.document_id.toLowerCase().includes(query));
            return matchDom && matchSearch;
        });

        catalogCount.textContent = `${filtered.length} Entities`;
        standardsList.innerHTML = '';

        if (filtered.length === 0) {
            standardsList.innerHTML = `<div class="empty" style="color: var(--text-muted); font-size: 0.8rem; padding: 12px;">No matching standards found.</div>`;
            return;
        }

        filtered.forEach(std => {
            const item = document.createElement('div');
            item.className = 'standard-card';
            item.innerHTML = `
                <div class="std-num">${std.standard_number || std.title}</div>
                <div class="std-title">${std.title || 'Official BIS Standard'}</div>
                <div class="std-meta">
                    <span>${std.document_id || ''}</span>
                    <span>${std.product_domain ? std.product_domain.replace('_', ' ') : ''}</span>
                </div>
            `;
            item.addEventListener('click', () => {
                queryInput.value = `What is the scope and requirements of ${std.standard_number || std.title}?`;
                handleQuerySubmit();
            });
            standardsList.appendChild(item);
        });
    }

    // Domain Tab Filtering
    domainTabs.addEventListener('click', (e) => {
        if (e.target.classList.contains('tab-btn')) {
            domainTabs.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            currentDomain = e.target.dataset.domain;
            renderCatalog();
        }
    });

    catalogSearch.addEventListener('input', renderCatalog);

    // 3. Handle Query Submission
    async function handleQuerySubmit() {
        const q = queryInput.value.trim();
        if (!q) return;

        let asOf = asOfDateSelect.value;
        if (asOf === 'custom') {
            asOf = customDateInput.value || null;
        } else if (!asOf) {
            asOf = null;
        }

        const topK = parseInt(topKSelect.value, 10) || 5;

        // UI Loading State
        submitBtn.disabled = true;
        btnText.textContent = 'Verifying...';
        btnSpinner.classList.remove('hidden');

        try {
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: q,
                    as_of_date: asOf,
                    top_k: topK,
                    conversation_id: currentConversationId
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Query execution failed.');
            }

            const data = await res.json();
            renderResults(data);
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            submitBtn.disabled = false;
            btnText.textContent = 'Query Assistant';
            btnSpinner.classList.add('hidden');
        }
    }

    queryForm.addEventListener('submit', (e) => {
        e.preventDefault();
        handleQuerySubmit();
    });

    // 4. Render Production Results
    function renderResults(data) {
        resultsCard.classList.remove('hidden');
        resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

        const payload = data.production_payload || {};

        // Confidence & Status
        const conf = payload.evidence_confidence !== undefined ? payload.evidence_confidence : data.confidence;
        confidenceVal.textContent = conf !== undefined ? Number(conf).toFixed(2) : '1.00';
        temporalBadge.textContent = data.temporal_context || 'Current Enforced Editions';

        // Intent Badge
        if (payload.intent && payload.intent.type) {
            intentBadge.textContent = `Intent: ${payload.intent.type.replace(/_/g, ' ')}`;
        } else {
            intentBadge.textContent = 'Intent: TECHNICAL COMPLIANCE';
        }

        // Grounding status
        const gRes = data.guardrail_result || {};
        if (gRes.passed && payload.status !== 'guardrail_blocked' && payload.status !== 'refusal') {
            groundingBadge.className = 'badge-success';
            groundingBadge.textContent = '✅ Grounded & Verified';
        } else if (payload.status === 'refusal' || gRes.refusal_required) {
            groundingBadge.className = 'badge-warning';
            groundingBadge.textContent = '⚠️ Grounded Refusal / Out of Scope';
        } else {
            groundingBadge.className = 'badge-danger';
            groundingBadge.textContent = '🛑 Guardrail Blocked';
        }

        // Entity Banner
        if (payload.entities && payload.entities.length > 0) {
            const ent = payload.entities[0];
            entityTitle.textContent = ent.name || ent.id;
            entityMeta.textContent = `${ent.domain ? ent.domain.replace(/_/g, ' ').toUpperCase() : 'BIS STANDARD'} • ${ent.mandatory_certification ? 'Compulsory ISI Marking' : 'Voluntary Specification'}`;
            entityBanner.classList.remove('hidden');
        } else {
            entityBanner.classList.add('hidden');
        }

        // Format Answer
        answerText.innerHTML = formatMarkdown(data.answer);

        // Numerical Verification Table
        const numChecks = payload.numerical_verifications || data.numerical_verifications || [];
        if (numChecks.length > 0) {
            numericalTableBody.innerHTML = '';
            numChecks.forEach(nv => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${nv.parameter || 'Parameter'}</strong></td>
                    <td>${nv.claim_value} ${nv.claim_unit}</td>
                    <td>${nv.source_value >= 0 ? `${nv.source_value} ${nv.source_unit}` : 'Not Found in Source'}</td>
                    <td><code>${nv.claim_unit}</code></td>
                    <td>${nv.passed ? '<span class="status-pass">✅ PASSED (0 Delta)</span>' : '<span class="status-fail">❌ FAILED MISMATCH</span>'}</td>
                `;
                numericalTableBody.appendChild(tr);
            });
            numericalSection.classList.remove('hidden');
        } else {
            numericalSection.classList.add('hidden');
        }

        // Atomic Claims Grounding Breakdown
        const claims = payload.claims || data.claims || [];
        if (claims.length > 0) {
            claimsList.innerHTML = '';
            claims.forEach(cl => {
                const div = document.createElement('div');
                div.className = `claim-card ${cl.verified ? 'verified' : 'unverified'}`;
                const evDetails = cl.evidence && cl.evidence.length > 0 
                    ? cl.evidence.map(ev => `<code>${ev.standard_number} Cl. ${ev.clause} (p. ${ev.page || 'N/A'})</code>`).join(' &bull; ')
                    : '<em>No direct chunk entailment</em>';
                
                div.innerHTML = `
                    <div class="claim-header">
                        <span class="claim-id">${cl.claim_id}</span>
                        <span class="claim-status">${cl.verified ? '✅ Verified Entailment' : '⚠️ Low Grounding'}</span>
                    </div>
                    <div class="claim-text">${cl.text}</div>
                    <div class="claim-evidence">Grounding Evidence: ${evDetails}</div>
                `;
                claimsList.appendChild(div);
            });
            claimsSection.classList.remove('hidden');
        } else {
            claimsSection.classList.add('hidden');
        }

        // Citations
        citationsList.innerHTML = '';
        if (data.citations && data.citations.length > 0) {
            data.citations.forEach(c => {
                const card = document.createElement('div');
                card.className = 'citation-card';
                card.innerHTML = `
                    <div class="citation-header">
                        <span>${c.standard_number || c.standard}</span>
                        <span>${c.verified ? '✅ Verified' : '⚠️ Unverified'}</span>
                    </div>
                    <div class="citation-meta">
                        <span><strong>Clause:</strong> ${c.clause || 'N/A'}</span>
                        <span><strong>Pages:</strong> ${c.pages && c.pages.length ? c.pages.join(', ') : (c.page || 'N/A')}</span>
                        <span><strong>Doc ID:</strong> ${c.source_id || c.chunk_id ? c.chunk_id.split('::')[0] : 'DOC'}</span>
                    </div>
                `;
                citationsList.appendChild(card);
            });
        } else {
            citationsList.innerHTML = `<div style="font-size:0.8rem; color:var(--text-muted);">No statutory citations attached for this response.</div>`;
        }

        // Guardrail Box
        guardrailDetails.innerHTML = '';
        const checks = [
            `<strong>Grounding Confidence:</strong> ${(conf * 100).toFixed(0)}%`,
            `<strong>Refusal Status:</strong> ${payload.status === 'refusal' || gRes.refusal_required ? `Triggered (${payload.refusal_reason || 'Out of Scope'})` : 'Not Required (Answer Grounded)'}`,
            `<strong>Deterministic Numerical Verifications:</strong> ${numChecks.length} parameters checked`,
            `<strong>Atomic Claims Verified:</strong> ${claims.filter(c => c.verified).length} / ${claims.length} propositions entailed`
        ];
        if (gRes.violations && gRes.violations.length > 0) {
            checks.push(`<strong style="color: var(--accent-rose);">Violations:</strong> ${gRes.violations.join('; ')}`);
        }
        guardrailDetails.innerHTML = checks.map(c => `<div class="guardrail-item">• ${c}</div>`).join('');

        // Evidence Inspector
        const chunks = data.retrieved_chunks || [];
        evidenceCount.textContent = chunks.length;
        evidenceList.innerHTML = '';
        chunks.forEach((chunk, i) => {
            const item = document.createElement('div');
            item.className = 'evidence-item';
            item.innerHTML = `<strong>[Chunk ${i+1}] ${chunk.standard_number} (Clause ${chunk.clause_number || 'N/A'}, Pages ${chunk.pages ? chunk.pages.join(',') : 'N/A'}) - Score: ${chunk.score ? chunk.score.toFixed(4) : 'N/A'}</strong>\n${chunk.text}`;
            evidenceList.appendChild(item);
        });
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let html = text
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/gim, '<em>$1</em>')
            .replace(/^\- (.*$)/gim, '<li>$1</li>')
            .replace(/\n\n/gim, '<br><br>');
        return html;
    }

    // Init
    loadSamples();
    loadCatalog();
});
