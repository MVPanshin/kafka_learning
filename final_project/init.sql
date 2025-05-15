CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    price_amount NUMERIC,
    price_currency TEXT,
    category TEXT,
    brand TEXT,
    stock_available INT,
    stock_reserved INT,
    sku TEXT,
    tags TEXT[],
    images JSONB[],
    created_at TEXT,
    updated_at TEXT,
    index TEXT,
    store_id TEXT
);

CREATE TABLE top_products (
    product_id TEXT PRIMARY KEY,
    name TEXT,
    category TEXT,
    brand TEXT,
    total_quantity BIGINT
);

CREATE USER etl_loader WITH PASSWORD 'etl_loader';
CREATE USER srv_search WITH PASSWORD 'srv_search';

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE products, top_products TO etl_loader;
GRANT SELECT ON TABLE products, top_products TO srv_search;
GRANT USAGE, CREATE ON SCHEMA public TO srv_search;

ALTER TABLE top_products owner to srv_search;