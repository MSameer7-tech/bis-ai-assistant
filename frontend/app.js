/**
 * BIS AI Assistant - Frontend Client Logic
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
    const temporalBadge = document.getElementById('temporalBadge');
    const confidenceVal = document.getElementById('confidenceVal');
    const answerText = document.getElementById('answerText');
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

        catalogCount.textContent = `${filtered.length} Standards`;
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
        btnText.textContent = 'Analyzing...';
        btnSpinner.classList.remove('hidden');

        try {
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: q,
                    as_of_date: asOf,
                    top_k: topK
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
            btnText.textContent = 'Query Standard';
            btnSpinner.classList.add('hidden');
        }
    }

    queryForm.addEventListener('submit', (e) => {
        e.preventDefault();
        handleQuerySubmit();
    });

    // 4. Render Results
    function renderResults(data) {
        resultsCard.classList.remove('hidden');
        resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Confidence & Status
        confidenceVal.textContent = data.confidence !== undefined ? data.confidence.toFixed(2) : '1.0';
        temporalBadge.textContent = data.temporal_context || 'Current Effective Edition';

        const gRes = data.guardrail_result || {};
        if (gRes.passed) {
            groundingBadge.className = 'badge-success';
            groundingBadge.textContent = '✅ Grounded & Verified';
        } else {
            groundingBadge.className = 'badge-warning';
            groundingBadge.textContent = '⚠️ Guardrail Abstention / Out of Scope';
        }

        // Format Answer
        answerText.innerHTML = formatMarkdown(data.answer);

        // Citations
        citationsList.innerHTML = '';
        if (data.citations && data.citations.length > 0) {
            data.citations.forEach(c => {
                const card = document.createElement('div');
                card.className = 'citation-card';
                card.innerHTML = `
                    <div class="citation-header">
                        <span>${c.standard_number}</span>
                        <span>${c.verified ? '✅ Verified' : '⚠️ Unverified'}</span>
                    </div>
                    <div class="citation-meta">
                        <span><strong>Clause:</strong> ${c.clause || 'N/A'}</span>
                        <span><strong>Pages:</strong> ${c.pages && c.pages.length ? c.pages.join(', ') : 'N/A'}</span>
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
            `<strong>Grounding Confidence:</strong> ${(gRes.grounding_confidence * 100).toFixed(0)}%`,
            `<strong>Refusal Status:</strong> ${gRes.refusal_required ? 'Triggered' : 'Not Required (Answer Permitted)'}`,
            `<strong>Numerical Claims Checked:</strong> ${gRes.numerical_checks ? gRes.numerical_checks.length : 0} verified against source text`,
            `<strong>Normative Force Checks:</strong> ${gRes.normative_checks ? gRes.normative_checks.length : 0} passed`
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
