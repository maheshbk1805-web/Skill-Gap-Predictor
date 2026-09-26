<?php
/**
 * API Handler for Skill-Gap Predictor
 * Project ID: P19 | IEEE CS Bangalore Chapter | GITAM University
 *
 * Dynamic architecture:
 *
 * Career URL
 *      ↓
 * Python scraper
 *      ↓
 * Actual jobs / roles / requirements
 *      ↓
 * PHP fallback scraper
 *      ↓
 * Source-specific career search fallback
 *      ↓
 * Resume upload
 *      ↓
 * Resume skills
 *      ↓
 * Skill matching
 *      ↓
 * Dynamically recommended job role
 *
 * No predefined job role is used.
 */


/* ============================================================
   SESSION CONFIGURATION
   ============================================================ */

$isHttps =
    (
        (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        ||
        (
            isset($_SERVER['HTTP_X_FORWARDED_PROTO'])
            &&
            strtolower($_SERVER['HTTP_X_FORWARDED_PROTO']) === 'https'
        )
    );

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

header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/db.php';


/* ============================================================
   COMMON JSON RESPONSE
   ============================================================ */

function jsonResponse($data, $httpCode = 200)
{
    http_response_code($httpCode);

    echo json_encode(
        $data,
        JSON_UNESCAPED_SLASHES |
        JSON_UNESCAPED_UNICODE
    );

    exit;
}


/* ============================================================
   SAFE TEXT
   ============================================================ */

function cleanText($value)
{
    if ($value === null) {
        return '';
    }

    if (is_array($value)) {
        return '';
    }

    $value = strip_tags((string)$value);

    $value = html_entity_decode(
        $value,
        ENT_QUOTES | ENT_HTML5,
        'UTF-8'
    );

    $value = preg_replace(
        '/\s+/u',
        ' ',
        $value
    );

    return trim($value);
}


/* ============================================================
   PYTHON BRIDGE
   ============================================================ */

function callPythonBridge($action, $payload = [])
{
    $isWindows =
        strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';

    $pythonCommands = $isWindows
        ? ['python', 'python3']
        : ['python3', 'python'];

    $bridgePath =
        __DIR__ . DIRECTORY_SEPARATOR . 'bridge.py';

    if (!file_exists($bridgePath)) {
        return [
            "status" => "error",
            "message" => "Python bridge file was not found."
        ];
    }

    $jsonInput =
        json_encode(
            $payload,
            JSON_UNESCAPED_SLASHES |
            JSON_UNESCAPED_UNICODE
        );

    if ($jsonInput === false) {
        return [
            "status" => "error",
            "message" => "Unable to encode Python bridge input."
        ];
    }

    $descriptorspec = [
        0 => ["pipe", "r"],
        1 => ["pipe", "w"],
        2 => ["pipe", "w"]
    ];

    foreach ($pythonCommands as $pythonCmd) {

        $command =
            escapeshellcmd($pythonCmd) .
            ' ' .
            escapeshellarg($bridgePath) .
            ' ' .
            escapeshellarg($action);

        $process = @proc_open(
            $command,
            $descriptorspec,
            $pipes,
            __DIR__
        );

        if (!is_resource($process)) {
            continue;
        }

        fwrite(
            $pipes[0],
            $jsonInput
        );

        fclose($pipes[0]);

        $output =
            stream_get_contents($pipes[1]);

        fclose($pipes[1]);

        $stderr =
            stream_get_contents($pipes[2]);

        fclose($pipes[2]);

        proc_close($process);

        $decoded =
            json_decode(
                $output,
                true
            );

        if (is_array($decoded)) {
            return $decoded;
        }

        if (!empty($stderr)) {
            return [
                "status" => "error",
                "message" =>
                    "Python bridge error: " .
                    trim($stderr)
            ];
        }
    }

    return [
        "status" => "error",
        "message" =>
            "Could not start the Python bridge process."
    ];
}


/* ============================================================
   SKILL NORMALIZATION
   ============================================================ */

function normalizeSkills($skills)
{
    if ($skills === null) {
        return [];
    }

    if (is_string($skills)) {

        $decoded =
            json_decode(
                $skills,
                true
            );

        if (is_array($decoded)) {
            $skills = $decoded;
        } else {
            $skills =
                preg_split(
                    '/[,;\n|]+/',
                    $skills
                );
        }
    }

    if (!is_array($skills)) {
        return [];
    }

    $result = [];
    $seen = [];

    foreach ($skills as $skill) {

        if (is_array($skill)) {
            $skill =
                $skill['name']
                ?? $skill['skill']
                ?? $skill['title']
                ?? $skill['value']
                ?? '';
        }

        if (!is_scalar($skill)) {
            continue;
        }

        $skill =
            cleanText($skill);

        if ($skill === '') {
            continue;
        }

        $key =
            strtolower($skill);

        if (!isset($seen[$key])) {

            $seen[$key] = true;

            $result[] =
                $skill;
        }
    }

    return array_values($result);
}


/* ============================================================
   JOB NORMALIZATION
   ============================================================ */

function normalizeCareerJobs($jobs)
{
    if (!is_array($jobs)) {
        return [];
    }

    $normalized = [];
    $seen = [];

    foreach ($jobs as $job) {

        if (!is_array($job)) {
            continue;
        }

        $company =
            $job['company']
            ?? $job['employer']
            ?? $job['company_name']
            ?? $job['organization']
            ?? '';

        $role =
            $job['role']
            ?? $job['title']
            ?? $job['job_title']
            ?? $job['position']
            ?? $job['name']
            ?? '';

        $requiredSkills =
            $job['required_skills']
            ?? $job['skills']
            ?? $job['requirements']
            ?? $job['technical_skills']
            ?? [];

        $jobUrl =
            $job['url']
            ?? $job['link']
            ?? $job['job_url']
            ?? $job['apply_url']
            ?? '';

        $description =
            $job['description']
            ?? $job['text']
            ?? $job['summary']
            ?? '';

        $location =
            $job['location']
            ?? $job['locations']
            ?? '';

        if (is_array($company)) {
            $company = '';
        }

        if (is_array($role)) {
            $role = '';
        }

        if (is_array($jobUrl)) {
            $jobUrl = '';
        }

        if (is_array($location)) {

            $location =
                implode(
                    ', ',
                    array_filter(
                        array_map(
                            'cleanText',
                            $location
                        )
                    )
                );
        }

        $company =
            cleanText($company);

        $role =
            cleanText($role);

        $jobUrl =
            trim((string)$jobUrl);

        $description =
            cleanText($description);

        $location =
            cleanText($location);

        $requiredSkills =
            normalizeSkills(
                $requiredSkills
            );

        if (
            empty($requiredSkills) &&
            $description !== ''
        ) {

            $requiredSkills =
                extractSkillsFromText(
                    $description
                );
        }

        if (
            $role === '' &&
            empty($requiredSkills)
        ) {
            continue;
        }

        $uniqueKey =
            strtolower(
                trim(
                    $role .
                    '|' .
                    $company .
                    '|' .
                    $jobUrl
                )
            );

        if (
            $uniqueKey !== '||' &&
            isset($seen[$uniqueKey])
        ) {
            continue;
        }

        $seen[$uniqueKey] = true;

        $normalized[] = [
            "company" =>
                $company,

            "role" =>
                $role,

            "required_skills" =>
                $requiredSkills,

            "url" =>
                $jobUrl,

            "description" =>
                $description,

            "location" =>
                $location
        ];
    }

    return $normalized;
}


/* ============================================================
   GENERIC TECHNICAL SKILL EXTRACTION
   ============================================================ */

function extractSkillsFromText($text)
{
    $text =
        strtolower(
            cleanText($text)
        );

    if ($text === '') {
        return [];
    }

    $skillVocabulary = [

        'python',
        'java',
        'javascript',
        'typescript',
        'c',
        'c++',
        'c#',
        'php',
        'go',
        'golang',
        'rust',
        'kotlin',
        'swift',

        'html',
        'css',
        'react',
        'react.js',
        'angular',
        'vue',
        'node',
        'node.js',
        'express',
        'next.js',

        'sql',
        'mysql',
        'postgresql',
        'postgres',
        'mongodb',
        'oracle',
        'redis',

        'git',
        'github',
        'gitlab',

        'docker',
        'kubernetes',

        'aws',
        'azure',
        'gcp',
        'google cloud',

        'linux',
        'unix',

        'networking',
        'tcp/ip',
        'tcp',
        'udp',
        'http',
        'https',
        'dns',
        'dhcp',

        'cyber security',
        'cybersecurity',
        'information security',
        'network security',
        'penetration testing',
        'ethical hacking',
        'digital forensics',

        'machine learning',
        'deep learning',
        'artificial intelligence',
        'data science',
        'data analysis',

        'pandas',
        'numpy',
        'scikit-learn',
        'tensorflow',
        'pytorch',
        'opencv',

        'rest api',
        'restful api',
        'api',
        'microservices',

        'linux administration',
        'system administration',

        'computer networks',
        'data structures',
        'algorithms',
        'object oriented programming',
        'oops',
        'dbms',
        'operating systems',

        'spring',
        'spring boot',

        'jenkins',
        'terraform',
        'ansible',

        'power bi',
        'tableau',
        'excel'
    ];

    $found = [];

    foreach ($skillVocabulary as $skill) {

        $pattern =
            '/(?<![a-z0-9])' .
            preg_quote(
                $skill,
                '/'
            ) .
            '(?![a-z0-9])/i';

        if (
            preg_match(
                $pattern,
                $text
            )
        ) {

            $found[] =
                $skill;
        }
    }

    return normalizeSkills(
        $found
    );
}


/* ============================================================
   FIND JOBS RECURSIVELY
   ============================================================ */

function findJobsInResponse($data)
{
    if (!is_array($data)) {
        return [];
    }

    $possibleKeys = [
        'jobs',
        'roles',
        'job_listings',
        'jobListings',
        'listings',
        'results',
        'positions',
        'openings',
        'vacancies',
        'items',
        'data'
    ];

    foreach ($possibleKeys as $key) {

        if (
            isset($data[$key]) &&
            is_array($data[$key])
        ) {

            $jobs =
                normalizeCareerJobs(
                    $data[$key]
                );

            if (!empty($jobs)) {
                return $jobs;
            }
        }
    }

    $directJobs =
        normalizeCareerJobs($data);

    if (!empty($directJobs)) {
        return $directJobs;
    }

    foreach ($data as $value) {

        if (!is_array($value)) {
            continue;
        }

        $jobs =
            findJobsInResponse($value);

        if (!empty($jobs)) {
            return $jobs;
        }
    }

    return [];
}


/* ============================================================
   STORE CAREER JOBS
   ============================================================ */

function storeCareerJobs($jobs, $url = '')
{
    $jobs =
        normalizeCareerJobs($jobs);

    $_SESSION['career_jobs'] =
        $jobs;

    if ($url !== '') {
        $_SESSION['career_url'] =
            trim($url);
    }

    return $jobs;
}


/* ============================================================
   HTTP GET
   ============================================================ */

function httpGetPage($url, $timeout = 15)
{
    if (!function_exists('curl_init')) {

        return [
            "success" => false,
            "body" => '',
            "message" =>
                "cURL is not available on this server."
        ];
    }

    $ch =
        curl_init();

    curl_setopt_array(
        $ch,
        [
            CURLOPT_URL =>
                $url,

            CURLOPT_RETURNTRANSFER =>
                true,

            CURLOPT_FOLLOWLOCATION =>
                true,

            CURLOPT_MAXREDIRS =>
                8,

            CURLOPT_CONNECTTIMEOUT =>
                10,

            CURLOPT_TIMEOUT =>
                $timeout,

            CURLOPT_USERAGENT =>
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154 Safari/537.36',

            CURLOPT_HTTPHEADER => [
                'Accept: text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
                'Accept-Language: en-US,en;q=0.9'
            ],

            CURLOPT_ENCODING =>
                '',

            CURLOPT_SSL_VERIFYPEER =>
                true,

            CURLOPT_SSL_VERIFYHOST =>
                2
        ]
    );

    $body =
        curl_exec($ch);

    $error =
        curl_error($ch);

    $httpCode =
        (int)curl_getinfo(
            $ch,
            CURLINFO_HTTP_CODE
        );

    curl_close($ch);

    if (
        $body === false ||
        $body === ''
    ) {

        return [
            "success" => false,
            "body" => '',
            "message" =>
                $error !== ''
                    ? $error
                    : "Empty response."
        ];
    }

    if ($httpCode >= 400) {

        return [
            "success" => false,
            "body" => '',
            "message" =>
                "HTTP " . $httpCode
        ];
    }

    return [
        "success" => true,
        "body" => $body,
        "message" => ''
    ];
}


/* ============================================================
   URL HELPERS
   ============================================================ */

function makeAbsoluteUrl($baseUrl, $href)
{
    $href =
        trim(
            html_entity_decode(
                $href,
                ENT_QUOTES | ENT_HTML5,
                'UTF-8'
            )
        );

    if ($href === '') {
        return '';
    }

    $lowerHref =
        strtolower($href);

    if (
        strpos(
            $lowerHref,
            'javascript:'
        ) === 0 ||
        strpos(
            $lowerHref,
            'mailto:'
        ) === 0 ||
        strpos(
            $href,
            '#'
        ) === 0
    ) {
        return '';
    }

    if (
        preg_match(
            '#^https?://#i',
            $href
        )
    ) {
        return $href;
    }

    $base =
        parse_url($baseUrl);

    if (
        !$base ||
        empty($base['host'])
    ) {
        return '';
    }

    $scheme =
        $base['scheme']
        ?? 'https';

    $host =
        $base['host'];

    if (
        strpos(
            $href,
            '//'
        ) === 0
    ) {
        return $scheme . ':' . $href;
    }

    if (
        strpos(
            $href,
            '/'
        ) === 0
    ) {

        return
            $scheme .
            '://' .
            $host .
            $href;
    }

    $basePath =
        $base['path']
        ?? '/';

    $directory =
        rtrim(
            dirname($basePath),
            '/'
        );

    return
        $scheme .
        '://' .
        $host .
        $directory .
        '/' .
        $href;
}


/* ============================================================
   EXTRACT BODY TEXT
   ============================================================ */

function extractHtmlBodyText($html)
{
    if ($html === '') {
        return '';
    }

    if (class_exists('DOMDocument')) {

        $dom =
            new DOMDocument();

        libxml_use_internal_errors(true);

        @$dom->loadHTML(
            '<?xml encoding="UTF-8">' .
            $html
        );

        libxml_clear_errors();

        $xpath =
            new DOMXPath($dom);

        $nodes =
            $xpath->query(
                '//body'
            );

        if (
            $nodes !== false &&
            $nodes->length > 0
        ) {

            return cleanText(
                $nodes->item(0)->textContent
            );
        }
    }

    $text =
        preg_replace(
            '/<script\b[^>]*>.*?<\/script>/is',
            ' ',
            $html
        );

    $text =
        preg_replace(
            '/<style\b[^>]*>.*?<\/style>/is',
            ' ',
            $text
        );

    $text =
        preg_replace(
            '/<noscript\b[^>]*>.*?<\/noscript>/is',
            ' ',
            $text
        );

    return cleanText($text);
}


/* ============================================================
   EXTRACT JSON-LD JOBS
   ============================================================ */

function extractJsonLdJobs($html, $sourceUrl)
{
    $jobs = [];

    if (
        !preg_match_all(
            '/<script[^>]+type=["\']application\/ld\+json["\'][^>]*>(.*?)<\/script>/is',
            $html,
            $matches
        )
    ) {
        return [];
    }

    foreach (
        $matches[1]
        as $jsonText
    ) {

        $jsonText =
            html_entity_decode(
                $jsonText,
                ENT_QUOTES | ENT_HTML5,
                'UTF-8'
            );

        $decoded =
            json_decode(
                trim($jsonText),
                true
            );

        if (!is_array($decoded)) {
            continue;
        }

        $objects = [];

        if (
            isset($decoded['@graph']) &&
            is_array($decoded['@graph'])
        ) {

            $objects =
                $decoded['@graph'];

        } elseif (
            isset($decoded[0]) &&
            is_array($decoded[0])
        ) {

            $objects =
                $decoded;

        } else {

            $objects[] =
                $decoded;
        }

        foreach ($objects as $obj) {

            if (!is_array($obj)) {
                continue;
            }

            $type =
                strtolower(
                    (string)(
                        $obj['@type']
                        ?? ''
                    )
                );

            if (
                strpos(
                    $type,
                    'jobposting'
                ) === false
            ) {
                continue;
            }

            $description =
                cleanText(
                    $obj['description']
                    ?? ''
                );

            $skills =
                normalizeSkills(
                    $obj['skills']
                    ?? $obj['qualifications']
                    ?? []
                );

            if (
                empty($skills) &&
                $description !== ''
            ) {

                $skills =
                    extractSkillsFromText(
                        $description
                    );
            }

            $company = '';

            if (
                isset(
                    $obj['hiringOrganization']
                ) &&
                is_array(
                    $obj['hiringOrganization']
                )
            ) {

                $company =
                    cleanText(
                        $obj['hiringOrganization']['name']
                        ?? ''
                    );
            }

            $location = '';

            if (
                isset(
                    $obj['jobLocation']
                ) &&
                is_array(
                    $obj['jobLocation']
                )
            ) {

                $location =
                    json_encode(
                        $obj['jobLocation'],
                        JSON_UNESCAPED_UNICODE
                    );

                $location =
                    cleanText($location);
            }

            $jobs[] = [
                "company" =>
                    $company,

                "role" =>
                    cleanText(
                        $obj['title']
                        ?? ''
                    ),

                "required_skills" =>
                    $skills,

                "url" =>
                    trim(
                        (string)(
                            $obj['url']
                            ?? $sourceUrl
                        )
                    ),

                "description" =>
                    $description,

                "location" =>
                    $location
            ];
        }
    }

    return normalizeCareerJobs($jobs);
}


/* ============================================================
   EXTRACT JOB LINKS WITH REGEX
   ============================================================ */

function extractJobLinksWithRegex(
    $html,
    $baseUrl,
    $limit = 50
) {
    $jobs = [];

    if (
        !preg_match_all(
            '/<a\b[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)<\/a>/is',
            $html,
            $matches,
            PREG_SET_ORDER
        )
    ) {
        return [];
    }

    foreach ($matches as $match) {

        $href =
            $match[1]
            ?? '';

        $anchorHtml =
            $match[2]
            ?? '';

        $title =
            cleanText(
                $anchorHtml
            );

        if (
            $title === '' ||
            strlen($title) < 4
        ) {
            continue;
        }

        $absolute =
            makeAbsoluteUrl(
                $baseUrl,
                $href
            );

        if ($absolute === '') {
            continue;
        }

        $lowerUrl =
            strtolower($absolute);

        $lowerTitle =
            strtolower($title);

        $isJobLink =
            preg_match(
                '/\/jobs?\//i',
                $lowerUrl
            ) ||
            preg_match(
                '/job|career|position|opening|vacanc|requisition|opportunit/i',
                $lowerUrl . ' ' . $lowerTitle
            );

        if (!$isJobLink) {
            continue;
        }

        $blockedWords = [
            'login',
            'sign in',
            'sign up',
            'home',
            'about us',
            'contact us',
            'privacy',
            'terms',
            'cookie',
            'search',
            'menu',
            'learn more',
            'read more',
            'apply now'
        ];

        $blocked = false;

        foreach ($blockedWords as $blockedWord) {

            if (
                $lowerTitle ===
                $blockedWord
            ) {

                $blocked = true;
                break;
            }
        }

        if ($blocked) {
            continue;
        }

        $jobs[] = [
            "company" =>
                '',

            "role" =>
                $title,

            "required_skills" =>
                [],

            "url" =>
                $absolute,

            "description" =>
                '',

            "location" =>
                ''
        ];

        if (
            count($jobs) >= $limit
        ) {
            break;
        }
    }

    return normalizeCareerJobs($jobs);
}


/* ============================================================
   EXTRACT JOB LINKS WITH DOM
   ============================================================ */

function extractJobLinksWithDom(
    $html,
    $baseUrl,
    $limit = 50
) {
    $jobs = [];

    if (!class_exists('DOMDocument')) {
        return [];
    }

    $dom =
        new DOMDocument();

    libxml_use_internal_errors(true);

    @$dom->loadHTML(
        '<?xml encoding="UTF-8">' .
        $html
    );

    libxml_clear_errors();

    $xpath =
        new DOMXPath($dom);

    $anchors =
        $xpath->query(
            '//a[@href]'
        );

    if (
        $anchors === false
    ) {
        return [];
    }

    foreach ($anchors as $anchor) {

        $href =
            $anchor->getAttribute(
                'href'
            );

        $title =
            cleanText(
                $anchor->textContent
            );

        if (
            $title === '' ||
            strlen($title) < 4
        ) {
            continue;
        }

        $absolute =
            makeAbsoluteUrl(
                $baseUrl,
                $href
            );

        if ($absolute === '') {
            continue;
        }

        $lowerUrl =
            strtolower($absolute);

        $lowerTitle =
            strtolower($title);

        $isJobLink =
            preg_match(
                '/\/jobs?\//i',
                $lowerUrl
            ) ||
            preg_match(
                '/job|career|position|opening|vacanc|requisition|opportunit/i',
                $lowerUrl . ' ' . $lowerTitle
            );

        if (!$isJobLink) {
            continue;
        }

        $blockedWords = [
            'login',
            'sign in',
            'sign up',
            'home',
            'about us',
            'contact us',
            'privacy',
            'terms',
            'cookie',
            'search',
            'menu',
            'learn more',
            'read more',
            'apply now'
        ];

        $blocked = false;

        foreach ($blockedWords as $blockedWord) {

            if (
                $lowerTitle ===
                $blockedWord
            ) {

                $blocked = true;
                break;
            }
        }

        if ($blocked) {
            continue;
        }

        $jobs[] = [
            "company" =>
                '',

            "role" =>
                $title,

            "required_skills" =>
                [],

            "url" =>
                $absolute,

            "description" =>
                '',

            "location" =>
                ''
        ];

        if (
            count($jobs) >= $limit
        ) {
            break;
        }
    }

    return normalizeCareerJobs($jobs);
}


/* ============================================================
   ENRICH JOB DETAILS
   ============================================================ */

function enrichJobDetails(
    $jobs,
    $limit = 20
) {
    $processed = 0;

    foreach ($jobs as $index => $job) {

        if ($processed >= $limit) {
            break;
        }

        $jobUrl =
            $job['url']
            ?? '';

        if ($jobUrl === '') {
            continue;
        }

        $existingDescription =
            $job['description']
            ?? '';

        $existingSkills =
            normalizeSkills(
                $job['required_skills']
                ?? []
            );

        if (
            $existingDescription !== '' &&
            !empty($existingSkills)
        ) {
            continue;
        }

        if (
            !preg_match(
                '#^https?://#i',
                $jobUrl
            )
        ) {
            continue;
        }

        $detail =
            httpGetPage(
                $jobUrl,
                10
            );

        $processed++;

        if (
            !$detail['success'] ||
            $detail['body'] === ''
        ) {
            continue;
        }

        $detailHtml =
            $detail['body'];

        $jsonJobs =
            extractJsonLdJobs(
                $detailHtml,
                $jobUrl
            );

        if (!empty($jsonJobs)) {

            $first =
                $jsonJobs[0];

            if (
                empty($jobs[$index]['role']) &&
                !empty($first['role'])
            ) {
                $jobs[$index]['role'] =
                    $first['role'];
            }

            if (
                empty($jobs[$index]['company']) &&
                !empty($first['company'])
            ) {
                $jobs[$index]['company'] =
                    $first['company'];
            }

            if (
                empty($jobs[$index]['location']) &&
                !empty($first['location'])
            ) {
                $jobs[$index]['location'] =
                    $first['location'];
            }

            if (
                empty($jobs[$index]['description']) &&
                !empty($first['description'])
            ) {
                $jobs[$index]['description'] =
                    $first['description'];
            }

            if (
                empty(
                    $jobs[$index]['required_skills']
                ) &&
                !empty(
                    $first['required_skills']
                )
            ) {
                $jobs[$index]['required_skills'] =
                    $first['required_skills'];
            }
        }

        if (
            empty(
                $jobs[$index]['description']
            )
        ) {

            $detailText =
                extractHtmlBodyText(
                    $detailHtml
                );

            if (
                $detailText !== ''
            ) {

                if (
                    strlen($detailText) > 12000
                ) {

                    $detailText =
                        substr(
                            $detailText,
                            0,
                            12000
                        );
                }

                $jobs[$index]['description'] =
                    $detailText;
            }
        }

        if (
            empty(
                $jobs[$index]['required_skills']
            )
        ) {

            $jobs[$index]['required_skills'] =
                extractSkillsFromText(
                    $jobs[$index]['description']
                    ?? ''
                );
        }
    }

    return normalizeCareerJobs($jobs);
}


/* ============================================================
   GENERIC FALLBACK CAREER SCRAPER
   ============================================================ */

function scrapeCareerPageFallback($url)
{
    $page =
        httpGetPage(
            $url,
            25
        );

    if (
        !$page['success'] ||
        $page['body'] === ''
    ) {

        return [
            "jobs" => [],
            "message" =>
                $page['message']
                ?? 'Unable to read career page.'
        ];
    }

    $html =
        $page['body'];

    $jobs = [];

    $jsonJobs =
        extractJsonLdJobs(
            $html,
            $url
        );

    if (!empty($jsonJobs)) {

        $jobs =
            array_merge(
                $jobs,
                $jsonJobs
            );
    }

    $domJobs =
        extractJobLinksWithDom(
            $html,
            $url,
            50
        );

    if (!empty($domJobs)) {

        $jobs =
            array_merge(
                $jobs,
                $domJobs
            );
    }

    $regexJobs =
        extractJobLinksWithRegex(
            $html,
            $url,
            50
        );

    if (!empty($regexJobs)) {

        $jobs =
            array_merge(
                $jobs,
                $regexJobs
            );
    }

    $jobs =
        normalizeCareerJobs(
            $jobs
        );

    if (!empty($jobs)) {

        $jobs =
            enrichJobDetails(
                $jobs,
                20
            );
    }

    return [
        "jobs" =>
            $jobs,

        "message" =>
            count($jobs) .
            " job(s) found by fallback scraper."
    ];
}


/* ============================================================
   AMAZON CAREER URL → SEARCH URL
   ============================================================ */

function buildAmazonSearchUrl($url)
{
    $parts =
        parse_url($url);

    if (
        !$parts ||
        empty($parts['host'])
    ) {
        return '';
    }

    $host =
        strtolower(
            $parts['host']
        );

    if (
        strpos(
            $host,
            'amazon.jobs'
        ) === false
    ) {
        return '';
    }

    $path =
        $parts['path']
        ?? '';

    $segments =
        array_values(
            array_filter(
                explode(
                    '/',
                    trim(
                        $path,
                        '/'
                    )
                )
            )
        );

    if (empty($segments)) {
        return '';
    }

    $locationSlug = '';

    for (
        $i = count($segments) - 1;
        $i >= 0;
        $i--
    ) {

        $candidate =
            strtolower(
                trim(
                    $segments[$i]
                )
            );

        if (
            $candidate === '' ||
            $candidate === 'locations' ||
            $candidate === 'location' ||
            $candidate === 'india' ||
            $candidate === 'en' ||
            $candidate === 'content'
        ) {
            continue;
        }

        $locationSlug =
            $candidate;

        break;
    }

    if ($locationSlug === '') {
        return '';
    }

    return
        'https://www.amazon.jobs/en/search?loc_query=' .
        rawurlencode(
            str_replace(
                '-',
                ' ',
                $locationSlug
            )
        );
}


/* ============================================================
   AMAZON SEARCH PAGE SCRAPER
   ============================================================ */

function scrapeAmazonSearchPage($searchUrl)
{
    $page =
        httpGetPage(
            $searchUrl,
            30
        );

    if (
        !$page['success'] ||
        $page['body'] === ''
    ) {

        return [
            "jobs" => [],
            "message" =>
                $page['message']
                ?? 'Unable to read Amazon job search page.'
        ];
    }

    $html =
        $page['body'];

    $jobs = [];

    $jsonJobs =
        extractJsonLdJobs(
            $html,
            $searchUrl
        );

    if (!empty($jsonJobs)) {

        $jobs =
            array_merge(
                $jobs,
                $jsonJobs
            );
    }

    $domJobs =
        extractJobLinksWithDom(
            $html,
            $searchUrl,
            50
        );

    if (!empty($domJobs)) {

        $jobs =
            array_merge(
                $jobs,
                $domJobs
            );
    }

    $regexJobs =
        extractJobLinksWithRegex(
            $html,
            $searchUrl,
            50
        );

    if (!empty($regexJobs)) {

        $jobs =
            array_merge(
                $jobs,
                $regexJobs
            );
    }

    if (
        preg_match_all(
            '#https?://(?:www\.)?amazon\.jobs/[^"\']*/jobs/[^"\']+#i',
            $html,
            $amazonUrlMatches
        )
    ) {

        foreach (
            $amazonUrlMatches[0]
            as $amazonUrl
        ) {

            $amazonUrl =
                html_entity_decode(
                    $amazonUrl,
                    ENT_QUOTES | ENT_HTML5,
                    'UTF-8'
                );

            $jobs[] = [
                "company" =>
                    '',

                "role" =>
                    '',

                "required_skills" =>
                    [],

                "url" =>
                    $amazonUrl,

                "description" =>
                    '',

                "location" =>
                    ''
            ];
        }
    }

    $jobs =
        normalizeCareerJobs(
            $jobs
        );

    if (!empty($jobs)) {

        $jobs =
            enrichJobDetails(
                $jobs,
                20
            );
    }

    return [
        "jobs" =>
            $jobs,

        "message" =>
            count($jobs) .
            " job(s) found from the career search page.",

        "search_url" =>
            $searchUrl
    ];
}


/* ============================================================
   SOURCE-SPECIFIC CAREER SCRAPER
   ============================================================ */

function scrapeSourceSpecificCareerPage($url)
{
    $parts =
        parse_url($url);

    if (
        !$parts ||
        empty($parts['host'])
    ) {

        return [
            "jobs" => [],
            "message" => ''
        ];
    }

    $host =
        strtolower(
            $parts['host']
        );

    if (
        strpos(
            $host,
            'amazon.jobs'
        ) !== false
    ) {

        $searchUrl =
            buildAmazonSearchUrl(
                $url
            );

        if ($searchUrl !== '') {

            return
                scrapeAmazonSearchPage(
                    $searchUrl
                );
        }
    }

    return [
        "jobs" => [],
        "message" => ''
    ];
}


/* ============================================================
   DYNAMIC JOB RECOMMENDATION
   ============================================================ */

function normalizeComparisonText($value)
{
    $value =
        strtolower(
            trim(
                strip_tags(
                    (string)$value
                )
            )
        );

    $value =
        preg_replace(
            '/[^a-z0-9+#.\- ]+/i',
            ' ',
            $value
        );

    $value =
        preg_replace(
            '/\s+/',
            ' ',
            $value
        );

    return trim($value);
}


function skillMatches(
    $resumeSkill,
    $requiredSkill
) {
    $a =
        normalizeComparisonText(
            $resumeSkill
        );

    $b =
        normalizeComparisonText(
            $requiredSkill
        );

    if (
        $a === '' ||
        $b === ''
    ) {
        return false;
    }

    if ($a === $b) {
        return true;
    }

    $aliases = [
        'node.js' =>
            ['node'],

        'node' =>
            ['node.js'],

        'react.js' =>
            ['react'],

        'react' =>
            ['react.js'],

        'postgresql' =>
            ['postgres'],

        'postgres' =>
            ['postgresql'],

        'javascript' =>
            ['js'],

        'typescript' =>
            ['ts'],

        'c++' =>
            ['cpp']
    ];

    if (
        isset($aliases[$a]) &&
        in_array(
            $b,
            $aliases[$a],
            true
        )
    ) {
        return true;
    }

    if (
        isset($aliases[$b]) &&
        in_array(
            $a,
            $aliases[$b],
            true
        )
    ) {
        return true;
    }

    if (
        strpos($a, $b) !== false ||
        strpos($b, $a) !== false
    ) {
        return true;
    }

    return false;
}


function calculateLocalJobRecommendation(
    $jobs,
    $resumeSkills
) {
    $resumeSkills =
        normalizeSkills(
            $resumeSkills
        );

    if (
        empty($jobs) ||
        empty($resumeSkills)
    ) {
        return null;
    }

    $best = null;

    foreach ($jobs as $job) {

        $required =
            normalizeSkills(
                $job['required_skills']
                ?? []
            );

        if (
            empty($required) &&
            !empty(
                $job['description']
            )
        ) {

            $required =
                extractSkillsFromText(
                    $job['description']
                );
        }

        if (empty($required)) {
            continue;
        }

        $matched = [];
        $missing = [];

        foreach (
            $required
            as $requiredSkill
        ) {

            $found = false;

            foreach (
                $resumeSkills
                as $resumeSkill
            ) {

                if (
                    skillMatches(
                        $resumeSkill,
                        $requiredSkill
                    )
                ) {

                    $found = true;

                    $matched[] =
                        $requiredSkill;

                    break;
                }
            }

            if (!$found) {

                $missing[] =
                    $requiredSkill;
            }
        }

        $matched =
            array_values(
                array_unique(
                    $matched
                )
            );

        $missing =
            array_values(
                array_unique(
                    $missing
                )
            );

        $score =
            count($required) > 0
                ? round(
                    (
                        count($matched) /
                        count($required)
                    ) * 100,
                    1
                )
                : 0;

        $candidate = [
            "company" =>
                $job['company'] ?? '',

            "role" =>
                $job['role'] ?? '',

            "url" =>
                $job['url'] ?? '',

            "description" =>
                $job['description'] ?? '',

            "location" =>
                $job['location'] ?? '',

            "required_skills" =>
                $required,

            "matched_skills" =>
                $matched,

            "missing_skills" =>
                $missing,

            "score" =>
                $score
        ];

        if ($best === null) {

            $best =
                $candidate;

            continue;
        }

        if (
            $candidate['score'] >
            $best['score']
        ) {

            $best =
                $candidate;

        } elseif (
            $candidate['score'] ===
            $best['score'] &&
            count(
                $candidate['matched_skills']
            ) >
            count(
                $best['matched_skills']
            )
        ) {

            $best =
                $candidate;
        }
    }

    return $best;
}


/* ============================================================
   SAVE DYNAMIC RECOMMENDATION
   ============================================================ */

function saveDynamicRecommendation(
    $recommendation
) {
    if (
        !is_array($recommendation) ||
        empty($recommendation)
    ) {
        return;
    }

    $_SESSION['recommended_job'] =
        $recommendation;

    $_SESSION['target_company'] =
        trim(
            $recommendation['company']
            ?? ''
        );

    $_SESSION['target_role'] =
        trim(
            $recommendation['role']
            ?? ''
        );

    $_SESSION['required_skills'] =
        normalizeSkills(
            $recommendation['required_skills']
            ?? []
        );
}


/* ============================================================
   ACTION
   ============================================================ */

$action =
    $_GET['action']
    ?? ($_POST['action'] ?? '');

$action =
    strtolower(
        trim(
            (string)$action
        )
    );

if ($action === '') {

    jsonResponse([
        "status" => "error",
        "message" =>
            "Action parameter required."
    ], 400);
}


/* ============================================================
   PUBLIC ACTIONS
   ============================================================ */


/* ============================================================
   LOGIN
   ============================================================ */

if ($action === 'login') {

    $email =
        trim(
            $_POST['email'] ?? ''
        );

    $password =
        $_POST['password'] ?? '';

    if (
        $email === '' ||
        $password === ''
    ) {

        jsonResponse([
            "status" => "error",
            "error_code" =>
                "VALIDATION_ERROR",
            "message" =>
                "Email and password are required."
        ], 400);
    }

    $authRes =
        authenticateUser(
            $email,
            $password
        );

    if (
        isset($authRes['success']) &&
        $authRes['success']
    ) {

        /*
         * Regenerate the session ID after authentication.
         */
        session_regenerate_id(true);

        /*
         * Store authenticated user.
         */
        $loggedInUser =
            $authRes['user'];

        $_SESSION['user'] =
            $loggedInUser;

        /*
         * Store user ID separately.
         */
        $_SESSION['user_id'] =
            isset($loggedInUser['id'])
                ? (int)$loggedInUser['id']
                : 0;

        /*
         * Explicit authentication flag.
         */
        $_SESSION['logged_in'] =
            true;

        /*
         * Reset application state.
         */
        $_SESSION['extracted_skills'] =
            [];

        $_SESSION['ats_score'] =
            null;

        $_SESSION['parsed_resume'] =
            [];

        $_SESSION['career_jobs'] =
            [];

        $_SESSION['career_url'] =
            '';

        $_SESSION['target_company'] =
            '';

        $_SESSION['target_role'] =
            '';

        $_SESSION['required_skills'] =
            [];

        $_SESSION['recommended_job'] =
            null;

        /*
         * Make absolutely sure the PHP session is
         * written before the response is sent.
         */
        session_write_close();

        jsonResponse([
            "status" =>
                "success",

            "success" =>
                true,

            "message" =>
                "Login successful.",

            "user" =>
                $loggedInUser,

            "user_id" =>
                isset($loggedInUser['id'])
                    ? (int)$loggedInUser['id']
                    : 0,

            "loggedIn" =>
                true,

            "redirect" =>
                "dashboard"
        ]);
    }

    jsonResponse([
        "status" =>
            "error",

        "error_code" =>
            "INVALID_CREDENTIALS",

        "message" =>
            $authRes['message']
            ?? "Invalid email or password."
    ], 401);
}


/* ============================================================
   SIGNUP / REGISTER
   ============================================================ */

if (
    $action === 'signup' ||
    $action === 'register'
) {

    $name =
        trim(
            $_POST['name'] ?? ''
        );

    $email =
        trim(
            $_POST['email'] ?? ''
        );

    $password =
        $_POST['password'] ?? '';

    $university =
        trim(
            $_POST['university']
            ?? 'GITAM University, Bengaluru'
        );

    $branch =
        trim(
            $_POST['branch']
            ?? 'Computer Science & Engineering'
        );

    $year =
        (int)(
            $_POST['graduation_year']
            ?? date('Y')
        );

    $linkedin =
        trim(
            $_POST['linkedin'] ?? ''
        );

    $github =
        trim(
            $_POST['github'] ?? ''
        );


    if (
        $name === '' ||
        $email === '' ||
        $password === ''
    ) {

        jsonResponse([
            "status" =>
                "error",

            "error_code" =>
                "VALIDATION_ERROR",

            "message" =>
                "Please fill in all required account fields."
        ], 400);
    }


    if (
        !filter_var(
            $email,
            FILTER_VALIDATE_EMAIL
        )
    ) {

        jsonResponse([
            "status" =>
                "error",

            "error_code" =>
                "INVALID_EMAIL",

            "message" =>
                "Please enter a valid email address."
        ], 400);
    }


    if (
        strlen($password) < 6
    ) {

        jsonResponse([
            "status" =>
                "error",

            "error_code" =>
                "WEAK_PASSWORD",

            "message" =>
                "Password must contain at least 6 characters."
        ], 400);
    }


    $regRes =
        registerUser(
            $name,
            $email,
            $password,
            $university,
            $branch,
            $year,
            '',
            '',
            $linkedin,
            $github
        );


    if (
        isset($regRes['success']) &&
        $regRes['success']
    ) {

        jsonResponse([
            "status" =>
                "success",

            "success" =>
                true,

            "registered" =>
                true,

            "accountCreated" =>
                true,

            "error_code" =>
                "ACCOUNT_CREATED",

            "message" =>
                "Account registered successfully.",

            "redirect" =>
                "login",

            "email" =>
                $email
        ], 200);
    }


    $registrationMessage =
        strtolower(
            trim(
                $regRes['message']
                ?? ''
            )
        );

    $duplicate =
        strpos(
            $registrationMessage,
            'already'
        ) !== false ||

        strpos(
            $registrationMessage,
            'exist'
        ) !== false ||

        strpos(
            $registrationMessage,
            'duplicate'
        ) !== false ||

        strpos(
            $registrationMessage,
            'taken'
        ) !== false ||

        strpos(
            $registrationMessage,
            'registered'
        ) !== false;


    if ($duplicate) {

        jsonResponse([
            "status" =>
                "error",

            "success" =>
                false,

            "error_code" =>
                "ACCOUNT_EXISTS",

            "accountExists" =>
                true,

            "message" =>
                "An account with this email already exists. Please log in instead.",

            "redirect" =>
                "login",

            "email" =>
                $email
        ], 409);
    }


    jsonResponse([
        "status" =>
            "error",

        "success" =>
            false,

        "error_code" =>
            "REGISTRATION_FAILED",

        "accountExists" =>
            false,

        "message" =>
            $regRes['message']
            ?? "Unable to create account."
    ], 400);
}


/* ============================================================
   LOGOUT
   ============================================================ */

if ($action === 'logout') {

    $_SESSION = [];

    if (
        ini_get(
            "session.use_cookies"
        )
    ) {

        $params =
            session_get_cookie_params();

        setcookie(
            session_name(),
            '',
            time() - 42000,
            $params["path"],
            $params["domain"],
            $params["secure"],
            $params["httponly"]
        );
    }

    session_destroy();

    jsonResponse([
        "status" =>
            "success",

        "message" =>
            "Logged out successfully.",

        "loggedIn" =>
            false
    ]);
}


/* ============================================================
   AUTHENTICATION REQUIRED
   ============================================================ */

if (
    empty($_SESSION['logged_in']) ||
    empty($_SESSION['user_id']) ||
    !isset($_SESSION['user']) ||
    !is_array($_SESSION['user'])
) {

    jsonResponse([
        "status" =>
            "error",

        "error_code" =>
            "UNAUTHORIZED",

        "message" =>
            "Unauthorized access. Please log in.",

        "loggedIn" =>
            false
    ], 401);
}


$current_user =
    $_SESSION['user'];


/* ============================================================
   UPDATE PROFILE
   ============================================================ */

if ($action === 'update_profile') {

    $name =
        trim(
            $_POST['name']
            ?? (
                $current_user['name']
                ?? ''
            )
        );

    $university =
        trim(
            $_POST['university']
            ?? (
                $current_user['university']
                ?? ''
            )
        );

    $branch =
        trim(
            $_POST['branch']
            ?? (
                $current_user['branch']
                ?? ''
            )
        );

    $year =
        (int)(
            $_POST['graduation_year']
            ?? (
                $current_user['graduation_year']
                ?? date('Y')
            )
        );

    $company =
        array_key_exists(
            'target_company',
            $_POST
        )
            ? trim(
                $_POST['target_company']
            )
            : '';

    $role =
        array_key_exists(
            'target_role',
            $_POST
        )
            ? trim(
                $_POST['target_role']
            )
            : '';

    $linkedin =
        trim(
            $_POST['linkedin']
            ?? (
                $current_user['linkedin']
                ?? ''
            )
        );

    $github =
        trim(
            $_POST['github']
            ?? (
                $current_user['github']
                ?? ''
            )
        );

    if (
        !array_key_exists(
            'target_company',
            $_POST
        )
    ) {

        $company =
            $current_user['target_company']
            ?? '';
    }

    if (
        !array_key_exists(
            'target_role',
            $_POST
        )
    ) {

        $role =
            $current_user['target_role']
            ?? '';
    }

    $ok =
        updateStudentProfile(
            $current_user['id'],
            $name,
            $university,
            $branch,
            $year,
            $role,
            $company,
            $linkedin,
            $github
        );

    if ($ok) {

        $_SESSION['user'] =
            getStudentById(
                $current_user['id']
            );

        jsonResponse([
            "status" =>
                "success",

            "message" =>
                "Profile updated successfully.",

            "user" =>
                $_SESSION['user']
        ]);
    }

    jsonResponse([
        "status" =>
            "error",

        "message" =>
            "Failed to update profile."
    ], 500);
}


/* ============================================================
   UPDATE SKILLS
   ============================================================ */

if ($action === 'update_skills') {

    $skills =
        normalizeSkills(
            $_POST['skills'] ?? []
        );

    $_SESSION['extracted_skills'] =
        $skills;

    $recommendation = null;

    if (
        !empty(
            $_SESSION['career_jobs']
            ?? []
        ) &&
        !empty($skills)
    ) {

        $recommendation =
            calculateLocalJobRecommendation(
                $_SESSION['career_jobs'],
                $skills
            );

        if ($recommendation !== null) {

            saveDynamicRecommendation(
                $recommendation
            );
        }
    }

    jsonResponse([
        "status" =>
            "success",

        "skills" =>
            $skills,

        "recommendation" =>
            $recommendation
    ]);
}


/* ============================================================
   UPLOAD RESUME
   ============================================================ */

if ($action === 'upload_resume') {

    $file = $_FILES['resume_file'] ?? ($_FILES['resume'] ?? null);

    if (!$file || !isset($file['error']) || $file['error'] !== UPLOAD_ERR_OK) {
        $uploadErrorMsg = "Please select a valid resume file.";
        if ($file && isset($file['error'])) {
            switch ($file['error']) {
                case UPLOAD_ERR_INI_SIZE:
                case UPLOAD_ERR_FORM_SIZE:
                    $uploadErrorMsg = "The uploaded file exceeds the allowed file size limit.";
                    break;
                case UPLOAD_ERR_PARTIAL:
                    $uploadErrorMsg = "The resume file was only partially uploaded. Please try again.";
                    break;
                case UPLOAD_ERR_NO_FILE:
                    $uploadErrorMsg = "No resume file was uploaded. Please choose a file.";
                    break;
                default:
                    $uploadErrorMsg = "File upload failed (error code " . $file['error'] . ").";
                    break;
            }
        }
        jsonResponse([
            "status" => "error",
            "message" => $uploadErrorMsg
        ], 400);
    }

    $extension =
        strtolower(
            pathinfo(
                $file['name'],
                PATHINFO_EXTENSION
            )
        );

    if (
        !in_array(
            $extension,
            [
                'pdf',
                'docx',
                'txt'
            ],
            true
        )
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "Unsupported file type. Please upload PDF, DOCX or TXT."
        ], 400);
    }

    $baseUploadDir = '';

    if (
        is_dir('/var/data') &&
        is_writable('/var/data')
    ) {

        $baseUploadDir =
            '/var/data';

    } else {

        $baseUploadDir =
            sys_get_temp_dir();
    }

    $uploadDir =
        rtrim(
            $baseUploadDir,
            DIRECTORY_SEPARATOR
        ) .
        DIRECTORY_SEPARATOR .
        'skill_gap_predictor_uploads' .
        DIRECTORY_SEPARATOR;

    if (!is_dir($uploadDir)) {

        @mkdir(
            $uploadDir,
            0777,
            true
        );
    }

    if (
        !is_dir($uploadDir) ||
        !is_writable($uploadDir)
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "Resume storage directory is not writable."
        ], 500);
    }

    $safeName =
        preg_replace(
            '/[^A-Za-z0-9._-]/',
            '_',
            basename(
                $file['name']
            )
        );

    $targetPath =
        $uploadDir .
        uniqid(
            'resume_',
            true
        ) .
        '_' .
        $safeName;

    if (
        !move_uploaded_file(
            $file['tmp_name'],
            $targetPath
        )
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "Unable to store the uploaded resume."
        ], 500);
    }

    $parseRes =
        callPythonBridge(
            "parse_resume",
            [
                "file_path" =>
                    $targetPath,

                "file_name" =>
                    $file['name']
            ]
        );

    if (
        !isset(
            $parseRes['status']
        ) ||
        $parseRes['status'] !==
        'success'
    ) {

        @unlink(
            $targetPath
        );

        jsonResponse(
            is_array($parseRes)
                ? $parseRes
                : [
                    "status" =>
                        "error",

                    "message" =>
                        "Resume parsing failed."
                ],
            400
        );
    }

    $_SESSION['parsed_resume'] =
        $parseRes['parsed_resume']
        ?? [];

    $_SESSION['extracted_skills'] =
        normalizeSkills(
            $parseRes['extracted_skills']
            ?? []
        );

    $_SESSION['ats_score'] =
        isset(
            $parseRes['ats_score']
        ) &&
        is_numeric(
            $parseRes['ats_score']
        )
            ? (float)
                $parseRes['ats_score']
            : null;

    $contact =
        $_SESSION['parsed_resume']['contact_info']
        ?? [];

    $linkedin =
        trim(
            $contact['linkedin']
            ?? ''
        );

    $github =
        trim(
            $contact['github']
            ?? ''
        );

    if ($linkedin !== '') {

        $_SESSION['user']['linkedin'] =
            $linkedin;
    }

    if ($github !== '') {

        $_SESSION['user']['github'] =
            $github;
    }

    $recommendation = null;

    if (
        !empty(
            $_SESSION['career_jobs']
            ?? []
        ) &&
        !empty(
            $_SESSION['extracted_skills']
        )
    ) {

        $recommendation =
            calculateLocalJobRecommendation(
                $_SESSION['career_jobs'],
                $_SESSION['extracted_skills']
            );

        if ($recommendation !== null) {

            saveDynamicRecommendation(
                $recommendation
            );
        }
    }

    $requiredSkills =
        normalizeSkills(
            $_POST['required_skills']
            ?? (
                $_SESSION['required_skills']
                ?? []
            )
        );

    $_SESSION['required_skills'] =
        $requiredSkills;

    $targetCompany =
        trim(
            $_POST['target_company']
            ?? (
                $_SESSION['target_company']
                ?? ''
            )
        );

    $targetRole =
        trim(
            $_POST['target_role']
            ?? (
                $_SESSION['target_role']
                ?? ''
            )
        );

    if (
        $recommendation === null
    ) {

        $_SESSION['target_company'] =
            $targetCompany;

        $_SESSION['target_role'] =
            $targetRole;
    }

    if (
        $recommendation !== null
    ) {

        $requiredSkills =
            normalizeSkills(
                $recommendation['required_skills']
                ?? []
            );

        $_SESSION['required_skills'] =
            $requiredSkills;

        $targetCompany =
            $recommendation['company']
            ?? '';

        $targetRole =
            $recommendation['role']
            ?? '';
    }

    $metrics = [];

    if (
        !empty($requiredSkills)
    ) {

        $metrics =
            callPythonBridge(
                "calculate_metrics",
                [
                    "extracted_skills" =>
                        $_SESSION['extracted_skills'],

                    "required_skills" =>
                        $requiredSkills,

                    "ats_score" =>
                        $_SESSION['ats_score'],

                    "target_company" =>
                        $targetCompany,

                    "target_role" =>
                        $targetRole,

                    "section_presence" =>
                        $_SESSION['parsed_resume']['section_presence']
                        ?? []
                ]
            );

        if (
            !is_array($metrics)
        ) {
            $metrics = [];
        }
    }

    if (
        !empty($requiredSkills)
    ) {

        saveResumeEvaluation(
            $current_user['id'],
            $file['name'],
            $parseRes['detected_domain']
            ?? '',
            $_SESSION['ats_score'],
            $metrics['readiness_pct']
            ?? 0,
            $metrics['confidence_pct']
            ?? 0,
            $metrics['matched_skills']
            ?? [],
            $metrics['missing_skills']
            ?? [],
            [
                "Tailor resume content to the selected job.",
                "Add measurable results to project descriptions.",
                "Develop the missing technical skills."
            ]
        );
    }

    @unlink(
        $targetPath
    );

    jsonResponse([
        "status" =>
            "success",

        "message" =>
            "Resume parsed successfully.",

        "data" =>
            $parseRes,

        "metrics" =>
            $metrics,

        "extracted_skills" =>
            $_SESSION['extracted_skills'],

        "ats_score" =>
            $_SESSION['ats_score'],

        "recommended_job" =>
            $recommendation
            ?? (
                $_SESSION['recommended_job']
                ?? null
            )
    ]);
}


