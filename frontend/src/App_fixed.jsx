import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

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
        `${API_URL}/api/opportunities`
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
            "Gagal mengambil Apply Package."
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
            "Gagal menyimpan application."
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
            "Gagal mengambil applications."
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
            "Gagal mengubah status application."
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

  return (
    <div className="app">

      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="header">
        <div>
          <p className="eyebrow">
            AI CAREER COPILOT
          </p>

          <h1>
            Find the right job.
            <br />
            Apply with confidence.
          </h1>

          <p className="subtitle">
            Analyze jobs from LinkedIn,
            Upwork, Glints, Wellfound,
            and other platforms.
          </p>
        </div>

        <div className="status-pill">
          ● API Ready
        </div>
      </header>

      {/* ======================================================
          NAVIGATION
      ====================================================== */}

      <nav className="tabs">

        <button
          type="button"
          className={
            activeTab === "manual"
              ? "tab active"
              : "tab"
          }
          onClick={() => {
            setActiveTab("manual");
            setSelectedPackage(null);
            setApplicationMessage("");
          }}
        >
          Manual Job
        </button>

        <button
          type="button"
          className={
            activeTab ===
            "opportunities"
              ? "tab active"
              : "tab"
          }
          onClick={() => {
            setActiveTab(
              "opportunities"
            );
            setSelectedPackage(null);
            setApplicationMessage("");
          }}
        >
          My Opportunities
        </button>

        <button
          type="button"
          className={
            activeTab ===
            "applications"
              ? "tab active"
              : "tab"
          }
          onClick={() => {
            setActiveTab(
              "applications"
            );
            setSelectedPackage(null);
            setApplicationMessage("");
          }}
        >
          My Applications
        </button>

      </nav>

      {/* ======================================================
          MANUAL JOB
      ====================================================== */}

      {activeTab === "manual" && (

        <main className="layout">

          <section className="card">

            <h2>
              Manual Job Analyzer
            </h2>

            <p className="muted">
              Copy the job details from
              the original platform and
              analyze them here.
            </p>

            <form
              onSubmit={analyzeJob}
            >

              <label>
                Source

                <select
                  value={
                    form.source
                  }
                  onChange={(event) =>
                    updateField(
                      "source",
                      event.target.value
                    )
                  }
                >
                  {SOURCES.map(
                    (source) => (
                      <option
                        key={source}
                        value={source}
                      >
                        {source}
                      </option>
                    )
                  )}
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
                Job Title

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
                  value={
                    form.company
                  }
                  onChange={(event) =>
                    updateField(
                      "company",
                      event.target.value
                    )
                  }
                />

              </label>

              <label>
                Location

                <input
                  placeholder="Remote / Indonesia / EMEA"
                  value={
                    form.location
                  }
                  onChange={(event) =>
                    updateField(
                      "location",
                      event.target.value
                    )
                  }
                />

              </label>

              <label>
                Job Description

                <textarea
                  required
                  rows="13"
                  placeholder="Paste the complete job description here..."
                  value={
                    form.description
                  }
                  onChange={(event) =>
                    updateField(
                      "description",
                      event.target.value
                    )
                  }
                />

              </label>

              {error && (
                <div className="error">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={
                  loading
                }
              >
                {loading
                  ? "ANALYZING..."
                  : "ANALYZE JOB"}
              </button>

            </form>

          </section>

          <section className="card result-card">

            {!result &&
              !loading && (

                <div className="empty">

                  <div className="empty-icon">
                    AI
                  </div>

                  <h2>
                    No analysis yet
                  </h2>

                  <p>
                    Submit a job to see
                    match score, remote
                    eligibility, opportunity
                    score, strengths, gaps,
                    and application action.
                  </p>

                </div>

              )}

            {loading && (

              <div className="empty">

                <div className="loader" />

                <h2>
                  Analyzing opportunity...
                </h2>

                <p>
                  AI is evaluating the job
                  against your candidate profile.
                </p>

              </div>

            )}

            {result && (

              <AnalysisResult
                result={result}
                onOpenJob={
                  openOriginalJob
                }
              />

            )}

          </section>

        </main>

      )}

      {/* ======================================================
          MY OPPORTUNITIES
      ====================================================== */}

      {activeTab ===
        "opportunities" && (

        <main className="opportunities-page">

          <div className="opportunities-header">

            <div>

              <p className="eyebrow">
                OPPORTUNITY PIPELINE
              </p>

              <h2>
                My Opportunities
              </h2>

              <p className="muted">
                Lowongan yang sudah melalui
                filter, AI matching, geo assessment,
                dan opportunity scoring.
              </p>

            </div>

            <button
              type="button"
              className="refresh-button"
              onClick={
                loadOpportunities
              }
              disabled={
                opportunitiesLoading
              }
            >
              {opportunitiesLoading
                ? "Loading..."
                : "Refresh"}
            </button>

          </div>

          {opportunitiesError && (
            <div className="error">
              {opportunitiesError}
            </div>
          )}

          {packageError && (
            <div className="error">
              {packageError}
            </div>
          )}

          {packageLoading && (
            <div
              className="card package-loading"
              id="apply-package-panel"
            >
              <div className="loader" />

              <h2>
                Loading Apply Package...
              </h2>
            </div>
          )}

          {selectedPackage &&
            !packageLoading && (
              <div id="apply-package-panel">
                <ApplyPackage
                  opportunity={
                    selectedPackage
                  }
                  onOpenJob={
                    openOriginalJob
                  }
                  onMarkApplied={
                    markAsApplied
                  }
                  applicationSaving={
                    applicationSaving
                  }
                  applicationMessage={
                    applicationMessage
                  }
                />
              </div>
            )}

          {opportunitiesLoading ? (

            <div className="card loading-card">

              <div className="loader" />

              <h2>
                Loading opportunities...
              </h2>

            </div>

          ) : (

            <div className="opportunity-grid">

              {opportunities.map(
                (opportunity) => (

                  <OpportunityCard
                    key={
                      opportunity.id
                    }
                    opportunity={
                      opportunity
                    }
                    onOpenJob={
                      openOriginalJob
                    }
                    onViewPackage={
                      loadApplyPackage
                    }
                  />

                )
              )}

            </div>

          )}

        </main>

      )}

      {/* ======================================================
          MY APPLICATIONS
      ====================================================== */}

      {activeTab ===
        "applications" && (

        <main className="opportunities-page">

          <div className="opportunities-header">

            <div>

              <p className="eyebrow">
                APPLICATION TRACKER
              </p>

              <h2>
                My Applications
              </h2>

              <p className="muted">
                Pantau semua lowongan yang
                pernah kamu tandai sebagai
                application.
              </p>

            </div>

            <button
              type="button"
              className="refresh-button"
              onClick={
                loadApplications
              }
              disabled={
                applicationsLoading
              }
            >
              {applicationsLoading
                ? "Loading..."
                : "Refresh"}
            </button>

          </div>

          {applicationsError && (
            <div className="error">
              {applicationsError}
            </div>
          )}

          {applicationsLoading ? (

            <div className="card loading-card">

              <div className="loader" />

              <h2>
                Loading applications...
              </h2>

            </div>

          ) : applications.length ===
            0 ? (

            <div className="card empty">

              <div className="empty-icon">
                APP
              </div>

              <h2>
                No applications yet
              </h2>

              <p>
                Setelah kamu menandai
                opportunity sebagai APPLIED,
                riwayatnya akan muncul di sini.
              </p>

            </div>

          ) : (

            <div className="applications-grid">

              {applications.map(
                (application) => (

                  <ApplicationCard
                    key={
                      application.id
                    }
                    application={
                      application
                    }
                    onOpenJob={
                      openOriginalJob
                    }
                    onUpdateStatus={
                      updateApplicationStatus
                    }
                    updating={
                      statusUpdating ===
                      application.id
                    }
                  />

                )
              )}

            </div>

          )}

        </main>

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

export default App;