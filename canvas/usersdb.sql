CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    semester_begin TEXT,
    url TEXT,
    bid TEXT,
    canvas_id INTEGER,
    canvas_name TEXT,
    timeformat INTEGER,
    background_image TEXT
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    course_id INTEGER,
    course_name TEXT,
    type INTEGER,
    maxshow INTEGER,
    display_order INTEGER,
    msg TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
    UNIQUE(user_id, course_id)
);

CREATE TABLE checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type INTEGER,
    item_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id)
    UNIQUE(user_id, item_id)
);

CREATE TABLE user_cache (
    user_id INTEGER PRIMARY KEY,
    html TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