/* ============================================================
   SAMPLE RESUME
   ============================================================ */

if ($action === 'load_sample') {

    $sampleRes =
        callPythonBridge(
            "parse_sample",
            [
                "name" =>
                    $current_user['name']
                    ?? '',

                "email" =>
                    $current_user['email']
                    ?? '',

                "branch" =>
                    $current_user['branch']
                    ?? '',

                "year" =>
                    $current_user['graduation_year']
                    ?? date('Y')
            ]
        );

    if (
        isset(
            $sampleRes['status']
        ) &&
        $sampleRes['status'] ===
        'success'
    ) {

        $_SESSION['parsed_resume'] =
            $sampleRes['parsed_resume']
            ?? [];

        $_SESSION['extracted_skills'] =
            normalizeSkills(
                $sampleRes['extracted_skills']
                ?? []
            );

        $_SESSION['ats_score'] =
            $sampleRes['ats_score']
            ?? null;

        $recommendation = null;

        if (
            !empty(
                $_SESSION['career_jobs']
                ?? []
            ) &&
            !empty(
                $_SESSION['extracted_skills']
            )
        ) {

            $recommendation =
                calculateLocalJobRecommendation(
                    $_SESSION['career_jobs'],
                    $_SESSION['extracted_skills']
                );

            if (
                $recommendation !== null
            ) {

                saveDynamicRecommendation(
                    $recommendation
                );
            }
        }

        jsonResponse([
            "status" =>
                "success",

            "data" =>
                $sampleRes,

            "recommended_job" =>
                $recommendation
        ]);
    }

    jsonResponse(
        $sampleRes
    );
}


