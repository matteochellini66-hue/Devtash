DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS snippets;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email_hash TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    titolo TEXT NOT NULL,
    linguaggio TEXT NOT NULL,
    codice TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);