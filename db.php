<?php

/*
|--------------------------------------------------------------------------
| Skill Gap Predictor - Database
|--------------------------------------------------------------------------
*/

/*
 * Select a writable database location.
 *
 * Render persistent disk:
 * /var/data
 */

if (
    is_dir('/var/data') &&
    is_writable('/var/data')
) {

    define(
        'DB_PATH',
        '/var/data/career_navigation.db'
    );

} elseif (
    is_writable(__DIR__)
) {

    define(
        'DB_PATH',
        __DIR__ .
        DIRECTORY_SEPARATOR .
        'career_navigation.db'
    );

} else {

    define(
        'DB_PATH',
        sys_get_temp_dir() .
        DIRECTORY_SEPARATOR .
        'career_navigation.db'
    );
}


/*
|--------------------------------------------------------------------------
| Database Connection
|--------------------------------------------------------------------------
*/

function getDB()
{
    static $pdo = null;

    if ($pdo !== null) {
        return $pdo;
    }

    $directory =
        dirname(DB_PATH);


    /*
     * Create directory if required.
     */

    if (
        !is_dir($directory)
    ) {

        @mkdir(
            $directory,
            0775,
            true
        );
    }


    $pdo =
        new PDO(
            'sqlite:' . DB_PATH
        );


    $pdo->setAttribute(
        PDO::ATTR_ERRMODE,
        PDO::ERRMODE_EXCEPTION
    );


    $pdo->setAttribute(
        PDO::ATTR_DEFAULT_FETCH_MODE,
        PDO::FETCH_ASSOC
    );


    /*
     * SQLite settings.
     */

    $pdo->exec(
        'PRAGMA foreign_keys = ON'
    );

    $pdo->exec(
        'PRAGMA journal_mode = WAL'
    );


    return $pdo;
}


/*
|--------------------------------------------------------------------------
| Initialize Database
|--------------------------------------------------------------------------
*/

function initDatabase()
{
    $pdo = getDB();


    $pdo->exec("
        CREATE TABLE IF NOT EXISTS students (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            university TEXT DEFAULT '',

            branch TEXT DEFAULT '',

            major TEXT DEFAULT '',

            graduation_year TEXT DEFAULT '',

            linkedin TEXT DEFAULT '',

            github TEXT DEFAULT '',

            target_company TEXT DEFAULT '',

            target_role TEXT DEFAULT '',

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP

        )
    ");


    $pdo->exec("
        CREATE TABLE IF NOT EXISTS resume_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            filename TEXT DEFAULT '',

            extracted_skills TEXT DEFAULT '',

            ats_score REAL DEFAULT 0,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES students(id)
                ON DELETE CASCADE

        )
    ");
}


/*
|--------------------------------------------------------------------------
| Initialize
|--------------------------------------------------------------------------
*/

initDatabase();


/*
|--------------------------------------------------------------------------
| Register User
|--------------------------------------------------------------------------
*/

function registerUser(
    $name,
    $email,
    $password,
    $university = '',
    $branch = '',
    $major = '',
    $graduationYear = '',
    $linkedin = '',
    $github = '',
    $targetCompany = '',
    $targetRole = ''
) {

    $pdo = getDB();


    /*
     * No predefined company.
     * No predefined role.
     */

    $targetCompany =
        trim($targetCompany);

    $targetRole =
        trim($targetRole);


    $passwordHash =
        password_hash(
            $password,
            PASSWORD_DEFAULT
        );


    $stmt =
        $pdo->prepare("
            INSERT INTO students
            (
                name,
                email,
                password,
                university,
                branch,
                major,
                graduation_year,
                linkedin,
                github,
                target_company,
                target_role
            )
            VALUES
            (
                :name,
                :email,
                :password,
                :university,
                :branch,
                :major,
                :graduation_year,
                :linkedin,
                :github,
                :target_company,
                :target_role
            )
        ");


    $stmt->execute([

        ':name' =>
            trim($name),

        ':email' =>
            strtolower(
                trim($email)
            ),

        ':password' =>
            $passwordHash,

        ':university' =>
            trim($university),

        ':branch' =>
            trim($branch),

        ':major' =>
            trim($major),

        ':graduation_year' =>
            trim($graduationYear),

        ':linkedin' =>
            trim($linkedin),

        ':github' =>
            trim($github),

        ':target_company' =>
            $targetCompany,

        ':target_role' =>
            $targetRole
    ]);


    return $pdo->lastInsertId();
}


/*
|--------------------------------------------------------------------------
| Get User By Email
|--------------------------------------------------------------------------
*/

function getUserByEmail($email)
{
    $pdo = getDB();


    $stmt =
        $pdo->prepare("
            SELECT *
            FROM students
            WHERE email = :email
            LIMIT 1
        ");


    $stmt->execute([
        ':email' =>
            strtolower(
                trim($email)
            )
    ]);


    return $stmt->fetch();
}


/*
|--------------------------------------------------------------------------
| Get User By ID
|--------------------------------------------------------------------------
*/

function getUserById($id)
{
    $pdo = getDB();


    $stmt =
        $pdo->prepare("
            SELECT *
            FROM students
            WHERE id = :id
            LIMIT 1
        ");


    $stmt->execute([
        ':id' => $id
    ]);


    return $stmt->fetch();
}