/* ============================================================
   SCRAPE CAREER URL
   ============================================================ */

if ($action === 'scrape_url') {

    $url =
        trim(
            $_POST['url'] ?? ''
        );

    if ($url === '') {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "Please enter a career URL."
        ], 400);
    }

    if (
        !filter_var(
            $url,
            FILTER_VALIDATE_URL
        )
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "Please enter a valid career URL."
        ], 400);
    }

    $scheme =
        strtolower(
            parse_url(
                $url,
                PHP_URL_SCHEME
            ) ?? ''
        );

    if (
        !in_array(
            $scheme,
            [
                'http',
                'https'
            ],
            true
        )
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "Only HTTP and HTTPS career URLs are supported."
        ], 400);
    }

    $_SESSION['career_jobs'] =
        [];

    $_SESSION['career_url'] =
        $url;

    $_SESSION['recommended_job'] =
        null;

    $_SESSION['target_company'] =
        '';

    $_SESSION['target_role'] =
        '';

    $_SESSION['required_skills'] =
        [];


    /* --------------------------------------------------------
       FIRST: PYTHON SCRAPER
       -------------------------------------------------------- */

    $pythonRes =
        callPythonBridge(
            "scrape_url",
            [
                "url" =>
                    $url
            ]
        );

    $jobs = [];

    if (
        is_array($pythonRes)
    ) {

        $jobs =
            findJobsInResponse(
                $pythonRes
            );
    }


    /* --------------------------------------------------------
       SECOND: GENERIC PHP FALLBACK
       -------------------------------------------------------- */

    $scraperMessages = [];

    if (
        empty($jobs)
    ) {

        $fallback =
            scrapeCareerPageFallback(
                $url
            );

        if (
            !empty(
                $fallback['jobs']
            )
        ) {

            $jobs =
                $fallback['jobs'];
        }

        if (
            !empty(
                $fallback['message']
            )
        ) {

            $scraperMessages[] =
                $fallback['message'];
        }
    }


    /* --------------------------------------------------------
       THIRD: SOURCE-SPECIFIC FALLBACK
       -------------------------------------------------------- */

    if (
        empty($jobs)
    ) {

        $sourceFallback =
            scrapeSourceSpecificCareerPage(
                $url
            );

        if (
            !empty(
                $sourceFallback['jobs']
            )
        ) {

            $jobs =
                $sourceFallback['jobs'];
        }

        if (
            !empty(
                $sourceFallback['message']
            )
        ) {

            $scraperMessages[] =
                $sourceFallback['message'];
        }
    }


    $jobs =
        normalizeCareerJobs(
            $jobs
        );

    storeCareerJobs(
        $jobs,
        $url
    );


    /* --------------------------------------------------------
       DYNAMIC RECOMMENDATION
       -------------------------------------------------------- */

    $recommendation = null;

    if (
        !empty(
            $_SESSION['extracted_skills']
            ?? []
        ) &&
        !empty(
            $_SESSION['career_jobs']
        )
    ) {

        $recommendation =
            calculateLocalJobRecommendation(
                $_SESSION['career_jobs'],
                $_SESSION['extracted_skills']
            );

        if (
            $recommendation !== null
        ) {

            saveDynamicRecommendation(
                $recommendation
            );
        }
    }


    /* --------------------------------------------------------
       ZERO RESULTS
       -------------------------------------------------------- */

    if (
        empty(
            $_SESSION['career_jobs']
        )
    ) {

        $pythonMessage =
            is_array($pythonRes)
                ? (
                    $pythonRes['message']
                    ?? ''
                )
                : '';

        jsonResponse([
            "status" =>
                "success",

            "message" =>
                "No individual job listings could be extracted from this career URL.",

            "career_url" =>
                $_SESSION['career_url'],

            "jobs" =>
                [],

            "career_jobs" =>
                [],

            "job_count" =>
                0,

            "recommendation" =>
                null,

            "scraper_message" =>
                $pythonMessage,

            "diagnostics" =>
                $scraperMessages
        ]);
    }


    /* --------------------------------------------------------
       SUCCESSFUL RESULT
       -------------------------------------------------------- */

    $jobCount =
        count(
            $_SESSION['career_jobs']
        );

    jsonResponse([
        "status" =>
            "success",

        "message" =>
            $jobCount .
            " job(s) found.",

        "career_url" =>
            $_SESSION['career_url'],

        "jobs" =>
            $_SESSION['career_jobs'],

        "career_jobs" =>
            $_SESSION['career_jobs'],

        "job_count" =>
            $jobCount,

        "recommendation" =>
            $recommendation
    ]);
}


