// Client-side interactions for Enterprise Document Intelligence Agent
document.addEventListener("DOMContentLoaded", () => {
  const btnAnalyze = document.getElementById("btn-analyze");
  const btnClear = document.getElementById("btn-clear");
  const btnSampleSdd = document.getElementById("btn-sample-sdd");
  const btnSampleContract = document.getElementById("btn-sample-contract");
  const docInput = document.getElementById("document-input");
  const docTypeSelect = document.getElementById("doc-type-select");
  const modelSelect = document.getElementById("model-select");
  const spinner = document.getElementById("spinner");
  const emptyState = document.getElementById("empty-state");
  const resultsContainer = document.getElementById("results-container");
  const badgeCache = document.getElementById("badge-cache");

  // Sample Documents
  const SAMPLE_SDD = `SOLUTION DESIGN DOCUMENT: SUBSEA PIPELINE TELEMETRY AUTOMATION
Document Ref: NNPC-ENG-SDD-OML119-004
Operating Asset: OML 119 Deepwater Field
Owner: NNPC RTI Directorate & NEPL-NAPIMS Joint Venture
Total Project Budget: $4,500,000.00 USD

1. Executive Scope & Objective
This specification outlines the real-time SCADA and IoT sensor ingestion framework for 3 offshore production manifolds at OML 119. Raw acoustic flow data will be collected, validated, and loaded into the Enterprise Data Warehouse with a maximum turnaround latency SLA of 15 seconds.

2. Architecture & Data Flow
Edge sensor gateways transmit telemetry to an Azure IoT Hub and Managed Redis cluster before downstream star-schema persistence. All API tokens and database credentials must be managed via Azure Key Vault.

3. SLA & Operational Commitments
System availability SLA is 99.9% uptime. Data processing turnaround time must remain under 12 hours for batch variance analysis.

4. Known Risks & Considerations
High security risk: Plaintext credentials must not be passed in telemetry payloads.
Financial reconciliation: Joint venture partners require quarterly cash-call alignment against Capex drawdowns.`;

  const SAMPLE_CONTRACT = `OFFSHORE ENGINEERING & RIG DRILLING SERVICES AGREEMENT
Contract Number: NNPC-CON-2024-8819
Operator: NEPL Operations & Joint Venture Partners
Contractor: ATLANTIC DEEPWATER DRILLING LTD (TIN: 2289410941)
Operating Workstream: OML 38 Western Niger Delta Asset
Total Commercial Value: $18,250,000.00 USD (Fixed Price with Escalation)

Section 4: Payment Terms & Invoicing
4.1 The Operator shall remit payment within NET 30 days of receiving a verified Tax Invoice.
4.2 Value Added Tax (VAT) of 7.5% and Withholding Tax (WHT) of 5.0% for offshore technical services shall be withheld at source.
4.3 Contractor guarantees an equipment operational uptime SLA of 98.5% across the 180-day exploration campaign.

Section 9: HSE & Environmental Governance
Contractor must adhere to Nigerian Upstream Petroleum Regulatory Commission (NUPRC) guidelines for produced-water disposal and environmental post-clean-up inspections. Failure to report leaks within 2 hours incurs a mandatory Level 1 Critical Non-Compliance penalty.`;

  btnSampleSdd.addEventListener("click", () => {
    docInput.value = SAMPLE_SDD;
    docTypeSelect.value = "SOLUTION_DESIGN_DOCUMENT";
  });

  btnSampleContract.addEventListener("click", () => {
    docInput.value = SAMPLE_CONTRACT;
    docTypeSelect.value = "VENDOR_CONTRACT";
  });

  btnClear.addEventListener("click", () => {
    docInput.value = "";
    emptyState.style.display = "flex";
    resultsContainer.style.display = "none";
    badgeCache.style.display = "none";
  });

  btnAnalyze.addEventListener("click", async () => {
    const text = docInput.value.trim();
    if (!text) {
      alert("Please enter or paste document content to analyze.");
      return;
    }

    // Set loading state
    spinner.style.display = "inline-block";
    btnAnalyze.disabled = true;

    try {
      const response = await fetch("/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_text: text,
          document_type: docTypeSelect.value,
          model_name: modelSelect.value,
          temperature: 0.1,
          use_cache: true
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const data = await response.json();
      renderResults(data);
    } catch (err) {
      alert(`Extraction failed: ${err.message}`);
    } finally {
      spinner.style.display = "none";
      btnAnalyze.disabled = false;
    }
  });

  function renderResults(data) {
    emptyState.style.display = "none";
    resultsContainer.style.display = "block";

    // Verdict & Score
    const verdictValue = document.getElementById("verdict-value");
    verdictValue.textContent = data.governance_verdict.replace(/_/g, " ");
    verdictValue.style.color = data.governance_verdict === "APPROVED" ? "var(--status-success)" : "var(--status-warning)";
    document.getElementById("completeness-score").textContent = `${data.completeness_score}%`;

    // Cache badge
    const isCached = data.processing_metadata && data.processing_metadata.cache_hit === "True";
    badgeCache.style.display = isCached ? "block" : "none";

    // Title & Summary
    document.getElementById("res-doc-title").textContent = data.document_title;
    document.getElementById("res-doc-summary").textContent = data.summary;

    // Entities
    const entityGrid = document.getElementById("entity-grid");
    entityGrid.innerHTML = "";
    data.extracted_entities.forEach(entity => {
      const card = document.createElement("div");
      card.className = "entity-card";
      card.innerHTML = `
        <div class="entity-name">${escapeHtml(entity.name)}</div>
        <div class="entity-value">${escapeHtml(entity.value)}</div>
        <div class="entity-conf">Confidence: ${(entity.confidence * 100).toFixed(0)}%</div>
      `;
      entityGrid.appendChild(card);
    });

    // Risks
    const riskList = document.getElementById("risk-list");
    riskList.innerHTML = "";
    data.identified_risks.forEach(risk => {
      const item = document.createElement("div");
      item.className = `risk-item ${risk.risk_level}`;
      item.innerHTML = `
        <div class="risk-header">
          <span class="risk-category">${escapeHtml(risk.category)}</span>
          <span class="risk-badge">${escapeHtml(risk.risk_level)}</span>
        </div>
        <div class="risk-desc">${escapeHtml(risk.description)}</div>
        <div class="risk-mitigation">Mitigation: ${escapeHtml(risk.mitigation_recommendation)}</div>
      `;
      riskList.appendChild(item);
    });

    // Actions
    const actionList = document.getElementById("action-list");
    actionList.innerHTML = "";
    data.key_action_items.forEach(action => {
      const li = document.createElement("li");
      li.textContent = action;
      actionList.appendChild(li);
    });

    // Footer Metadata
    document.getElementById("meta-engine").textContent = `Engine: ${data.processing_metadata?.inference_mode || "Local AI"}`;
    document.getElementById("meta-latency").textContent = `Latency: ${data.processing_metadata?.latency_seconds || "0.0"}s`;
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
});
