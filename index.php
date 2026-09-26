<?php

/* ============================================================
   SESSION CONFIGURATION
   ============================================================ */

/*
 * Prevent the browser/proxy from displaying an old login page
 * after successful authentication.
 */
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Cache-Control: post-check=0, pre-check=0', false);
header('Pragma: no-cache');
header('Expires: 0');


$isHttps =
    (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
    ||
    (isset($_SERVER['HTTP_X_FORWARDED_PROTO'])
        && strtolower((string)$_SERVER['HTTP_X_FORWARDED_PROTO']) === 'https');


if (session_status() === PHP_SESSION_NONE) {

    session_set_cookie_params([
        'lifetime' => 0,
        'path' => '/',
        'domain' => '',
        'secure' => $isHttps,
        'httponly' => true,
        'samesite' => 'Lax'
    ]);

    session_start();
}


/*
 * Keep the authenticated session active.
 */
if (session_status() === PHP_SESSION_ACTIVE) {
    $_SESSION['last_activity'] = time();
}


require_once __DIR__ . '/db.php';


/* ============================================================
   HELPERS
   ============================================================ */

function h($value) {
    return htmlspecialchars((string)$value, ENT_QUOTES, 'UTF-8');
}


function safeArray($value) {
    return is_array($value) ? $value : [];
}


function formatSocialUrl($url) {

    $url = trim((string)$url);

    if ($url === '') {
        return '';
    }

    if (!preg_match('/^https?:\/\//i', $url)) {
        $url = 'https://' . $url;
    }

    return $url;
}


/* ============================================================
   CURRENT USER
   ============================================================ */

$user = null;


/*
 * Primary authentication source:
 * use the authenticated user stored by api.php.
 *
 * This is intentionally checked before getCurrentUser()
 * so a successful login is not lost during redirect.
 */

if (
    isset($_SESSION['user']) &&
    is_array($_SESSION['user']) &&
    !empty($_SESSION['user'])
) {

    $user = $_SESSION['user'];

    /*
     * Keep authentication flags synchronized.
     */

    $_SESSION['logged_in'] = true;

    if (isset($user['id'])) {
        $_SESSION['user_id'] = (int)$user['id'];
    }
}


/*
 * Backward compatibility:
 * If no authenticated session user exists, use the existing
 * database helper when available.
 */

if (!$user && function_exists('getCurrentUser')) {

    try {

        $currentUser = getCurrentUser();

        if (
            is_array($currentUser) &&
            !empty($currentUser)
        ) {

            $user = $currentUser;

            /*
             * Synchronize the session.
             */

            $_SESSION['user'] = $user;
            $_SESSION['logged_in'] = true;

            if (isset($user['id'])) {
                $_SESSION['user_id'] = (int)$user['id'];
            }
        }

    } catch (Throwable $e) {

        $user = null;
    }
}


/* ============================================================
   SESSION DATA
   ============================================================ */

$careerUrl =
    $_SESSION['career_url'] ?? '';


$targetCompany =
    $_SESSION['target_company'] ?? '';


$targetRole =
    $_SESSION['target_role'] ?? '';


$requiredSkills = safeArray(
    $_SESSION['required_skills'] ?? []
);


$extractedSkills = safeArray(
    $_SESSION['extracted_skills'] ?? []
);


$atsScore = (float)(
    $_SESSION['ats_score'] ?? 0
);


$recommendedJob =
    $_SESSION['recommended_job'] ?? null;


$careerJobs = safeArray(
    $_SESSION['career_jobs'] ?? []
);


/* ============================================================
   RESUME DATA
   ============================================================ */

$resumeName =
    $_SESSION['resume_name'] ?? '';


$resumeEmail =
    $_SESSION['resume_email'] ?? '';


$resumePhone =
    $_SESSION['resume_phone'] ?? '';


$resumeLinkedin =
    $_SESSION['resume_linkedin'] ?? '';


$resumeGithub =
    $_SESSION['resume_github'] ?? '';


/* ============================================================
   RESUME HISTORY
   ============================================================ */

$resumeHistory = [];


if (
    $user &&
    function_exists('getResumeHistoryForStudent')
) {

    try {

        $resumeHistory = safeArray(
            getResumeHistoryForStudent(
                $user['id'] ?? null
            )
        );

    } catch (Throwable $e) {

        $resumeHistory = [];
    }
}


/* ============================================================
   APP DATA FOR JAVASCRIPT
   ============================================================ */

$appData = [

    'loggedIn' =>
        (bool)$user,

    'user' =>
        $user,

    'careerUrl' =>
        $careerUrl,

    'targetCompany' =>
        $targetCompany,

    'targetRole' =>
        $targetRole,

    'requiredSkills' =>
        $requiredSkills,

    'extractedSkills' =>
        $extractedSkills,

    'atsScore' =>
        $atsScore,

    'recommendedJob' =>
        $recommendedJob,

    'careerJobs' =>
        $careerJobs
];

?>
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">


    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >


    <meta
        http-equiv="Cache-Control"
        content="no-cache, no-store, must-revalidate"
    >


    <meta
        http-equiv="Pragma"
        content="no-cache"
    >


    <meta
        http-equiv="Expires"
        content="0"
    >


    <title>
        Skill-Gap Predictor
    </title>


    <link
        rel="stylesheet"
        href="static/styles.css?v=<?php echo time(); ?>"
    >


    <script>

        window.APP_DATA = <?php

            echo json_encode(
                $appData,

                JSON_UNESCAPED_SLASHES |
                JSON_UNESCAPED_UNICODE |
                JSON_HEX_TAG |
                JSON_HEX_AMP |
                JSON_HEX_APOS |
                JSON_HEX_QUOT
            );

        ?>;


        window.USER_LOGGED_IN =
            <?php echo $user ? 'true' : 'false'; ?>;


        window.BENCHMARK_DATA = [];


    </script>


    <script
        src="https://cdn.jsdelivr.net/npm/chart.js"
    ></script>

</head>


<body>


<!-- ============================================================
     PAGE LOADER
     ============================================================ -->

<div
    id="page-loader"
    class="page-loader"
>

    <div class="loader-card">

        <div class="loader-ring"></div>

        <div class="loader-title">
            Skill-Gap Predictor
        </div>

        <div class="loader-text">
            Loading Career Navigation AI...
        </div>

    </div>

</div>


<?php if (!$user): ?>


<!-- ============================================================
     AUTH SCREEN
     ============================================================ -->

<div
    id="auth-screen"
    class="auth-screen"
>

    <div class="auth-container">


        <div class="auth-brand">

            <div class="brand-logo">
                SG
            </div>

            <div>

                <h1>
                    Skill-Gap Predictor
                </h1>

                <p>
                    Career Navigation & Skill Analysis
                </p>

            </div>

        </div>


        <div class="auth-card">


            <!-- AUTH TABS -->

            <div class="auth-tabs">

                <button
                    type="button"
                    id="tab-btn-login"
                    class="auth-tab active"
                    data-auth-tab="login"
                >
                    Login
                </button>


                <button
                    type="button"
                    id="tab-btn-signup"
                    class="auth-tab"
                    data-auth-tab="signup"
                >
                    Create Account
                </button>

            </div>


            <!-- ====================================================
                 LOGIN
                 ==================================================== -->

            <div
                id="form-login-box"
                class="auth-panel active"
            >

                <div class="auth-heading">

                    <h2>
                        Welcome Back
                    </h2>

                    <p>
                        Sign in to continue your career analysis.
                    </p>

                </div>


                <div
                    id="login-error-msg"
                    class="auth-message error"
                    style="display:none;"
                ></div>


                <div
                    id="login-success-msg"
                    class="auth-message success"
                    style="display:none;"
                ></div>


                <form id="form-login">


                    <div class="form-group">

                        <label for="login_email">
                            Email Address
                        </label>

                        <input
                            type="email"
                            id="login_email"
                            name="email"
                            placeholder="Enter your email"
                            autocomplete="email"
                            required
                        >

                    </div>


                    <div class="form-group">

                        <label for="login_password">
                            Password
                        </label>


                        <div class="password-field">

                            <input
                                type="password"
                                id="login_password"
                                name="password"
                                placeholder="Enter your password"
                                autocomplete="current-password"
                                required
                            >


                            <button
                                type="button"
                                class="password-toggle"
                                data-password-target="login_password"
                                aria-label="Show password"
                            >
                                Show
                            </button>

                        </div>

                    </div>


                    <button
                        type="submit"
                        id="btn-do-login"
                        class="primary-button auth-submit"
                    >
                        Login
                    </button>


                </form>

            </div>


            <!-- ====================================================
                 SIGNUP
                 ==================================================== -->

            <div
                id="form-signup-box"
                class="auth-panel"
            >

                <div class="auth-heading">

                    <h2>
                        Create Account
                    </h2>

                    <p>
                        Create your account to start your career analysis.
                    </p>

                </div>


                <div
                    id="signup-error-msg"
                    class="auth-message error"
                    style="display:none;"
                ></div>


                <div
                    id="signup-success-msg"
                    class="auth-message success"
                    style="display:none;"
                ></div>


                <form id="form-signup">


                    <div class="form-group">

                        <label for="signup_name">
                            Full Name
                        </label>

                        <input
                            type="text"
                            id="signup_name"
                            name="name"
                            placeholder="Enter your full name"
                            required
                        >

                    </div>


                    <div class="form-group">

                        <label for="signup_email">
                            Email Address
                        </label>

                        <input
                            type="email"
                            id="signup_email"
                            name="email"
                            placeholder="Enter your email"
                            autocomplete="email"
                            required
                        >

                    </div>


                    <div class="form-group">

                        <label for="signup_pwd">
                            Password
                        </label>


                        <div class="password-field">

                            <input
                                type="password"
                                id="signup_pwd"
                                name="password"
                                placeholder="Create a password"
                                autocomplete="new-password"
                                required
                            >


                            <button
                                type="button"
                                class="password-toggle"
                                data-password-target="signup_pwd"
                                aria-label="Show password"
                            >
                                Show
                            </button>

                        </div>

                    </div>


                    <div class="form-row">


                        <div class="form-group">

                            <label for="signup_uni">
                                University
                            </label>

                            <input
                                type="text"
                                id="signup_uni"
                                name="university"
                                placeholder="University"
                            >

                        </div>


                        <div class="form-group">

                            <label for="signup_branch">
                                Branch
                            </label>

                            <input
                                type="text"
                                id="signup_branch"
                                name="branch"
                                placeholder="Branch"
                            >

                        </div>


                    </div>


                    <div class="form-row">


                        <div class="form-group">

                            <label for="signup_major">
                                Specialization
                            </label>

                            <input
                                type="text"
                                id="signup_major"
                                name="major"
                                placeholder="Specialization"
                            >

                        </div>


                        <div class="form-group">

                            <label for="signup_gradyear">
                                Graduation Year
                            </label>

                            <input
                                type="number"
                                id="signup_gradyear"
                                name="gradyear"
                                placeholder="2027"
                                min="2000"
                                max="2100"
                            >

                        </div>


                    </div>


                    <div class="form-group">

                        <label for="signup_linkedin">
                            LinkedIn Profile
                        </label>

                        <input
                            type="url"
                            id="signup_linkedin"
                            name="linkedin"
                            placeholder="https://linkedin.com/in/your-profile"
                        >

                    </div>


                    <div class="form-group">

                        <label for="signup_github">
                            GitHub Profile
                        </label>

                        <input
                            type="url"
                            id="signup_github"
                            name="github"
                            placeholder="https://github.com/your-profile"
                        >

                    </div>


                    <div class="terms-row">

                        <label>

                            <input
                                type="checkbox"
                                id="signup-terms"
                                required
                            >

                            <span>
                                I agree to the terms and conditions.
                            </span>

                        </label>

                    </div>


                    <button
                        type="submit"
                        id="btn-do-signup"
                        class="primary-button auth-submit"
                    >
                        Create Account
                    </button>


                </form>

            </div>

        </div>

    </div>

</div>


<?php else: ?>


<!-- ============================================================
     APPLICATION SHELL
     ============================================================ -->

<div
    id="app-shell"
    class="app-shell"
>


    <!-- ========================================================
         SIDEBAR
         ======================================================== -->

    <aside
        id="app-sidebar"
        class="app-sidebar"
    >


        <div class="sidebar-header">

            <div class="sidebar-brand">

                <div class="brand-logo small">
                    SG
                </div>

                <div>

                    <strong>
                        Skill-Gap
                    </strong>

                    <span>
                        Predictor
                    </span>

                </div>

            </div>


            <button
                type="button"
                id="sidebar-close"
                class="sidebar-close"
                aria-label="Close sidebar"
            >
                ×
            </button>

        </div>


        <div class="sidebar-user">

            <div class="user-avatar">

                <?php

                $userName =
                    $user['name'] ?? 'User';

                echo h(
                    strtoupper(
                        substr(
                            trim($userName),
                            0,
                            1
                        )
                    )
                );

                ?>

            </div>


            <div class="user-info">

                <strong>
                    <?php echo h($userName); ?>
                </strong>

                <span>
                    <?php
                    echo h(
                        $user['email'] ?? ''
                    );
                    ?>
                </span>

            </div>

        </div>


        <nav class="sidebar-nav">


            <button
                type="button"
                class="nav-item active"
                data-view="dashboard"
            >
                <span class="nav-icon">⌂</span>
                <span>Dashboard</span>
            </button>


            <button
                type="button"
                class="nav-item"
                data-view="resume"
            >
                <span class="nav-icon">▣</span>
                <span>ATS & Resume Parser</span>
            </button>


            <button
                type="button"
                class="nav-item"
                data-view="skillgap"
            >
                <span class="nav-icon">◈</span>
                <span>Skill Gap</span>
            </button>


            <button
                type="button"
                class="nav-item"
                data-view="jobs"
            >
                <span class="nav-icon">▤</span>
                <span>Career Jobs</span>
            </button>


            <button
                type="button"
                class="nav-item"
                data-view="roadmap"
            >
                <span class="nav-icon">➜</span>
                <span>Roadmap</span>
            </button>


            <button
                type="button"
                class="nav-item"
                data-view="interview"
            >
                <span class="nav-icon">?</span>
                <span>Interview</span>
            </button>


            <button
                type="button"
                class="nav-item"
                data-view="report"
            >
                <span class="nav-icon">▧</span>
                <span>Report</span>
            </button>


            <button
                type="button"
                class="nav-item"
                data-view="profile"
            >
                <span class="nav-icon">◉</span>
                <span>Profile</span>
            </button>


        </nav>


        <div class="sidebar-footer">


            <button
                type="button"
                id="sidebar-theme-toggle"
                class="theme-button"
            >

                <span id="theme-icon">
                    ☾
                </span>

                <span id="theme-text">
                    Dark Mode
                </span>

            </button>


            <button
                type="button"
                id="btn-logout"
                class="logout-button"
            >

                <span>
                    ↪
                </span>

                <span>
                    Logout
                </span>

            </button>


        </div>


    </aside>


    <div
        id="sidebar-overlay"
        class="sidebar-overlay"
    ></div>


    <!-- ========================================================
         MAIN
         ======================================================== -->

    <main class="app-main">


        <header class="topbar">


            <div class="topbar-left">


                <button
                    type="button"
                    id="mobile-menu-toggle"
                    class="mobile-menu-toggle"
                    aria-label="Open menu"
                >
                    ☰
                </button>


                <div class="page-heading">

                    <h1 id="page-title">
                        Dashboard
                    </h1>

                    <p id="page-subtitle">
                        Analyze your skills against live career opportunities.
                    </p>

                </div>


            </div>


            <div class="topbar-right">


                <button
                    type="button"
                    id="top-theme-toggle"
                    class="top-theme-toggle"
                    aria-label="Toggle theme"
                >
                    ☾
                </button>


            </div>


        </header>


        <div class="page-content">


            <!-- ==================================================
                 DASHBOARD
                 ================================================== -->

            <section
                id="view-dashboard"
                class="view-panel active"
            >


                <div class="welcome-banner">

                    <div>

                        <span class="eyebrow">
                            CAREER NAVIGATION
                        </span>

                        <h2>
                            Find the skills you need for your target career.
                        </h2>

                        <p>
                            Enter a career or jobs URL to fetch live opportunities,
                            then upload your resume to identify skill gaps.
                        </p>

                    </div>

                </div>


                <div class="content-card career-source-card">


                    <div class="card-header">

                        <div>

                            <h3>
                                Career Source
                            </h3>

                            <p>
                                Enter the URL of a career or jobs page.
                            </p>

                        </div>

                    </div>


                    <div class="career-url-row">

                        <input
                            type="url"
                            id="career-url"
                            value="<?php echo h($careerUrl); ?>"
                            placeholder="https://example.com/careers"
                        >


                        <button
                            type="button"
                            id="scrape-career-url"
                            class="primary-button"
                        >
                            Fetch Jobs
                        </button>

                    </div>


                    <div
                        id="career-url-status"
                        class="inline-status"
                    ></div>


                </div>


                <div class="metrics-grid">


                    <div class="metric-card">

                        <span class="metric-label">
                            ATS Score
                        </span>

                        <strong id="metric-ats">
                            <?php
                            echo round($atsScore);
                            ?>%
                        </strong>

                    </div>


                    <div class="metric-card">

                        <span class="metric-label">
                            Skills Found
                        </span>

                        <strong id="metric-skills">
                            <?php
                            echo count($extractedSkills);
                            ?>
                        </strong>

                    </div>


                    <div class="metric-card">

                        <span class="metric-label">
                            Jobs Found
                        </span>

                        <strong id="metric-jobs">
                            <?php
                            echo count($careerJobs);
                            ?>
                        </strong>

                    </div>


                    <div class="metric-card">

                        <span class="metric-label">
                            Best Match
                        </span>

                        <strong id="metric-match">
                            0%
                        </strong>

                    </div>


                </div>


                <div
                    id="recommendation-card"
                    class="content-card recommendation-card"
                >


                    <div class="card-header">

                        <div>

                            <span class="eyebrow">
                                RECOMMENDATION
                            </span>

                            <h3 id="recommended-job">
                                No job recommendation yet
                            </h3>

                            <p id="recommendation-description">
                                Fetch jobs from a career URL and upload your resume
                                to generate a dynamic recommendation.
                            </p>

                        </div>

                    </div>


                </div>


                <div class="dashboard-grid">


                    <div class="content-card">

                        <div class="card-header">

                            <div>

                                <h3>
                                    Skill Overview
                                </h3>

                                <p>
                                    Your extracted skills compared with requirements.
                                </p>

                            </div>

                        </div>


                        <canvas
                            id="skills-chart"
                            height="250"
                        ></canvas>


                    </div>


                    <div class="content-card">

                        <div class="card-header">

                            <div>

                                <h3>
                                    Readiness
                                </h3>

                                <p>
                                    Current career preparation overview.
                                </p>

                            </div>

                        </div>


                        <canvas
                            id="readiness-chart"
                            height="250"
                        ></canvas>


                    </div>


                </div>


            </section>


            <!-- ==================================================
                 RESUME
                 ================================================== -->

            <section
                id="view-resume"
                class="view-panel"
            >


                <div class="section-header">

                    <div>

                        <span class="eyebrow">
                            RESUME ANALYSIS
                        </span>

                        <h2>
                            ATS & Resume Parser
                        </h2>

                        <p>
                            Upload your resume to extract skills and calculate ATS compatibility.
                        </p>

                    </div>

                </div>


                <div class="resume-grid">


                    <div class="content-card">


                        <form
                            id="form-resume-upload"
                            enctype="multipart/form-data"
                        >


                            <div
                                id="resume-drop-zone"
                                class="resume-drop-zone"
                            >


                                <div class="upload-icon">
                                    ↑
                                </div>


                                <h3>
                                    Upload Resume
                                </h3>


                                <p>
                                    PDF or DOCX files supported.
                                </p>


                                <input
                                    type="file"
                                    id="resume-file"
                                    name="resume_file"
                                    accept=".pdf,.doc,.docx,.txt"
                                    hidden
                                >


                                <button
                                    type="button"
                                    id="resume-select-button"
                                    class="secondary-button"
                                >
                                    Choose Resume
                                </button>


                                <div
                                    id="resume-file-name"
                                    class="file-name"
                                ></div>


                            </div>


                            <button
                                type="submit"
                                id="evaluate-resume"
                                class="primary-button full-width"
                            >
                                Analyze Resume
                            </button>


                        </form>


                    </div>


                    <div class="content-card ats-card">


                        <div class="card-header">

                            <div>

                                <h3>
                                    ATS Score
                                </h3>

                            </div>

                        </div>


                        <div class="ats-score-wrapper">

                            <div
                                id="ats-score"
                                class="ats-score"
                            >
                                <?php
                                echo round($atsScore);
                                ?>%
                            </div>

                        </div>


                        <div
                            id="ats-feedback"
                            class="ats-feedback"
                        >
                            Upload your resume to receive ATS feedback.
                        </div>


                    </div>


                </div>


                <div class="content-card">


                    <div class="card-header">

                        <div>

                            <h3>
                                Extracted Contact Information
                            </h3>

                        </div>

                    </div>


                    <div class="contact-grid">


                        <div>

                            <span>
                                Name
                            </span>

                            <strong id="resume-name">
                                <?php echo h($resumeName); ?>
                            </strong>

                        </div>


                        <div>

                            <span>
                                Email
                            </span>

                            <strong id="resume-email">
                                <?php echo h($resumeEmail); ?>
                            </strong>

                        </div>


                        <div>

                            <span>
                                Phone
                            </span>

                            <strong id="resume-phone">
                                <?php echo h($resumePhone); ?>
                            </strong>

                        </div>


                        <div>

                            <span>
                                LinkedIn
                            </span>

                            <strong id="resume-linkedin">
                                <?php echo h($resumeLinkedin); ?>
                            </strong>

                        </div>


                        <div>

                            <span>
                                GitHub
                            </span>

                            <strong id="resume-github">
                                <?php echo h($resumeGithub); ?>
                            </strong>

                        </div>


                    </div>


                </div>


                <div class="content-card">


                    <div class="card-header">

                        <div>

                            <h3>
                                Extracted Skills
                            </h3>

                        </div>

                    </div>


                    <div
                        id="resume-skills-list"
                        class="skills-list"
                    >


                        <?php if (!empty($extractedSkills)): ?>


                            <?php foreach ($extractedSkills as $skill): ?>


                                <span class="skill-tag">
                                    <?php echo h($skill); ?>
                                </span>


                            <?php endforeach; ?>


                        <?php else: ?>


                            <span class="empty-state">
                                No skills extracted yet.
                            </span>


                        <?php endif; ?>


                    </div>


                </div>


            </section>


            <!-- ==================================================
                 SKILL GAP
                 ================================================== -->

            <section
                id="view-skillgap"
                class="view-panel"
            >


                <div class="section-header">

                    <div>

                        <span class="eyebrow">
                            SKILL ANALYSIS
                        </span>

                        <h2>
                            Skill Gap
                        </h2>

                        <p>
                            Compare your resume skills against live job requirements.
                        </p>

                    </div>

                </div>


                <div class="two-column-grid">


                    <div class="content-card">


                        <div class="card-header">

                            <h3>
                                Your Skills
                            </h3>

                        </div>


                        <div
                            id="skillgap-user-skills"
                            class="skills-list"
                        >

                            <span class="empty-state">
                                Upload a resume to extract your skills.
                            </span>

                        </div>


                    </div>


                    <div class="content-card">


                        <div class="card-header">

                            <h3>
                                Required Skills
                            </h3>

                        </div>


                        <div
                            id="skillgap-required-skills"
                            class="skills-list"
                        >

                            <span class="empty-state">
                                Fetch a career URL to identify required skills.
                            </span>

                        </div>


                    </div>


                </div>


                <div class="content-card">


                    <div class="card-header">

                        <div>

                            <h3>
                                Missing Skills
                            </h3>

                            <p>
                                Skills detected in job requirements but not in your resume.
                            </p>

                        </div>

                    </div>


                    <div
                        id="missing-skills-list"
                        class="skills-list"
                    >

                        <span class="empty-state">
                            No skill gap calculated yet.
                        </span>

                    </div>


                </div>


            </section>


            <!-- ==================================================
                 JOBS
                 ================================================== -->

            <section
                id="view-jobs"
                class="view-panel"
            >


                <div class="section-header">

                    <div>

                        <span class="eyebrow">
                            LIVE OPPORTUNITIES
                        </span>

                        <h2>
                            Career Jobs
                        </h2>

                        <p>
                            Jobs discovered from your selected career source.
                        </p>

                    </div>

                </div>


                <div class="content-card">


                    <div class="career-url-row">

                        <input
                            type="url"
                            id="jobs-career-url"
                            value="<?php echo h($careerUrl); ?>"
                            placeholder="Enter career URL"
                        >


                        <button
                            type="button"
                            id="rank-career-jobs"
                            class="primary-button"
                        >
                            Fetch & Rank Jobs
                        </button>

                    </div>


                </div>


                <div
                    id="job-results"
                    class="job-results"
                >


                    <?php if (!empty($careerJobs)): ?>


                        <div class="job-table-wrapper">


                            <table class="job-table">


                                <thead>

                                    <tr>

                                        <th>
                                            Job Role
                                        </th>

                                        <th>
                                            Company
                                        </th>

                                        <th>
                                            Location
                                        </th>

                                        <th>
                                            Match
                                        </th>

                                        <th>
                                            Action
                                        </th>

                                    </tr>

                                </thead>


                                <tbody>


                                <?php foreach ($careerJobs as $job): ?>


                                    <?php

                                    $title =
                                        $job['title']
                                        ?? $job['role']
                                        ?? $job['job_title']
                                        ?? 'Job Opportunity';


                                    $company =
                                        $job['company']
                                        ?? $job['company_name']
                                        ?? '';


                                    $location =
                                        $job['location']
                                        ?? '';


                                    $url =
                                        $job['url']
                                        ?? $job['link']
                                        ?? $job['job_url']
                                        ?? '#';

                                    ?>


                                    <tr>


                                        <td>
                                            <?php echo h($title); ?>
                                        </td>


                                        <td>
                                            <?php echo h($company); ?>
                                        </td>


                                        <td>
                                            <?php echo h($location); ?>
                                        </td>


                                        <td>
                                            —
                                        </td>


                                        <td>


                                            <?php if ($url !== '#'): ?>


                                                <a
                                                    href="<?php echo h($url); ?>"
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    class="job-link"
                                                >
                                                    View Job
                                                </a>


                                            <?php else: ?>


                                                —


                                            <?php endif; ?>


                                        </td>


                                    </tr>


                                <?php endforeach; ?>


                                </tbody>


                            </table>


                        </div>


                    <?php else: ?>


                        <div class="empty-state-card">

                            <h3>
                                No jobs loaded
                            </h3>

                            <p>
                                Enter a career URL above and fetch live jobs to populate this table.
                            </p>

                        </div>


                    <?php endif; ?>


                </div>


            </section>


            <!-- ==================================================
                 ROADMAP
                 ================================================== -->

            <section
                id="view-roadmap"
                class="view-panel"
            >


                <div class="section-header">

                    <div>

                        <span class="eyebrow">
                            CAREER DEVELOPMENT
                        </span>

                        <h2>
                            Learning Roadmap
                        </h2>

                        <p>
                            Build a learning path around your identified skill gaps.
                        </p>

                    </div>

                </div>


                <div
                    id="container-dynamic-roadmap"
                    class="roadmap-container"
                >

                    <div class="empty-state-card">

                        <h3>
                            Roadmap will appear here
                        </h3>

                        <p>
                            Analyze your resume and career source first.
                        </p>

                    </div>

                </div>


                <div
                    id="container-dynamic-resources"
                    class="resources-container"
                ></div>


            </section>


            <!-- ==================================================
                 INTERVIEW
                 ================================================== -->

            <section
                id="view-interview"
                class="view-panel"
            >


                <div class="section-header">

                    <div>

                        <span class="eyebrow">
                            INTERVIEW PREPARATION
                        </span>

                        <h2>
                            Interview Practice
                        </h2>

                        <p>
                            Practice questions based on your career target and skills.
                        </p>

                    </div>

                </div>


                <div class="content-card interview-card">


                    <div
                        id="interview-question"
                        class="interview-question"
                    >
                        Click "Generate Question" to begin.
                    </div>


                    <div class="form-group">

                        <label for="interview-answer">
                            Your Answer
                        </label>


                        <textarea
                            id="interview-answer"
                            rows="7"
                            placeholder="Write your answer here..."
                        ></textarea>


                    </div>


                    <div class="button-row">


                        <button
                            type="button"
                            id="generate-interview-question"
                            class="secondary-button"
                        >
                            Generate Question
                        </button>


                        <button
                            type="button"
                            id="submit-interview-answer"
                            class="primary-button"
                        >
                            Submit Answer
                        </button>


                    </div>


                    <div
                        id="interview-feedback"
                        class="interview-feedback"
                    ></div>


                </div>


                <div class="content-card">


                    <div class="card-header">

                        <div>

                            <h3>
                                AI Career Assistant
                            </h3>

                            <p>
                                Ask questions about your skills, roadmap or interview preparation.
                            </p>

                        </div>

                    </div>


                    <div class="ai-input-row">


                        <textarea
                            id="input-ai-prompt"
                            rows="3"
                            placeholder="Ask your career question..."
                        ></textarea>


                        <button
                            type="button"
                            id="btn-submit-ai-prompt"
                            class="primary-button"
                        >
                            Ask Assistant
                        </button>


                    </div>


                    <div
                        id="ai-assistant-response-card"
                        class="ai-response-card"
                        style="display:none;"
                    >

                        <h3 id="ai-response-title">
                            AI Assistant
                        </h3>

                        <div id="ai-response-body"></div>

                    </div>


                </div>


            </section>


            <!-- ==================================================
                 REPORT
                 ================================================== -->

            <section
                id="view-report"
                class="view-panel"
            >


                <div class="section-header">

                    <div>

                        <span class="eyebrow">
                            CAREER REPORT
                        </span>

                        <h2>
                            Generate Report
                        </h2>

                        <p>
                            Download your current skill-gap analysis.
                        </p>

                    </div>

                </div>


                <div class="content-card report-card">


                    <form
                        id="report-form"
                        method="POST"
                        action="api.php?action=download_pdf"
                    >


                        <input
                            type="hidden"
                            name="career_url"
                            id="report-career-url"
                            value="<?php echo h($careerUrl); ?>"
                        >


                        <button
                            type="submit"
                            class="primary-button"
                        >
                            Download Career Report
                        </button>


                    </form>


                </div>


            </section>


            <!-- ==================================================
                 PROFILE
                 ================================================== -->

            <section
                id="view-profile"
                class="view-panel"
            >


                <div class="section-header">

                    <div>

                        <span class="eyebrow">
                            ACCOUNT
                        </span>

                        <h2>
                            Profile
                        </h2>

                        <p>
                            Update your personal and academic information.
                        </p>

                    </div>

                </div>


                <div class="content-card">


                    <form id="profile-form">


                        <div class="form-row">


                            <div class="form-group">

                                <label for="profile_name">
                                    Full Name
                                </label>

                                <input
                                    type="text"
                                    id="profile_name"
                                    name="name"
                                    value="<?php echo h($user['name'] ?? ''); ?>"
                                    required
                                >

                            </div>


                            <div class="form-group">

                                <label for="profile_email">
                                    Email
                                </label>

                                <input
                                    type="email"
                                    id="profile_email"
                                    name="email"
                                    value="<?php echo h($user['email'] ?? ''); ?>"
                                    readonly
                                >

                            </div>


                        </div>


                        <div class="form-row">


                            <div class="form-group">

                                <label for="profile_university">
                                    University
                                </label>

                                <input
                                    type="text"
                                    id="profile_university"
                                    name="university"
                                    value="<?php echo h($user['university'] ?? ''); ?>"
                                >

                            </div>


                            <div class="form-group">

                                <label for="profile_degree">
                                    Degree
                                </label>

                                <input
                                    type="text"
                                    id="profile_degree"
                                    name="degree"
                                    value="<?php echo h($user['degree'] ?? ''); ?>"
                                >

                            </div>


                        </div>


                        <div class="form-row">


                            <div class="form-group">

                                <label for="profile_major">
                                    Specialization
                                </label>

                                <input
                                    type="text"
                                    id="profile_major"
                                    name="major"
                                    value="<?php echo h($user['major'] ?? ''); ?>"
                                >

                            </div>


                            <div class="form-group">

                                <label for="profile_gradyear">
                                    Graduation Year
                                </label>

                                <input
                                    type="number"
                                    id="profile_gradyear"
                                    name="gradyear"
                                    value="<?php echo h($user['gradyear'] ?? ''); ?>"
                                >

                            </div>


                        </div>


                        <div class="form-row">


                            <div class="form-group">

                                <label for="profile_linkedin">
                                    LinkedIn
                                </label>

                                <input
                                    type="url"
                                    id="profile_linkedin"
                                    name="linkedin"
                                    value="<?php echo h(
                                        formatSocialUrl(
                                            $user['linkedin'] ?? ''
                                        )
                                    ); ?>"
                                >

                            </div>


                            <div class="form-group">

                                <label for="profile_github">
                                    GitHub
                                </label>

                                <input
                                    type="url"
                                    id="profile_github"
                                    name="github"
                                    value="<?php echo h(
                                        formatSocialUrl(
                                            $user['github'] ?? ''
                                        )
                                    ); ?>"
                                >

                            </div>


                        </div>


                        <button
                            type="submit"
                            class="primary-button"
                        >
                            Save Profile
                        </button>


                        <div
                            id="profile-message"
                            class="inline-status"
                        ></div>


                    </form>


                </div>


            </section>


        </div>


    </main>


</div>


<?php endif; ?>


<!-- ============================================================
     JAVASCRIPT
     ============================================================ -->

<script
    src="static/app.js?v=<?php echo time(); ?>"
></script>


</body>

</html>