/* ============================================================
   RECOMMEND JOB
   ============================================================ */

if ($action === 'recommend_job') {

    $jobs =
        $_SESSION['career_jobs']
        ?? [];

    $resumeSkills =
        $_SESSION['extracted_skills']
        ?? [];

    if (
        empty($jobs)
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "No jobs have been loaded. Enter a career URL first."
        ], 400);
    }

    if (
        empty($resumeSkills)
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "Please upload your resume before calculating the best matching role."
        ], 400);
    }

    $recommendation =
        calculateLocalJobRecommendation(
            $jobs,
            $resumeSkills
        );

    if (
        $recommendation === null
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "The available jobs do not contain enough skill information for matching."
        ], 400);
    }

    saveDynamicRecommendation(
        $recommendation
    );

    jsonResponse([
        "status" =>
            "success",

        "recommendation" =>
            $recommendation
    ]);
}


/* ============================================================
   GET METRICS
   ============================================================ */

if ($action === 'get_metrics') {

    $company =
        trim(
            $_POST['target_company']
            ?? (
                $_SESSION['target_company']
                ?? ''
            )
        );

    $role =
        trim(
            $_POST['target_role']
            ?? (
                $_SESSION['target_role']
                ?? ''
            )
        );

    $requiredSkills =
        normalizeSkills(
            $_POST['required_skills']
            ?? (
                $_SESSION['required_skills']
                ?? []
            )
        );

    if (
        empty($role)
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "No job role has been selected."
        ], 400);
    }

    if (
        empty($requiredSkills)
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "No job requirements are available. Please enter a career URL and select a job."
        ], 400);
    }

    $_SESSION['target_company'] =
        $company;

    $_SESSION['target_role'] =
        $role;

    $_SESSION['required_skills'] =
        $requiredSkills;

    $metrics =
        callPythonBridge(
            "calculate_metrics",
            [
                "extracted_skills" =>
                    $_SESSION['extracted_skills']
                    ?? [],

                "required_skills" =>
                    $requiredSkills,

                "ats_score" =>
                    $_SESSION['ats_score']
                    ?? null,

                "target_company" =>
                    $company,

                "target_role" =>
                    $role,

                "section_presence" =>
                    $_SESSION['parsed_resume']['section_presence']
                    ?? []
            ]
        );

    if (
        !is_array($metrics)
    ) {
        $metrics = [];
    }

    $metrics['ats_score'] =
        $_SESSION['ats_score']
        ?? null;

    $metrics['matched_skills'] =
        normalizeSkills(
            $metrics['matched_skills']
            ?? []
        );

    $metrics['missing_skills'] =
        normalizeSkills(
            $metrics['missing_skills']
            ?? []
        );

    jsonResponse(
        $metrics
    );
}


