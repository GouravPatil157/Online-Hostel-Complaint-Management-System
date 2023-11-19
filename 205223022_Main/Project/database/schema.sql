CREATE DATABASE IF NOT EXISTS users;

CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT);

INSERT INTO users (username, password) VALUES ("admin", "nitt@admin");

INSERT INTO users (username, password) VALUES ("h123", "nitt@123");

INSERT INTO users (username, password) VALUES ("h234", "nitt@234");

INSERT INTO users (username, password) VALUES ("h345", "nitt@345");

INSERT INTO users (username, password) VALUES ("h456", "nitt@456");

INSERT INTO users (username, password) VALUES ("h567", "nitt@567");