-- Runs automatically the first time the postgres container initializes its
-- data volume (official postgres image behavior for /docker-entrypoint-initdb.d).
-- Keeps the test suite off the dev database entirely.
CREATE DATABASE urlshortener_test;