/* ============================================================
   RANK JOBS
   ============================================================ */

if ($action === 'rank_jobs') {

    $domainFilter =
        $_POST['domain_filter']
        ?? 'All Domains';

    $careerJobs =
        $_SESSION['career_jobs']
        ?? [];

    if (
        empty($careerJobs)
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "No career jobs available. Please enter a career URL first."
        ], 400);
    }

    $res =
        callPythonBridge(
            "rank_jobs",
            [
                "extracted_skills" =>
                    $_SESSION['extracted_skills']
                    ?? [],

                "domain_filter" =>
                    $domainFilter,

                "jobs" =>
                    $careerJobs
            ]
        );

    $pythonJobs =
        findJobsInResponse(
            $res
        );

    if (
        !empty($pythonJobs)
    ) {

        jsonResponse([
            "status" =>
                "success",

            "jobs" =>
                $pythonJobs
        ]);
    }

    $ranked = [];

    foreach (
        $careerJobs
        as $job
    ) {

        $recommendation =
            calculateLocalJobRecommendation(
                [$job],
                $_SESSION['extracted_skills']
                ?? []
            );

        if (
            $recommendation !== null
        ) {

            $ranked[] =
                $recommendation;
        }
    }

    usort(
        $ranked,
        function ($a, $b) {

            $scoreA =
                (float)(
                    $a['score']
                    ?? 0
                );

            $scoreB =
                (float)(
                    $b['score']
                    ?? 0
                );

            return
                $scoreB <=>
                $scoreA;
        }
    );

    jsonResponse([
        "status" =>
            "success",

        "jobs" =>
            $ranked
    ]);
}


