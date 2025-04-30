CREATE TABLE items (
    item_id bigint PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price DOUBLE PRECISION NOT NULL
);

CREATE USER nifi_loader WITH PASSWORD 'nifi_loader_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE items TO nifi_loader;