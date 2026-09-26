/* ============================================================
   SKILL-GAP PREDICTOR COMPLETE FRONTEND APPLICATION JAVASCRIPT
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {
  "use strict";

  /* ========================================================
     GLOBAL STATE
     ======================================================== */
  const state = {
    loggedIn: Boolean(window.APP_DATA?.loggedIn),
    user: window.APP_DATA?.user || null,
    careerUrl: window.APP_DATA?.careerUrl || "",
    careerJobs: Array.isArray(window.APP_DATA?.careerJobs) ? window.APP_DATA.careerJobs : [],
    extractedSkills: Array.isArray(window.APP_DATA?.extractedSkills) ? window.APP_DATA.extractedSkills : [],
    requiredSkills: Array.isArray(window.APP_DATA?.requiredSkills) ? window.APP_DATA.requiredSkills : [],
    atsScore: Number(window.APP_DATA?.atsScore || 0),
    targetCompany: window.APP_DATA?.targetCompany || "",
    targetRole: window.APP_DATA?.targetRole || "",
    recommendedJob: window.APP_DATA?.recommendedJob || null,
    currentView: "dashboard",
    selectedResume: null,
    charts: {
      radar: null,
      pie: null
    }
  };

  /* ========================================================
     BASIC HELPERS
     ======================================================== */
  function $(id) {
    return document.getElementById(id);
  }

  function qs(selector) {
    return document.querySelector(selector);
  }

  function qsa(selector) {
    return Array.from(document.querySelectorAll(selector));
  }

  function escapeHtml(value) {
    if (value === null || value === undefined) {
      return "";
    }
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function normalizeSkill(value) {
    return String(value || "")
      .trim()
      .replace(/\s+/g, " ");
  }

  function normalizeSkills(skills) {
    if (!Array.isArray(skills)) {
      return [];
    }
    const result = [];
    skills.forEach(function (skill) {
      let value = "";
      if (typeof skill === "string") {
        value = skill;
      } else if (skill && typeof skill === "object") {
        value = skill.name || skill.skill || skill.title || skill.value || "";
      }
      value = normalizeSkill(value);
      if (
        value &&
        !result.some(function (x) {
          return x.toLowerCase() === value.toLowerCase();
        })
      ) {
        result.push(value);
      }
    });
    return result;
  }

  function showElement(element) {
    if (element) {
      element.style.display = "";
    }
  }

  function hideElement(element) {
    if (element) {
      element.style.display = "none";
    }
  }

  /* ========================================================
     POPUP SYSTEM
     ======================================================== */
  function ensurePopup() {
    if ($("sg-popup-overlay")) {
      return;
    }

    const overlay = document.createElement("div");
    overlay.id = "sg-popup-overlay";
    overlay.innerHTML = `
      <div class="sg-popup-card">
        <button type="button" id="sg-popup-close" class="sg-popup-close">×</button>
        <div id="sg-popup-icon" class="sg-popup-icon">✓</div>
        <h3 id="sg-popup-title">Message</h3>
        <p id="sg-popup-message">Message</p>
        <button type="button" id="sg-popup-ok" class="btn">OK</button>
      </div>
    `;
    document.body.appendChild(overlay);

    const style = document.createElement("style");
    style.id = "sg-popup-style";
    style.textContent = `
      #sg-popup-overlay {
        position: fixed;
        inset: 0;
        z-index: 999999;
        display: none;
        align-items: center;
        justify-content: center;
        background: rgba(0,0,0,.72);
        backdrop-filter: blur(5px);
        padding: 20px;
      }
      .sg-popup-card {
        position: relative;
        width: min(440px, 95vw);
        padding: 30px 26px;
        border-radius: 18px;
        text-align: center;
        background: var(--card-bg, #111827);
        color: var(--text-main, #f8fafc);
        border: 1px solid rgba(148,163,184,.25);
        box-shadow: 0 25px 70px rgba(0,0,0,.5);
      }
      .sg-popup-close {
        position: absolute;
        right: 15px;
        top: 10px;
        border: 0;
        background: transparent;
        color: #94a3b8;
        font-size: 27px;
        cursor: pointer;
      }
      .sg-popup-icon {
        width: 58px;
        height: 58px;
        margin: 0 auto 15px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 27px;
        font-weight: 800;
        background: rgba(16,185,129,.15);
        color: #34d399;
      }
      .sg-popup-card h3 {
        margin: 0 0 10px;
        font-size: 21px;
      }
      .sg-popup-card p {
        margin: 0 0 22px;
        color: #94a3b8;
        line-height: 1.6;
      }
      .sg-popup-card .btn {
        min-width: 110px;
      }
    `;
    document.head.appendChild(style);

    $("sg-popup-close").addEventListener("click", hidePopup);
    $("sg-popup-ok").addEventListener("click", hidePopup);

    overlay.addEventListener("click", function (event) {
      if (event.target === overlay) {
        hidePopup();
      }
    });
  }

  function showPopup(title, message, type) {
    ensurePopup();
    const overlay = $("sg-popup-overlay");
    const titleElement = $("sg-popup-title");
    const messageElement = $("sg-popup-message");
    const iconElement = $("sg-popup-icon");

    if (!overlay) {
      return;
    }

    titleElement.textContent = title || "Message";
    messageElement.textContent = message || "";

    if (type === "error") {
      iconElement.textContent = "!";
      iconElement.style.color = "#fb7185";
      iconElement.style.background = "rgba(244,63,94,.15)";
    } else if (type === "warning") {
      iconElement.textContent = "!";
      iconElement.style.color = "#fbbf24";
      iconElement.style.background = "rgba(245,158,11,.15)";
    } else {
      iconElement.textContent = "✓";
      iconElement.style.color = "#34d399";
      iconElement.style.background = "rgba(16,185,129,.15)";
    }

    overlay.style.display = "flex";
  }

  function hidePopup() {
    const overlay = $("sg-popup-overlay");
    if (overlay) {
      overlay.style.display = "none";
    }
  }

  window.showSkillGapPopup = showPopup;

  const nativeAlert = window.alert;
  window.alert = function (message) {
    try {
      showPopup("Skill-Gap Predictor", String(message || ""), "info");
    } catch (error) {
      nativeAlert(message);
    }
  };

  /* ========================================================
     LOADING SYSTEM
     ======================================================== */
  function setLoading(button, loading, text) {
    if (!button) {
      return;
    }

    if (loading) {
      if (!button.dataset.originalText) {
        button.dataset.originalText = button.innerHTML;
      }
      button.disabled = true;
      button.innerHTML = `<span class="button-loading"></span> ${escapeHtml(text || "Processing...")}`;
    } else {
      button.disabled = false;
      if (button.dataset.originalText) {
        button.innerHTML = button.dataset.originalText;
        delete button.dataset.originalText;
      }
    }
  }

  function hidePageLoader() {
    const loader = $("page-loader");
    if (!loader) {
      return;
    }
    loader.classList.add("loaded");
    setTimeout(function () {
      loader.style.display = "none";
    }, 300);
  }

  window.addEventListener("load", hidePageLoader);
  setTimeout(hidePageLoader, 3000);

  /* ========================================================
     API REQUEST HELPER
     ======================================================== */
  async function apiRequest(action, data, options) {
    data = data || {};
    options = options || {};
    const method = String(options.method || "POST").toUpperCase();
    let url = "api.php?action=" + encodeURIComponent(action);

    const fetchOptions = {
      method: method,
      credentials: "same-origin",
      cache: "no-store",
      headers: {}
    };

    if (method === "GET") {
      const params = new URLSearchParams();
      Object.keys(data).forEach(function (key) {
        if (data[key] !== undefined && data[key] !== null) {
          params.append(key, String(data[key]));
        }
      });
      const query = params.toString();
      if (query) {
        url += "&" + query;
      }
    } else {
      if (data instanceof FormData) {
        fetchOptions.body = data;
      } else {
        const params = new URLSearchParams();
        Object.keys(data).forEach(function (key) {
          if (data[key] !== undefined && data[key] !== null) {
            params.append(key, String(data[key]));
          }
        });
        fetchOptions.headers["Content-Type"] = "application/x-www-form-urlencoded;charset=UTF-8";
        fetchOptions.body = params.toString();
      }
    }

    const response = await fetch(url, fetchOptions);
    const responseText = await response.text();

    let result;
    try {
      result = JSON.parse(responseText);
    } catch (error) {
      console.error("Invalid API response:", responseText);
      throw new Error("Invalid server response.");
    }

    if (!response.ok) {
      throw new Error(result.message || result.error || "Request failed.");
    }

    return result;
  }

  function apiSuccess(result) {
    return Boolean(
      result &&
        (result.success === true || result.status === "success" || result.ok === true)
    );
  }

  /* ========================================================
     AUTHENTICATION
     ======================================================== */
  function initAuth() {
    const tabLogin = $("tab-btn-login");
    const tabSignup = $("tab-btn-signup");
    const formLoginBox = $("form-login-box");
    const formSignupBox = $("form-signup-box");

    function showLogin() {
      if (tabLogin) tabLogin.classList.add("active");
      if (tabSignup) tabSignup.classList.remove("active");
      showElement(formLoginBox);
      hideElement(formSignupBox);
    }

    function showSignup() {
      if (tabSignup) tabSignup.classList.add("active");
      if (tabLogin) tabLogin.classList.remove("active");
      showElement(formSignupBox);
      hideElement(formLoginBox);
    }

    if (tabLogin) {
      tabLogin.addEventListener("click", function (event) {
        event.preventDefault();
        showLogin();
      });
    }

    if (tabSignup) {
      tabSignup.addEventListener("click", function (event) {
        event.preventDefault();
        showSignup();
      });
    }

    const loginForm = $("form-login");
    if (loginForm) {
      loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const emailElement = $("login_email");
        const passwordElement = $("login_password");
        const errorElement = $("login-error-msg");
        const successElement = $("login-success-msg");
        const button = $("btn-do-login");

        const email = emailElement ? emailElement.value.trim() : "";
        const password = passwordElement ? passwordElement.value : "";

        if (!email || !password) {
          if (errorElement) {
            errorElement.textContent = "Please enter both email and password.";
            errorElement.style.display = "block";
          }
          return;
        }

        if (errorElement) errorElement.style.display = "none";
        setLoading(button, true, "Signing in...");

        const formData = new FormData(loginForm);
        formData.set("action", "login");

        try {
          const result = await apiRequest("login", formData);
          if (!apiSuccess(result)) {
            throw new Error(result.message || "Login failed.");
          }
          if (successElement) {
            successElement.textContent = "Login successful. Opening dashboard...";
            successElement.style.display = "block";
          }

          setTimeout(function () {
            window.location.replace(window.location.pathname + "?logged_in=1");
          }, 500);
        } catch (error) {
          if (errorElement) {
            errorElement.textContent = error.message || "Unable to sign in.";
            errorElement.style.display = "block";
          }
          setLoading(button, false);
        }
      });
    }

    const signupForm = $("form-signup");
    if (signupForm) {
      signupForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const errorElement = $("signup-error-msg");
        const successElement = $("signup-success-msg");
        const button = $("btn-do-signup");

        if (errorElement) errorElement.style.display = "none";
        if (successElement) successElement.style.display = "none";

        const name = $("signup_name")?.value.trim() || "";
        const email = $("signup_email")?.value.trim() || "";
        const password = $("signup_pwd")?.value || "";
        const university = $("signup_uni")?.value.trim() || "";
        const branch = $("signup_branch")?.value.trim() || "";
        const graduationYear = ($("signup_gradyear") || $("signup_year"))?.value || "";
        const terms = $("signup-terms");

        if (!name || !email || !password || !university || !branch || !graduationYear) {
          if (errorElement) {
            errorElement.textContent = "Please fill in all required fields.";
            errorElement.style.display = "block";
          }
          return;
        }

        if (terms && !terms.checked) {
          if (errorElement) {
            errorElement.textContent = "Please accept the terms before creating your account.";
            errorElement.style.display = "block";
          }
          return;
        }

        setLoading(button, true, "Creating Account...");

        const formData = new FormData(signupForm);
        formData.set("action", "signup");
        formData.set("name", name);
        formData.set("email", email);
        formData.set("password", password);
        formData.set("university", university);
        formData.set("branch", branch);
        formData.set("graduation_year", graduationYear);

        try {
          const result = await apiRequest("signup", formData);
          if (!apiSuccess(result)) {
            throw new Error(result.message || "Account registration failed.");
          }
          if (successElement) {
            successElement.textContent = "Account registered successfully.";
            successElement.style.display = "block";
          }
          showPopup(
            "Account Registered Successfully",
            "Your account has been created. Please log in with your new account.",
            "success"
          );
          setTimeout(function () {
            showLogin();
            if ($("login_email")) {
              $("login_email").value = email;
            }
          }, 1200);
        } catch (error) {
          if (errorElement) {
            errorElement.textContent = error.message || "Unable to create account.";
            errorElement.style.display = "block";
          }
          showPopup("Registration Failed", error.message || "Unable to create account.", "error");
        } finally {
          setLoading(button, false);
        }
      });
    }

    const logoutButton = $("btn-logout");
    if (logoutButton) {
      logoutButton.addEventListener("click", async function (event) {
        event.preventDefault();
        try {
          await apiRequest("logout", {}, { method: "GET" });
        } catch (error) {
          console.error("Logout error:", error);
        }
        window.location.replace(window.location.pathname);
      });
    }
  }

  /* ========================================================
     THEME
     ======================================================== */
  function initTheme() {
    const savedTheme = localStorage.getItem("skillGapTheme");
    if (savedTheme === "dark") {
      document.body.classList.add("dark-mode");
      document.documentElement.classList.add("dark-mode");
    }

    const buttons = qsa("#theme-toggle, #btn-theme-toggle, .theme-toggle");
    buttons.forEach(function (button) {
      button.addEventListener("click", function () {
        const enabled = document.body.classList.toggle("dark-mode");
        document.documentElement.classList.toggle("dark-mode", enabled);
        localStorage.setItem("skillGapTheme", enabled ? "dark" : "light");
        updateChartsTheme();
      });
    });
  }

  /* ========================================================
     SIDEBAR / MOBILE MENU
     ======================================================== */
  function initSidebar() {
    const menuButtons = qsa("#menu-toggle, #mobile-menu-toggle, .menu-toggle");
    const sidebar = $("sidebar");

    menuButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        if (sidebar) sidebar.classList.toggle("open");
        document.body.classList.toggle("sidebar-open");
      });
    });

    const closeButtons = qsa("#sidebar-close, .sidebar-close");
    closeButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        if (sidebar) sidebar.classList.remove("open");
        document.body.classList.remove("sidebar-open");
      });
    });
  }

  /* ========================================================
     NAVIGATION
     ======================================================== */
  function initNavigation() {
    const navItems = qsa(".nav-item");
    const views = qsa(".view-panel");

    navItems.forEach(function (item) {
      item.addEventListener("click", function (event) {
        event.preventDefault();
        const targetView = item.getAttribute("data-view");
        if (!targetView) return;

        navItems.forEach(function (nav) {
          nav.classList.remove("active");
        });
        views.forEach(function (view) {
          view.style.display = "none";
        });

        item.classList.add("active");
        const target = $(targetView);
        if (target) {
          target.style.display = "block";
        }

        state.currentView = targetView;

        if (targetView === "view-roadmap") loadDynamicRoadmap();
        if (targetView === "view-interview") loadDynamicInterview();
        if (targetView === "view-jobranking") loadRankedJobs();
        if (targetView === "view-report") updateReport();
      });
    });
  }

  /* ========================================================
     CAREER URL / DYNAMIC JOB SCRAPER
     ======================================================== */
  function initWebScraper() {
    const button = $("btn-scrape-url");
    const input = $("input-scrape-url");

    if (!button || !input) return;

    button.addEventListener("click", async function (event) {
      event.preventDefault();
      const url = input.value.trim();

      if (!url) {
        showPopup("Career URL Required", "Please enter a valid career page URL.", "warning");
        return;
      }

      setLoading(button, true, "Scraping Jobs...");

      try {
        const formData = new FormData();
        formData.append("action", "scrape_jobs");
        formData.append("career_url", url);

        const result = await apiRequest("scrape_jobs", formData);

        if (apiSuccess(result)) {
          state.careerUrl = url;
          state.careerJobs = Array.isArray(result.jobs) ? result.jobs : Array.isArray(result.data?.jobs) ? result.data.jobs : [];
          state.targetCompany = result.company || result.data?.company || state.targetCompany;

          if (result.required_skills) {
            state.requiredSkills = normalizeSkills(result.required_skills);
          } else if (result.data?.required_skills) {
            state.requiredSkills = normalizeSkills(result.data.required_skills);
          }

          if (result.recommended_job) {
            state.recommendedJob = result.recommended_job;
          }

          renderJobs();
          renderSkillGap();
          updateRecommendation();
          renderDashboardCharts();

          showPopup("Career Page Scraped", `Successfully analyzed job opportunities from ${state.targetCompany || "the target page"}.`, "success");
        } else {
          throw new Error(result.message || "Failed to analyze career page.");
        }
      } catch (error) {
        showPopup("Scraper Failed", error.message || "Unable to extract career details from the provided link.", "error");
      } finally {
        setLoading(button, false);
      }
    });
  }

  /* ============================================================
     RESUME UPLOAD & SAMPLE LOADER (REPLACED CORRECTLY)
     ============================================================ */
  function initResumeUpload() {
    const uploadForm = document.getElementById("form-resume-upload");
    const fileInput = document.getElementById("resume-file") || document.getElementById("input-resume-file");
    const sampleBtn = document.getElementById("btn-load-sample-resume");
    const statusBox = document.getElementById("resume-upload-status");
    const selectBtn = document.getElementById("resume-select-button");
    const dropZone = document.getElementById("resume-drop-zone");
    const fileNameDisplay = document.getElementById("resume-file-name");

    if (!uploadForm || !fileInput) {
      return;
    }

    if (selectBtn) {
      selectBtn.addEventListener("click", function (e) {
        e.preventDefault();
        fileInput.click();
      });
    }

    if (dropZone) {
      ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, function (e) {
          e.preventDefault();
          e.stopPropagation();
          dropZone.classList.add("dragover");
        });
      });

      ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, function (e) {
          e.preventDefault();
          e.stopPropagation();
          dropZone.classList.remove("dragover");
        });
      });

      dropZone.addEventListener("drop", function (e) {
        if (e.dataTransfer && e.dataTransfer.files.length) {
          fileInput.files = e.dataTransfer.files;
          if (fileNameDisplay) {
            fileNameDisplay.textContent = "Selected: " + e.dataTransfer.files[0].name;
          }
        }
      });
    }

    fileInput.addEventListener("change", function () {
      if (fileNameDisplay && fileInput.files && fileInput.files.length) {
        fileNameDisplay.textContent = "Selected: " + fileInput.files[0].name;
      }
    });

    uploadForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      const file = fileInput.files && fileInput.files.length ? fileInput.files[0] : null;

      if (!file) {
        showPopup("Resume Required", "Please select a resume PDF or DOCX file first.", "warning");
        return;
      }

      // ----------------------------------------------------
      // Validate file type
      // ----------------------------------------------------
      const fileName = String(file.name || "").toLowerCase();
      const validExtension = fileName.endsWith(".pdf") || fileName.endsWith(".docx") || fileName.endsWith(".txt") || fileName.endsWith(".doc");

      if (!validExtension) {
        showPopup("Invalid Resume", "Please upload a PDF, DOCX, or TXT resume.", "warning");
        return;
      }

      // ----------------------------------------------------
      // Validate file size
      // ----------------------------------------------------
      if (file.size <= 0) {
        showPopup("Invalid Resume", "The selected resume file is empty.", "error");
        return;
      }

      if (file.size > 15 * 1024 * 1024) {
        showPopup("File Too Large", "Please upload a resume smaller than 15 MB.", "warning");
        return;
      }

      // ----------------------------------------------------
      // Status UI
      // ----------------------------------------------------
      if (statusBox) {
        statusBox.className = "alert alert-info";
        statusBox.textContent = "Extracting skills and evaluating ATS compatibility...";
        statusBox.style.display = "block";
      }

      const evaluateButton = document.getElementById("evaluate-resume") || document.querySelector('#form-resume-upload button[type="submit"]');
      setLoading(evaluateButton, true, "Analyzing Resume...");

      // ----------------------------------------------------
      // Send both resume_file and resume for maximum compatibility
      // ----------------------------------------------------
      const formData = new FormData();
      formData.append("action", "upload_resume");
      formData.append("resume_file", file);
      formData.append("resume", file);

      // ----------------------------------------------------
      // Send currently selected career information only.
      // No hard-coded company or role.
      // ----------------------------------------------------
      if (window.CAREER_URL && String(window.CAREER_URL).trim() !== "") {
        formData.append("career_url", String(window.CAREER_URL).trim());
      }

      if (window.REQUIRED_SKILLS && Array.isArray(window.REQUIRED_SKILLS)) {
        formData.append("required_skills", JSON.stringify(window.REQUIRED_SKILLS));
      }

      try {
        const response = await fetch("api.php", {
          method: "POST",
          body: formData,
          credentials: "same-origin",
          cache: "no-store"
        });

        const responseText = await response.text();
        let result;

        try {
          result = JSON.parse(responseText);
        } catch (jsonError) {
          console.error("Resume upload returned invalid JSON:", responseText);
          throw new Error("The server returned an invalid response while processing the resume.");
        }

        console.log("Resume upload response:", result);

        // ------------------------------------------------
        // Backend success
        // ------------------------------------------------
        if (result.success === true || result.status === "success" || result.ok === true) {
          // Extract returned skills
          state.extractedSkills = normalizeSkills(
            result.extracted_skills || result.skills || (result.data && result.data.extracted_skills) || []
          );

          // Required skills
          state.requiredSkills = normalizeSkills(
            result.required_skills || (result.data && result.data.required_skills) || state.requiredSkills || []
          );

          // ATS score
          state.atsScore = Number(result.ats_score || (result.data && result.data.ats_score) || 0);

          // Recommended job
          if (result.recommended_job) {
            state.recommendedJob = result.recommended_job;
          }
          if (result.data && result.data.recommended_job) {
            state.recommendedJob = result.data.recommended_job;
          }

          // Career jobs
          if (Array.isArray(result.jobs)) {
            state.careerJobs = result.jobs;
          }
          if (result.data && Array.isArray(result.data.jobs)) {
            state.careerJobs = result.data.jobs;
          }

          // Resume contact information
          if (result.resume) {
            updateResumeContact(result.resume);
          }
          if (result.data && result.data.resume) {
            updateResumeContact(result.data.resume);
          }

          // --------------------------------------------
          // Refresh existing application UI
          // --------------------------------------------
          renderATS();
          renderExtractedSkills();
          renderSkillGap();
          renderJobs();
          updateRecommendation();
          updateStats();
          renderDashboardCharts();

          if (statusBox) {
            statusBox.className = "alert alert-success";
            statusBox.textContent = "Resume parsed and recorded successfully.";
            statusBox.style.display = "block";
          }

          showPopup("Resume Analyzed", "Your resume has been successfully processed.", "success");
          return;
        }

        // ------------------------------------------------
        // Backend returned an error
        // ------------------------------------------------
        const errorMessage = result.message || result.error || "Unable to analyze the resume.";
        console.error("Resume analysis error:", result);

        if (statusBox) {
          statusBox.className = "alert alert-error";
          statusBox.textContent = errorMessage;
          statusBox.style.display = "block";
        }

        showPopup("Resume Analysis Failed", errorMessage, "error");
      } catch (error) {
        console.error("Resume upload exception:", error);
        const message = error && error.message ? error.message : "Unable to connect to the server.";

        if (statusBox) {
          statusBox.className = "alert alert-error";
          statusBox.textContent = message;
          statusBox.style.display = "block";
        }

        showPopup("Resume Analysis Failed", message, "error");
      } finally {
        setLoading(evaluateButton, false);
      }
    });

    // ========================================================
    // SAMPLE PROFILE BUTTON
    // Keep existing functionality
    // ========================================================
    if (sampleBtn) {
      sampleBtn.addEventListener("click", async function () {
        if (statusBox) {
          statusBox.className = "alert alert-info";
          statusBox.textContent = "Loading sample profile...";
          statusBox.style.display = "block";
        }

        try {
          const response = await fetch("api.php?action=load_sample", {
            method: "GET",
            credentials: "same-origin",
            cache: "no-store"
          });

          const result = await response.json();

          if (result.success === true || result.status === "success" || result.ok === true) {
            window.location.reload();
          } else {
            const message = result.message || "Unable to load sample profile.";

            if (statusBox) {
              statusBox.className = "alert alert-error";
              statusBox.textContent = message;
            }

            showPopup("Sample Profile Failed", message, "error");
          }
        } catch (error) {
          console.error("Sample profile error:", error);
          showPopup("Sample Profile Failed", "Unable to load the sample profile.", "error");
        }
      });
    }
  }

  function updateResumeContact(contact) {
    if (!contact) return;
    if ($("profile-email") && contact.email) $("profile-email").textContent = contact.email;
    if ($("profile-phone") && contact.phone) $("profile-phone").textContent = contact.phone;
    if ($("profile-name") && contact.name) $("profile-name").textContent = contact.name;
  }

  /* ========================================================
     UI RENDERERS & UPDATERS
     ======================================================== */
  function renderATS() {
    const scoreElement = $("ats-score-value");
    const fillElement = $("ats-progress-fill");
    const gaugeElement = $("ats-gauge");

    const score = Math.max(0, Math.min(100, Math.round(state.atsScore || 0)));

    if (scoreElement) scoreElement.textContent = score + "%";
    if (fillElement) fillElement.style.width = score + "%";
    if (gaugeElement) {
      gaugeElement.style.setProperty("--score", score);
      gaugeElement.dataset.score = score;
    }
  }

  function renderExtractedSkills() {
    const container = $("extracted-skills-container");
    if (!container) return;

    if (!state.extractedSkills.length) {
      container.innerHTML = `<p class="empty-state">No skills extracted yet. Upload a resume to analyze.</p>`;
      return;
    }

    container.innerHTML = state.extractedSkills
      .map(
        (skill) => `<span class="badge badge-primary"><i class="fas fa-check-circle"></i> ${escapeHtml(skill)}</span>`
      )
      .join(" ");
  }

  function renderSkillGap() {
    const missingContainer = $("missing-skills-container");
    const matchedContainer = $("matched-skills-container");

    const userSkills = state.extractedSkills.map((s) => s.toLowerCase());
    const required = state.requiredSkills;

    const matched = [];
    const missing = [];

    required.forEach((req) => {
      if (userSkills.includes(req.toLowerCase())) {
        matched.push(req);
      } else {
        missing.push(req);
      }
    });

    if (matchedContainer) {
      if (matched.length) {
        matchedContainer.innerHTML = matched
          .map((s) => `<span class="badge badge-success"><i class="fas fa-check"></i> ${escapeHtml(s)}</span>`)
          .join(" ");
      } else {
        matchedContainer.innerHTML = `<p class="empty-state">No matching skills found.</p>`;
      }
    }

    if (missingContainer) {
      if (missing.length) {
        missingContainer.innerHTML = missing
          .map((s) => `<span class="badge badge-warning"><i class="fas fa-exclamation-triangle"></i> ${escapeHtml(s)}</span>`)
          .join(" ");
      } else {
        missingContainer.innerHTML = `<p class="empty-state">Great job! No critical skills missing.</p>`;
      }
    }
  }

  function renderJobs() {
    const container = $("jobs-list-container");
    if (!container) return;

    if (!state.careerJobs.length) {
      container.innerHTML = `<div class="empty-card"><p>No dynamic job offers loaded yet. Paste a Career URL to extract listings.</p></div>`;
      return;
    }

    container.innerHTML = state.careerJobs
      .map((job) => {
        const title = escapeHtml(job.title || job.role || "Role");
        const company = escapeHtml(job.company || state.targetCompany || "Company");
        const location = escapeHtml(job.location || "Remote / Onsite");
        const url = job.url || state.careerUrl || "#";

        return `
        <div class="job-card">
          <div class="job-header">
            <h4>${title}</h4>
            <span class="company-badge">${company}</span>
          </div>
          <p class="job-location"><i class="fas fa-map-marker-alt"></i> ${location}</p>
          <div class="job-actions">
            <a href="${escapeHtml(url)}" target="_blank" rel="noopener" class="btn btn-sm btn-outline">View Details</a>
          </div>
        </div>
      `;
      })
      .join("");
  }

  function updateRecommendation() {
    const recBox = $("recommended-job-box");
    if (!recBox) return;

    if (!state.recommendedJob) {
      recBox.innerHTML = `<p class="empty-state">Analyzing career target for best matched role...</p>`;
      return;
    }

    const job = state.recommendedJob;
    recBox.innerHTML = `
      <div class="recommendation-card">
        <h3><i class="fas fa-star text-gold"></i> Best Match: ${escapeHtml(job.title || "Target Role")}</h3>
        <p><strong>Match Score:</strong> ${Math.round(job.match_score || state.atsScore || 0)}%</p>
        <p>${escapeHtml(job.description || "Matches your current profile requirements.")}</p>
      </div>
    `;
  }

  function updateStats() {
    if ($("stat-ats-score")) $("stat-ats-score").textContent = Math.round(state.atsScore || 0) + "%";
    if ($("stat-skills-count")) $("stat-skills-count").textContent = state.extractedSkills.length;
    if ($("stat-jobs-count")) $("stat-jobs-count").textContent = state.careerJobs.length;
  }

  /* ========================================================
     CHARTS
     ======================================================== */
  function renderDashboardCharts() {
    if (typeof Chart === "undefined") return;

    const radarCtx = $("chart-radar")?.getContext("2d");
    const pieCtx = $("chart-pie")?.getContext("2d");

    if (radarCtx) {
      if (state.charts.radar) state.charts.radar.destroy();

      const userSkills = state.extractedSkills.map((s) => s.toLowerCase());
      const labels = state.requiredSkills.slice(0, 6);
      const dataValues = labels.map((req) => (userSkills.includes(req.toLowerCase()) ? 90 : 30));

      state.charts.radar = new Chart(radarCtx, {
        type: "radar",
        data: {
          labels: labels.length ? labels : ["Skill A", "Skill B", "Skill C", "Skill D"],
          datasets: [
            {
              label: "Required Match Proficiency",
              data: dataValues.length ? dataValues : [50, 50, 50, 50],
              backgroundColor: "rgba(99, 102, 241, 0.2)",
              borderColor: "#6366f1",
              pointBackgroundColor: "#6366f1"
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false
        }
      });
    }

    if (pieCtx) {
      if (state.charts.pie) state.charts.pie.destroy();

      const userSkills = state.extractedSkills.map((s) => s.toLowerCase());
      let matchedCount = 0;
      let missingCount = 0;

      state.requiredSkills.forEach((req) => {
        if (userSkills.includes(req.toLowerCase())) matchedCount++;
        else missingCount++;
      });

      if (matchedCount === 0 && missingCount === 0) {
        matchedCount = 1;
        missingCount = 1;
      }

      state.charts.pie = new Chart(pieCtx, {
        type: "doughnut",
        data: {
          labels: ["Skills Acquired", "Skills Needed"],
          datasets: [
            {
              data: [matchedCount, missingCount],
              backgroundColor: ["#10b981", "#f59e0b"]
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false
        }
      });
    }
  }

  function updateChartsTheme() {
    if (state.charts.radar || state.charts.pie) {
      renderDashboardCharts();
    }
  }

  /* ========================================================
     DYNAMIC ROADMAP, INTERVIEW & RANKINGS
     ======================================================== */
  async function loadDynamicRoadmap() {
    const container = $("roadmap-content");
    if (!container) return;

    container.innerHTML = `<div class="loader-spinner">Generating personalized learning roadmap...</div>`;

    try {
      const result = await apiRequest("get_roadmap", {}, { method: "GET" });
      if (apiSuccess(result) && result.roadmap) {
        container.innerHTML = renderRoadmapSteps(result.roadmap);
      } else {
        container.innerHTML = `<p>Upload a resume and set a career goal to generate an AI roadmap.</p>`;
      }
    } catch (e) {
      container.innerHTML = `<p>Error loading roadmap. Please try again later.</p>`;
    }
  }

  function renderRoadmapSteps(roadmap) {
    if (!Array.isArray(roadmap)) return `<p>${escapeHtml(roadmap)}</p>`;
    return roadmap
      .map(
        (step, index) => `
      <div class="roadmap-step">
        <div class="step-number">${index + 1}</div>
        <div class="step-details">
          <h4>${escapeHtml(step.title || step.step || "Step " + (index + 1))}</h4>
          <p>${escapeHtml(step.description || step.details || "")}</p>
        </div>
      </div>
    `
      )
      .join("");
  }

  async function loadDynamicInterview() {
    const container = $("interview-content");
    if (!container) return;

    container.innerHTML = `<div class="loader-spinner">Preparing role-specific interview questions...</div>`;

    try {
      const result = await apiRequest("get_interview_qs", {}, { method: "GET" });
      if (apiSuccess(result) && result.questions) {
        container.innerHTML = renderInterviewQuestions(result.questions);
      } else {
        container.innerHTML = `<p>Complete profile analysis to unlock targeted interview preparation.</p>`;
      }
    } catch (e) {
      container.innerHTML = `<p>Error loading interview questions.</p>`;
    }
  }

  function renderInterviewQuestions(qsList) {
    if (!Array.isArray(qsList)) return `<p>${escapeHtml(qsList)}</p>`;
    return qsList
      .map(
        (item, idx) => `
      <div class="faq-item">
        <h4 class="faq-question">Q${idx + 1}: ${escapeHtml(item.question || item.q || "Interview Question")}</h4>
        <div class="faq-answer"><p>${escapeHtml(item.answer || item.a || "Focus on demonstrating core concepts.")}</p></div>
      </div>
    `
      )
      .join("");
  }

  async function loadRankedJobs() {
    const container = $("ranked-jobs-container");
    if (!container) return;

    renderJobs();
  }

  function updateReport() {
    const reportBox = $("report-summary-box");
    if (!reportBox) return;

    reportBox.innerHTML = `
      <div class="report-card">
        <h3>Career Analysis Report</h3>
        <p><strong>Candidate:</strong> ${escapeHtml(state.user?.name || "User Profile")}</p>
        <p><strong>ATS Compatibility Score:</strong> ${Math.round(state.atsScore)}%</p>
        <p><strong>Total Extracted Skills:</strong> ${state.extractedSkills.length}</p>
        <p><strong>Target Opportunities:</strong> ${state.careerJobs.length} Positions Analyzed</p>
      </div>
    `;
  }

  /* ========================================================
     APPLICATION INITIALIZATION
     ======================================================== */
  function initApp() {
    initTheme();
    initSidebar();
    initAuth();
    initNavigation();
    initWebScraper();
    initResumeUpload();

    renderATS();
    renderExtractedSkills();
    renderSkillGap();
    renderJobs();
    updateRecommendation();
    updateStats();
    renderDashboardCharts();
  }

  initApp();
});