/* ============================================================
   ROADMAP
   ============================================================ */

if ($action === 'get_roadmap') {

    $missingSkills =
        normalizeSkills(
            $_POST['missing_skills']
            ?? []
        );

    $targetRole =
        trim(
            $_POST['target_role']
            ?? (
                $_SESSION['target_role']
                ?? ''
            )
        );

    $targetCompany =
        trim(
            $_POST['target_company']
            ?? (
                $_SESSION['target_company']
                ?? ''
            )
        );

    if (
        $targetRole === ''
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "No target job role has been selected."
        ], 400);
    }

    $res =
        callPythonBridge(
            "generate_roadmap",
            [
                "missing_skills" =>
                    $missingSkills,

                "target_role" =>
                    $targetRole,

                "target_company" =>
                    $targetCompany
            ]
        );

    jsonResponse(
        $res
    );
}


/* ============================================================
   INTERVIEW
   ============================================================ */

if ($action === 'get_interview') {

    $matched =
        normalizeSkills(
            $_POST['matched_skills']
            ?? []
        );

    $missing =
        normalizeSkills(
            $_POST['missing_skills']
            ?? []
        );

    $targetRole =
        trim(
            $_POST['target_role']
            ?? (
                $_SESSION['target_role']
                ?? ''
            )
        );

    if (
        $targetRole === ''
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "No target job role has been selected."
        ], 400);
    }

    $res =
        callPythonBridge(
            "generate_interview",
            [
                "target_role" =>
                    $targetRole,

                "matched_skills" =>
                    $matched,

                "missing_skills" =>
                    $missing
            ]
        );

    jsonResponse(
        $res
    );
}


