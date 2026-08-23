import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "https://ai-job-matcher-agent.fastapicloud.dev";

const SOURCES = [
  "linkedin",
  "upwork",
  "glints",
  "wellfound",
  "dealls",
  "tech in asia",
  "freelancer",
  "other",
];

const APPLICATION_STATUSES = [
  "SAVED",
  "REVIEWED",
  "APPLIED",
  "RECRUITER_CONTACTED",
  "INTERVIEW",
  "TECHNICAL_TEST",
  "FINAL_INTERVIEW",
  "OFFER",
  "REJECTED",
  "NO_RESPONSE",
  "WITHDRAWN",
];

function App() {
  const [activeTab, setActiveTab] = useState("manual");

  const [infoModal, setInfoModal] = useState(null);

  // ==========================================================
  // MANUAL JOB
  // ==========================================================

  const [form, setForm] = useState({
    source: "linkedin",
    url: "",
    title: "",
    company: "",
    location: "",
    description: "",
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ==========================================================
  // OPPORTUNITIES
  // ==========================================================

  const [opportunities, setOpportunities] = useState([]);
  const [opportunitiesLoading, setOpportunitiesLoading] =
    useState(false);
  const [opportunitiesError, setOpportunitiesError] =
    useState("");

  // ==========================================================
  // APPLY PACKAGE
  // ==========================================================

  const [selectedPackage, setSelectedPackage] = useState(null);
  const [packageLoading, setPackageLoading] = useState(false);
  const [packageError, setPackageError] = useState("");

  // ==========================================================
  // APPLICATION
  // ==========================================================

  const [applicationSaving, setApplicationSaving] =
    useState(false);
  const [applicationMessage, setApplicationMessage] =
    useState("");

  // ==========================================================
  // MY APPLICATIONS
  // ==========================================================

  const [applications, setApplications] = useState([]);
  const [applicationsLoading, setApplicationsLoading] =
    useState(false);
  const [applicationsError, setApplicationsError] =
    useState("");

  const [statusUpdating, setStatusUpdating] = useState(null);

  // ==========================================================
  // HELPERS
  // ==========================================================

  function updateField(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function openOriginalJob(url) {
    if (!url) {
      return;
    }

    window.open(
      url,
      "_blank",
      "noopener,noreferrer"
    );
  }

  // ==========================================================
  // MANUAL JOB ANALYSIS
  // ==========================================================

  async function analyzeJob(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/api/manual-job`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            source: form.source,
            title: form.title,
            company: form.company,
            location: form.location,
            description: form.description,
            url: form.url,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Gagal menganalisis job."
        );
      }

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // ==========================================================
  // LOAD OPPORTUNITIES
  // ==========================================================

  async function loadOpportunities() {
    setOpportunitiesLoading(true);
    setOpportunitiesError("");

    try {
      const response = await fetch(
        `${API_URL}/api/notifications/opportunities`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Gagal mengambil opportunities."
        );
      }

      setOpportunities(
        data.opportunities || []
      );
    } catch (err) {
      setOpportunitiesError(
        err.message
      );
    } finally {
      setOpportunitiesLoading(false);
    }
  }

  // ==========================================================
  // LOAD APPLY PACKAGE
  // ==========================================================

  async function loadApplyPackage(jobId) {
    setPackageLoading(true);
    setPackageError("");
    setApplicationMessage("");
    setSelectedPackage(null);

    try {
      const response = await fetch(
        `${API_URL}/api/opportunities/${jobId}/package`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Gagal mengambil Apply Package"
        );
      }

      setSelectedPackage(
        data.opportunity
      );
    } catch (err) {
      setPackageError(
        err.message
      );
    } finally {
      setPackageLoading(false);
    }
  }

  // ==========================================================
  // MARK AS APPLIED
  // ==========================================================

  async function markAsApplied() {
    if (!selectedPackage) {
      return;
    }

    const finalAction =
      selectedPackage.final_action;

    if (
      finalAction === "SKIP" ||
      finalAction === "DO NOT APPLY"
    ) {
      setApplicationMessage(
        "Job ini tidak boleh ditandai sebagai APPLIED."
      );
      return;
    }

    if (finalAction === "VERIFY BEFORE APPLY") {
      const confirmed = window.confirm(
        "Job ini masih membutuhkan verifikasi. Apakah kamu sudah memverifikasi eligibility dan benar-benar ingin menandainya sebagai APPLIED?"
      );

      if (!confirmed) {
        return;
      }
    }

    setApplicationSaving(true);
    setApplicationMessage("");
    setPackageError("");

    try {
      const response = await fetch(
        `${API_URL}/api/applications`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            job_id:
              selectedPackage.id,

            ai_evaluation_id:
              null,

            application_channel:
              selectedPackage.source ||
              "MANUAL",

            cv_version:
              "v1",

            notes:
              "Marked as applied from Career Copilot",
          }),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Gagal menyimpan application"
        );
      }

      setApplicationMessage(
        `Application berhasil disimpan. ID: ${data.application_id}`
      );

      await loadApplications();

      await loadOpportunities();
    } catch (err) {
      setApplicationMessage(
        `Error: ${err.message}`
      );
    } finally {
      setApplicationSaving(false);
    }
  }

  // ==========================================================
  // LOAD APPLICATIONS
  // ==========================================================

  async function loadApplications() {
    setApplicationsLoading(true);
    setApplicationsError("");

    try {
      const response = await fetch(
        `${API_URL}/api/applications`
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Gagal mengambil applications"
        );
      }

      setApplications(
        data.applications || []
      );
    } catch (err) {
      setApplicationsError(
        err.message
      );
    } finally {
      setApplicationsLoading(false);
    }
  }

  // ==========================================================
  // UPDATE APPLICATION STATUS
  // ==========================================================

  async function updateApplicationStatus(
    applicationId,
    status
  ) {
    setStatusUpdating(
      applicationId
    );

    try {
      const response = await fetch(
        `${API_URL}/api/applications/${applicationId}/status`,
        {
          method: "PATCH",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            status,
            notes:
              `Status updated from Career Copilot UI: ${status}`,
          }),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Gagal mengubah status application"
        );
      }

      await loadApplications();
    } catch (err) {
      setApplicationsError(
        err.message
      );
    } finally {
      setStatusUpdating(null);
    }
  }

  // ==========================================================
  // TAB LOAD
  // ==========================================================

  useEffect(() => {
    if (
      activeTab ===
      "opportunities"
    ) {
      loadOpportunities();
    }

    if (
      activeTab ===
      "applications"
    ) {
      loadApplications();
    }
  }, [activeTab]);

  // ==========================================================
  // SCROLL TO APPLY PACKAGE
  // ==========================================================

  useEffect(() => {
    if (!selectedPackage) {
      return;
    }

    requestAnimationFrame(() => {
      document
        .getElementById("apply-package-panel")
        ?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
    });
  }, [selectedPackage]);

  // ==========================================================
  // RENDER
  // ==========================================================

  const highPriorityCount = opportunities.filter(
    (item) => item.priority === "HIGH"
  ).length;

  const verifyCount = opportunities.filter(
    (item) => item.final_action === "VERIFY BEFORE APPLY"
  ).length;

  return (
    <div className="copilot-app">
      <header className="copilot-topbar">
        <div className="copilot-brand">
          <div className="copilot-brand-mark">AI</div>
          <div>
            <div className="copilot-brand-name">Remote Job Intelligence</div>
            <div className="copilot-brand-subtitle">
              Remote Job Intelligence
            </div>
          </div>
        </div>

        <nav className="copilot-nav" aria-label="Primary">
          <button
            type="button"
            className={activeTab === "manual" ? "copilot-nav-link active" : "copilot-nav-link"}
            onClick={() => {
              setActiveTab("manual");
              setSelectedPackage(null);
              setApplicationMessage("");
            }}
          >
            Analyze
          </button>

          <button
            type="button"
            className={
              activeTab === "opportunities"
                ? "copilot-nav-link active"
                : "copilot-nav-link"
            }
            onClick={() => {
              setActiveTab("opportunities");
              setSelectedPackage(null);
              setApplicationMessage("");
            }}
          >
            Opportunities
            {opportunities.length > 0 && (
              <span className="copilot-nav-count">
                {opportunities.length}
              </span>
            )}
          </button>

          <button
            type="button"
            className={
              activeTab === "applications"
                ? "copilot-nav-link active"
                : "copilot-nav-link"
            }
            onClick={() => {
              setActiveTab("applications");
              setSelectedPackage(null);
              setApplicationMessage("");
            }}
          >
            Applications
            {applications.length > 0 && (
              <span className="copilot-nav-count">
                {applications.length}
              </span>
            )}
          </button>
        </nav>

        <div className="copilot-status">
          <span className="copilot-status-dot" />
          Production online
        </div>
      </header>

      <main className="copilot-main">
        {activeTab === "manual" && (
          <>
            <section className="copilot-hero">
              <div className="copilot-kicker">
                REMOTE JOB INTELLIGENCE
              </div>
              <h1>
                Find the right
                <br />
                remote job
              </h1>
              <p>
                AI researches, verifies and ranks
                <br />
                You decide what to pursue
              </p>

              <div className="copilot-process">
                <span>
                  <strong>01</strong> Match
                </span>
                <span>
                  <strong>02</strong> Verify
                </span>
                <span>
                  <strong>03</strong> Prioritize
                </span>
                <span>
                  <strong>04</strong> Decide
                </span>
              </div>
            </section>

            <section className="copilot-analyze-grid">
              <div className="copilot-panel">
                <div className="copilot-panel-top">
                  <div>
                    <div className="copilot-section-label">
                      ANALYZE A JOB
                    </div>
                    <h2>Evaluate a job before you apply</h2>
                  </div>

                  <div className="copilot-human-chip">
                    HUMAN DECISION
                  </div>
                </div>

                <form
                  onSubmit={analyzeJob}
                  className="copilot-form"
                >
                  <div className="copilot-form-grid">
                    <label>
                      Source
                      <select
                        value={form.source}
                        onChange={(event) =>
                          updateField(
                            "source",
                            event.target.value
                          )
                        }
                      >
                        {SOURCES.map((source) => (
                          <option key={source} value={source}>
                            {source}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Job URL
                      <input
                        type="url"
                        placeholder="https://..."
                        value={form.url}
                        onChange={(event) =>
                          updateField(
                            "url",
                            event.target.value
                          )
                        }
                      />
                    </label>

                    <label>
                      Job title
                      <input
                        required
                        placeholder="AI Automation Engineer"
                        value={form.title}
                        onChange={(event) =>
                          updateField(
                            "title",
                            event.target.value
                          )
                        }
                      />
                    </label>

                    <label>
                      Company
                      <input
                        required
                        placeholder="Company name"
                        value={form.company}
                        onChange={(event) =>
                          updateField(
                            "company",
                            event.target.value
                          )
                        }
                      />
                    </label>

                    <label className="copilot-full">
                      Location
                      <input
                        placeholder="Remote / Indonesia / EMEA"
                        value={form.location}
                        onChange={(event) =>
                          updateField(
                            "location",
                            event.target.value
                          )
                        }
                      />
                    </label>

                    <label className="copilot-full">
                      Job description
                      <textarea
                        required
                        rows="12"
                        placeholder="Paste the complete job description here..."
                        value={form.description}
                        onChange={(event) =>
                          updateField(
                            "description",
                            event.target.value
                          )
                        }
                      />
                    </label>
                  </div>

                  {error && (
                    <div className="copilot-error">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    className="copilot-primary"
                    disabled={loading}
                  >
                    {loading
                      ? "ANALYZING..."
                      : "ANALYZE OPPORTUNITY"}
                  </button>
                </form>
              </div>

              <div className="copilot-preview">
                {!result && !loading && (
                  <>
                    <div className="copilot-preview-line" />
                    <div className="copilot-section-label">
                      DECISION ENGINE
                    </div>
                    <h2>Know before you apply</h2>
                    <p>
                      The system separates four signals:
                      candidate fit, geographic eligibility,
                      opportunity quality and final action.
                    </p>

                    <div className="copilot-signal-list">
                      <div>
                        <span>01</span>
                        <strong>Candidate fit</strong>
                        <small>
                          Match the role against your profile
                        </small>
                      </div>
                      <div>
                        <span>02</span>
                        <strong>Remote eligibility</strong>
                        <small>
                          Detect restrictions and uncertainty
                        </small>
                      </div>
                      <div>
                        <span>03</span>
                        <strong>Opportunity quality</strong>
                        <small>
                          Rank what deserves attention
                        </small>
                      </div>
                      <div>
                        <span>04</span>
                        <strong>Human decision</strong>
                        <small>
                          AI recommends and you decide when to apply
                        </small>
                      </div>
                    </div>
                  </>
                )}

                {loading && (
                  <div className="copilot-processing">
                    <div className="copilot-spinner" />
                    <div className="copilot-section-label">
                      PROCESSING
                    </div>
                    <h2>Analyzing opportunity...</h2>
                    <p>
                      AI is evaluating the role against
                      your candidate profile
                    </p>
                  </div>
                )}

                {result && (
                  <AnalysisResult
                    result={result}
                    onOpenJob={openOriginalJob}
                  />
                )}
              </div>
            </section>
          </>
        )}

        {activeTab === "opportunities" && (
          <>
            <section className="copilot-page-hero">
              <div>
                <div className="copilot-kicker">
                  OPPORTUNITY PIPELINE
                </div>
                <h1>From job listings to real opportunities</h1>
                <p>
                  Ranked after search, AI matching, geo assessment
                  and opportunity scoring
                </p>
              </div>

              <div className="copilot-kpi-strip">
                <div>
                  <span>OPEN</span>
                  <strong>{opportunities.length}</strong>
                </div>
                <div>
                  <span>HIGH</span>
                  <strong className="accent">
                    {highPriorityCount}
                  </strong>
                </div>
                <div>
                  <span>VERIFY</span>
                  <strong className="warning">
                    {verifyCount}
                  </strong>
                </div>
              </div>
            </section>

            <div className="copilot-page-actions">
              <button
                type="button"
                className="copilot-secondary"
                onClick={loadOpportunities}
                disabled={opportunitiesLoading}
              >
                {opportunitiesLoading
                  ? "Refreshing..."
                  : "Refresh opportunities"}
              </button>
            </div>

            {opportunitiesError && (
              <div className="copilot-error">
                {opportunitiesError}
              </div>
            )}

            {packageError && (
              <div className="copilot-error">
                {packageError}
              </div>
            )}

            {packageLoading && (
              <div
                className="copilot-panel copilot-loading-panel"
                id="apply-package-panel"
              >
                <div className="copilot-spinner" />
                <div className="copilot-section-label">
                  BUILDING APPLY PACKAGE
                </div>
                <h2>Loading opportunity detail...</h2>
              </div>
            )}

            {selectedPackage && !packageLoading && (
              <div id="apply-package-panel">
                <ApplyPackage
                  opportunity={selectedPackage}
                  onOpenJob={openOriginalJob}
                  onMarkApplied={markAsApplied}
                  applicationSaving={applicationSaving}
                  applicationMessage={applicationMessage}
                />
              </div>
            )}

            {opportunitiesLoading ? (
              <div className="copilot-panel copilot-loading-panel">
                <div className="copilot-spinner" />
                <div className="copilot-section-label">
                  LOADING
                </div>
                <h2>Refreshing the pipeline...</h2>
              </div>
            ) : opportunities.length === 0 ? (
              <div className="copilot-panel copilot-empty-panel">
                <div className="copilot-empty-number">01</div>
                <div className="copilot-section-label">
                  PIPELINE CLEAR
                </div>
                <h2>No actionable opportunities yet</h2>
                <p>
                  New roles will appear here after the production
                  search and assessment pipeline runs
                </p>
              </div>
            ) : (
              <div className="copilot-opportunity-list">
                {opportunities.map((opportunity) => (
                  <OpportunityCard
                    key={opportunity.id}
                    opportunity={opportunity}
                    onOpenJob={openOriginalJob}
                    onViewPackage={loadApplyPackage}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === "applications" && (
          <>
            <section className="copilot-page-hero">
              <div>
                <div className="copilot-kicker">
                  APPLICATION TRACKER
                </div>
                <h1>Keep your applications moving</h1>
                <p>
                  One place for the jobs you reviewed, applied to
                  and moved forward
                </p>
              </div>

              <div className="copilot-kpi-strip">
                <div>
                  <span>APPLICATIONS</span>
                  <strong>{applications.length}</strong>
                </div>
              </div>
            </section>

            <div className="copilot-page-actions">
              <button
                type="button"
                className="copilot-secondary"
                onClick={loadApplications}
                disabled={applicationsLoading}
              >
                {applicationsLoading
                  ? "Refreshing..."
                  : "Refresh applications"}
              </button>
            </div>

            {applicationsError && (
              <div className="copilot-error">
                {applicationsError}
              </div>
            )}

            {applicationsLoading ? (
              <div className="copilot-panel copilot-loading-panel">
                <div className="copilot-spinner" />
                <div className="copilot-section-label">
                  LOADING
                </div>
                <h2>Refreshing applications...</h2>
              </div>
            ) : applications.length === 0 ? (
              <div className="copilot-panel copilot-empty-panel">
                <div className="copilot-empty-number">00</div>
                <div className="copilot-section-label">
                  APPLICATION TRACKER
                </div>
                <h2>No applications tracked yet</h2>
                <p>
                  Once you verify an opportunity and mark it as applied,
                  the outcome will appear here
                </p>
              </div>
            ) : (
              <div className="copilot-application-list">
                {applications.map((application) => (
                  <ApplicationCard
                    key={application.id}
                    application={application}
                    onOpenJob={openOriginalJob}
                    onUpdateStatus={updateApplicationStatus}
                    updating={
                      statusUpdating === application.id
                    }
                  />
                ))}
              </div>
            )}
          </>
        )}
      </main>

      <footer className="copilot-footer">
        <nav className="copilot-footer-links" aria-label="Footer">
          <button
            type="button"
            className="copilot-footer-link"
            onClick={() => setInfoModal("about")}
          >
            About
          </button>

          <a
            href="https://github.com/vidiatmoko/ai-job-matcher-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="copilot-footer-link"
          >
            GitHub
          </a>

          <a
            href="https://www.linkedin.com/in/anggik-pipit-vidiatmoko/"
            target="_blank"
            rel="noopener noreferrer"
            className="copilot-footer-link"
          >
            LinkedIn
          </a>

          <button
            type="button"
            className="copilot-footer-link"
            onClick={() => setInfoModal("privacy")}
          >
            Privacy
          </button>
        </nav>

        <div className="copilot-footer-brand">
          © 2026 Vidi - Remote Job Intelligence
        </div>
      </footer>

      {infoModal && (
        <div
          className="copilot-modal-backdrop"
          role="presentation"
          onMouseDown={() => setInfoModal(null)}
        >
          <div
            className="copilot-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="copilot-modal-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="copilot-modal-close"
              onClick={() => setInfoModal(null)}
              aria-label="Close"
            >
              ×
            </button>

            <div className="copilot-section-label">
              {infoModal === "about" ? "ABOUT" : "PRIVACY"}
            </div>

            <h2 id="copilot-modal-title">
              {infoModal === "about"
                ? "Remote Job Intelligence"
                : "Privacy"}
            </h2>

            {infoModal === "about" ? (
              <>
                <p>
                  Remote Job Intelligence is an Indonesia-built remote job
                  intelligence system that researches, evaluates and
                  prioritizes global remote opportunities
                </p>
                <p>
                  AI handles the research and analysis. The final decision
                  to apply remains with the human
                </p>
              </>
            ) : (
              <>
                <p>
                  Job information is analyzed to support career decisions
                  and opportunity evaluation
                </p>
                <p>
                  Application actions remain user-controlled
                </p>
              </>
            )}

            <button
              type="button"
              className="copilot-modal-action"
              onClick={() => setInfoModal(null)}
            >
              Close
            </button>
          </div>
        </div>
      )}

    </div>
  );
}

// ============================================================
// ANALYSIS RESULT
// ============================================================

function AnalysisResult({
  result,
  onOpenJob,
}) {
  return (
    <div>

      <div className="result-header">

        <div>

          <p className="eyebrow">
            ANALYSIS RESULT
          </p>

          <h2>
            {result.job.title}
          </h2>

          <p className="muted">
            {result.job.company}
            {" · "}
            {result.job.location ||
              "Location unknown"}
          </p>

        </div>

        <div className="score">

          <span>
            {result.ai.match_score}
          </span>

          <small>
            AI MATCH
          </small>

        </div>

      </div>

      <div className="metrics">

        <Metric
          label="Geo"
          value={
            displayGeo(
              result.opportunity
                .geo_status
            )
          }
        />

        <Metric
          label="Priority"
          value={
            result.opportunity
              .priority
          }
        />

        <Metric
          label="Action"
          value={
            displayAction(
              result.opportunity
                .final_action
            )
          }
        />

        <Metric
          label="Provider"
          value={
            result.ai.provider
          }
        />

      </div>

      <div className="section">

        <h3>
          Why this job
        </h3>

        <p>
          {result.ai.fit_summary}
        </p>

      </div>

      <div className="columns">

        <div className="section">

          <h3>
            Strengths
          </h3>

          <ul>
            {result.ai.key_pros?.map(
              (item, index) => (
                <li key={index}>
                  {item}
                </li>
              )
            )}
          </ul>

        </div>

        <div className="section">

          <h3>
            Gaps
          </h3>

          <ul>
            {result.ai.key_gaps?.map(
              (item, index) => (
                <li key={index}>
                  {item}
                </li>
              )
            )}
          </ul>

        </div>

      </div>

      <div className="section">

        <h3>
          Outreach
        </h3>

        <div className="outreach">
          {
            result.ai.draft_outreach ||
            "No outreach draft available."
          }
        </div>

      </div>

      {result.job.url && (

        <button
          type="button"
          className="open-job"
          onClick={() =>
            onOpenJob(
              result.job.url
            )
          }
        >
          OPEN ORIGINAL JOB →
        </button>

      )}

    </div>
  );
}


// ============================================================
// OPPORTUNITY CARD
// ============================================================

function OpportunityCard({
  opportunity,
  onOpenJob,
  onViewPackage,
}) {
  return (
    <article className="opportunity-card">

      <div className="opportunity-top">

        <div>

          <span
            className={`priority-badge ${priorityClass(
              opportunity.priority
            )}`}
          >
            {
              opportunity.priority
            }
          </span>

          <h3>
            {
              opportunity.title
            }
          </h3>

          <p className="company">
            {opportunity.company ||
              "Company unknown"}
          </p>

          <p className="location">
            {opportunity.location ||
              "Location unknown"}
          </p>

        </div>

        <div className="card-score">

          {opportunity.match_score}

          <small>
            %
          </small>

          <span>
            MATCH
          </span>

        </div>

      </div>

      <div className="card-metrics">

        <Metric
          label="Opportunity"
          value={
            opportunity.opportunity_score
          }
        />

        <Metric
          label="Geo"
          value={
            displayGeo(
              opportunity.geo_status
            )
          }
        />

        <Metric
          label="Action"
          value={
            displayAction(
              opportunity.final_action
            )
          }
        />

        <Metric
          label="Source"
          value={
            displaySource(
              opportunity.source
            )
          }
        />

      </div>

      <div className="opportunity-actions">

        <button
          type="button"
          className="secondary-action"
          onClick={() =>
            onViewPackage(
              opportunity.id
            )
          }
        >
          VIEW APPLY PACKAGE
        </button>

        <button
          type="button"
          onClick={() =>
            onOpenJob(
              opportunity.url
            )
          }
          disabled={
            !opportunity.url
          }
        >
          OPEN JOB
        </button>

      </div>

    </article>
  );
}


// ============================================================
// APPLY PACKAGE
// ============================================================

function ApplyPackage({
  opportunity,
  onOpenJob,
  onMarkApplied,
  applicationSaving,
  applicationMessage,
}) {
  const strengths =
    parseJsonList(
      opportunity.key_pros
    );

  const gaps =
    parseJsonList(
      opportunity.key_gaps
    );

  const blocked =
    opportunity.final_action ===
      "SKIP" ||
    opportunity.final_action ===
      "DO NOT APPLY";

  return (
    <section className="card apply-package">

      <div className="package-header">

        <div>

          <p className="eyebrow">
            APPLICATION PACKAGE
          </p>

          <h2>
            {
              opportunity.title
            }
          </h2>

          <p className="muted">
            {opportunity.company}
            {" · "}
            {opportunity.location}
          </p>

        </div>

        <div className="score">

          <span>
            {
              opportunity.match_score
            }
          </span>

          <small>
            AI MATCH
          </small>

        </div>

      </div>

      <div className="package-metrics">

        <Metric
          label="Priority"
          value={
            opportunity.priority
          }
        />

        <Metric
          label="Opportunity"
          value={
            opportunity.opportunity_score
          }
        />

        <Metric
          label="Geo"
          value={
            displayGeo(
              opportunity.geo_status
            )
          }
        />

        <Metric
          label="Final Action"
          value={
            displayAction(
              opportunity.final_action
            )
          }
        />

      </div>

      <div className="section">

        <h3>
          Why this job
        </h3>

        <p>
          {
            opportunity.fit_summary
          }
        </p>

      </div>

      <div className="columns">

        <div className="section">

          <h3>
            Strengths to emphasize
          </h3>

          <ul>

            {strengths.map(
              (item, index) => (
                <li key={index}>
                  {item}
                </li>
              )
            )}

          </ul>

        </div>

        <div className="section">

          <h3>
            Gaps to handle
          </h3>

          <ul>

            {gaps.map(
              (item, index) => (
                <li key={index}>
                  {item}
                </li>
              )
            )}

          </ul>

        </div>

      </div>

      <div className="section">

        <h3>
          Outreach
        </h3>

        <div className="outreach">
          {
            opportunity.draft_outreach ||
            "No outreach draft available."
          }
        </div>

      </div>

      <div className="package-actions">

        <button
          type="button"
          className="open-job"
          onClick={() =>
            onOpenJob(
              opportunity.url
            )
          }
          disabled={
            !opportunity.url
          }
        >
          OPEN ORIGINAL JOB →
        </button>

        <button
          type="button"
          className="secondary-action"
          onClick={
            onMarkApplied
          }
          disabled={
            applicationSaving ||
            blocked
          }
        >
          {applicationSaving
            ? "SAVING..."
            : blocked
              ? "NOT ELIGIBLE"
              : "MARK AS APPLIED"}
        </button>

      </div>

      {applicationMessage && (

        <div className="application-message">
          {applicationMessage}
        </div>

      )}

    </section>
  );
}


// ============================================================
// APPLICATION CARD
// ============================================================

function ApplicationCard({
  application,
  onOpenJob,
  onUpdateStatus,
  updating,
}) {
  return (
    <article className="application-card">

      <div className="application-header">

        <div>

          <span
            className={`application-status ${statusClass(
              application.status
            )}`}
          >
            {
              displayApplicationStatus(
                application.status
              )
            }
          </span>

          <h3>
            {
              application.title
            }
          </h3>

          <p className="company">
            {
              application.company
            }
          </p>

          <p className="location">
            {
              application.location
            }
          </p>

        </div>

        <div className="card-score">

          {
            application.match_score ??
            "-"
          }

          <small>
            %
          </small>

          <span>
            MATCH
          </span>

        </div>

      </div>

      <div className="card-metrics">

        <Metric
          label="Opportunity"
          value={
            application.opportunity_score
          }
        />

        <Metric
          label="Priority"
          value={
            application.priority
          }
        />

        <Metric
          label="Final Action"
          value={
            displayAction(
              application.final_action
            )
          }
        />

        <Metric
          label="Source"
          value={
            displaySource(
              application.source
            )
          }
        />

      </div>

      <div className="application-update">

        <label>
          Update Status

          <select
            value={
              application.status
            }
            disabled={updating}
            onChange={(event) =>
              onUpdateStatus(
                application.id,
                event.target.value
              )
            }
          >
            {APPLICATION_STATUSES.map(
              (status) => (
                <option
                  key={status}
                  value={status}
                >
                  {
                    displayApplicationStatus(
                      status
                    )
                  }
                </option>
              )
            )}
          </select>

        </label>

      </div>

      <div className="opportunity-actions">

        <button
          type="button"
          onClick={() =>
            onOpenJob(
              application.url
            )
          }
          disabled={
            !application.url
          }
        >
          OPEN JOB
        </button>

      </div>

      <p className="application-meta">
        Application #{application.id}
        {" · "}
        CV {application.cv_version}
      </p>

    </article>
  );
}


// ============================================================
// HELPERS
// ============================================================

function parseJsonList(value) {
  if (!value) {
    return [];
  }

  if (Array.isArray(value)) {
    return value;
  }

  try {
    const parsed =
      JSON.parse(value);

    return Array.isArray(parsed)
      ? parsed
      : [];
  } catch {
    return [];
  }
}

function displaySource(source) {
  const labels = {
    adzuna: "Adzuna",
    remoteok: "RemoteOK",
    jobicy: "Jobicy",
    linkedin: "LinkedIn",
    upwork: "Upwork",
    glints: "Glints",
    wellfound: "Wellfound",
    dealls: "Dealls",
    "tech in asia":
      "Tech in Asia",
    freelancer:
      "Freelancer",
  };

  return (
    labels[source] ||
    source ||
    "Unknown"
  );
}

function displayGeo(status) {
  const labels = {
    LIKELY_ELIGIBLE:
      "Likely Eligible",
    NEEDS_VERIFICATION:
      "Needs Verification",
    RESTRICTED:
      "Restricted",
  };

  return (
    labels[status] ||
    status ||
    "Unknown"
  );
}

function displayAction(action) {
  const labels = {
    "APPLY NOW":
      "Apply Now",

    "APPLY WITH TAILORED CV":
      "Apply with Tailored CV",

    "VERIFY BEFORE APPLY":
      "Verify Before Apply",

    "DO NOT APPLY":
      "Do Not Apply",

    SKIP:
      "Skip",

    VERIFY:
      "Verify",

    REVIEW:
      "Review",
  };

  return (
    labels[action] ||
    action ||
    "Review"
  );
}

function displayApplicationStatus(
  status
) {
  const labels = {
    SAVED: "Saved",
    REVIEWED: "Reviewed",
    APPLIED: "Applied",
    RECRUITER_CONTACTED:
      "Recruiter Contacted",
    INTERVIEW:
      "Interview",
    TECHNICAL_TEST:
      "Technical Test",
    FINAL_INTERVIEW:
      "Final Interview",
    OFFER: "Offer",
    REJECTED:
      "Rejected",
    NO_RESPONSE:
      "No Response",
    WITHDRAWN:
      "Withdrawn",
  };

  return (
    labels[status] ||
    status ||
    "Unknown"
  );
}

function statusClass(
  status
) {
  switch (status) {
    case "APPLIED":
      return "status-applied";

    case "RECRUITER_CONTACTED":
      return "status-contacted";

    case "INTERVIEW":
      return "status-interview";

    case "TECHNICAL_TEST":
      return "status-test";

    case "FINAL_INTERVIEW":
      return "status-final";

    case "OFFER":
      return "status-offer";

    case "REJECTED":
      return "status-rejected";

    case "WITHDRAWN":
      return "status-withdrawn";

    default:
      return "status-neutral";
  }
}

function priorityClass(
  priority
) {
  switch (priority) {
    case "HIGH":
      return "priority-high";

    case "MEDIUM":
      return "priority-medium";

    case "LOW":
      return "priority-low";

    default:
      return "priority-verify";
  }
}

function Metric({
  label,
  value,
}) {
  return (
    <div className="metric">
      <span>
        {label}
      </span>

      <strong>
        {value ?? "-"}
      </strong>
    </div>
  );
}

// Final AI workspace design direction inspired by modern enterprise automation products; logic preserved.
export default App;