/* ============================================================
   AI INTERVIEW ASSISTANT
   ============================================================ */

if ($action === 'ask_interview_ai') {

    $prompt =
        trim(
            $_POST['prompt'] ?? ''
        );

    $targetRole =
        trim(
            $_POST['target_role']
            ?? (
                $_SESSION['target_role']
                ?? ''
            )
        );

    $targetCompany =
        trim(
            $_POST['target_company']
            ?? (
                $_SESSION['target_company']
                ?? ''
            )
        );

    if (
        $targetRole === ''
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "No target job role has been selected."
        ], 400);
    }

    $res =
        callPythonBridge(
            "ask_interview_ai",
            [
                "prompt" =>
                    $prompt,

                "target_role" =>
                    $targetRole,

                "target_company" =>
                    $targetCompany
            ]
        );

    jsonResponse(
        $res
    );
}


/* ============================================================
   EVALUATE INTERVIEW ANSWER
   ============================================================ */

if ($action === 'evaluate_answer') {

    $question =
        trim(
            $_POST['question']
            ?? ''
        );

    $userAnswer =
        trim(
            $_POST['user_answer']
            ?? ''
        );

    $targetRole =
        trim(
            $_POST['target_role']
            ?? (
                $_SESSION['target_role']
                ?? ''
            )
        );

    if (
        $targetRole === ''
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "No target job role has been selected."
        ], 400);
    }

    $res =
        callPythonBridge(
            "evaluate_answer",
            [
                "question" =>
                    $question,

                "user_answer" =>
                    $userAnswer,

                "target_role" =>
                    $targetRole
            ]
        );

    jsonResponse(
        $res
    );
}


/* ============================================================
   DOWNLOAD PDF
   ============================================================ */

if ($action === 'download_pdf') {

    $targetCompany =
        trim(
            $_POST['target_company']
            ?? (
                $_SESSION['target_company']
                ?? ''
            )
        );

    $targetRole =
        trim(
            $_POST['target_role']
            ?? (
                $_SESSION['target_role']
                ?? ''
            )
        );

    $requiredSkills =
        normalizeSkills(
            $_POST['required_skills']
            ?? (
                $_SESSION['required_skills']
                ?? []
            )
        );

    if (
        $targetRole === ''
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "No target job role is available."
        ], 400);
    }

    if (
        empty($requiredSkills)
    ) {

        jsonResponse([
            "status" =>
                "error",

            "message" =>
                "No job requirements are available for the report."
        ], 400);
    }

    $metrics =
        callPythonBridge(
            "calculate_metrics",
            [
                "extracted_skills" =>
                    $_SESSION['extracted_skills']
                    ?? [],

                "required_skills" =>
                    $requiredSkills,

                "ats_score" =>
                    $_SESSION['ats_score']
                    ?? null,

                "target_company" =>
                    $targetCompany,

                "target_role" =>
                    $targetRole,

                "section_presence" =>
                    $_SESSION['parsed_resume']['section_presence']
                    ?? []
            ]
        );

    if (
        !is_array($metrics)
    ) {
        $metrics = [];
    }

    $roadmapRes =
        callPythonBridge(
            "generate_roadmap",
            [
                "missing_skills" =>
                    $metrics['missing_skills']
                    ?? [],

                "target_role" =>
                    $targetRole,

                "target_company" =>
                    $targetCompany
            ]
        );

    $recommendations = [];

    if (
        !empty(
            $metrics['missing_skills']
        )
    ) {

        $firstMissing =
            $metrics['missing_skills'][0]
            ?? '';

        if (
            $firstMissing !== ''
        ) {

            $recommendations[] =
                "Prioritize learning " .
                $firstMissing .
                " and build a practical project using it.";
        }
    }

    $recommendations[] =
        "Tailor the resume to the selected job requirements.";

    $recommendations[] =
        "Use measurable results in project descriptions.";

    $pdfRes =
        callPythonBridge(
            "generate_pdf",
            [
                "student_name" =>
                    $current_user['name']
                    ?? 'Student',

                "target_role" =>
                    $targetRole,

                "target_company" =>
                    $targetCompany,

                "domain" =>
                    $metrics['detected_domain']
                    ?? '',

                "ats_score" =>
                    $_SESSION['ats_score']
                    ?? null,

                "readiness_score" =>
                    $metrics['readiness_pct']
                    ?? 0,

                "confidence_score" =>
                    $metrics['confidence_pct']
                    ?? 0,

                "resume_strength" =>
                    $metrics['strength_label']
                    ?? '',

                "matched_skills" =>
                    $metrics['matched_skills']
                    ?? [],

                "missing_skills" =>
                    $metrics['missing_skills']
                    ?? [],

                "recommendations" =>
                    $recommendations,

                "roadmap_phases" =>
                    $roadmapRes['roadmap']['phases']
                    ?? []
            ]
        );

    if (
        !empty(
            $pdfRes['pdf_b64']
        )
    ) {

        $pdfData =
            base64_decode(
                $pdfRes['pdf_b64'],
                true
            );

        if (
            $pdfData === false
        ) {

            jsonResponse([
                "status" =>
                    "error",

                "message" =>
                    "Generated PDF data is invalid."
            ], 500);
        }

        header_remove(
            'Content-Type'
        );

        header(
            'Content-Type: application/pdf'
        );

        $safeName =
            preg_replace(
                '/[^A-Za-z0-9_-]/',
                '_',
                $current_user['name']
                ?? 'Student'
            );

        header(
            'Content-Disposition: attachment; filename="Progress_Report_' .
            $safeName .
            '.pdf"'
        );

        header(
            'Content-Length: ' .
            strlen($pdfData)
        );

        echo $pdfData;

        exit;
    }

    jsonResponse([
        "status" =>
            "error",

        "message" =>
            "PDF generation failed."
    ], 500);
}


/* ============================================================
   INVALID ACTION
   ============================================================ */

jsonResponse([
    "status" =>
        "error",

    "message" =>
        "Invalid API action: " .
        $action
], 400);