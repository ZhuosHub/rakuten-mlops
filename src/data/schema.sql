DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS labels;

CREATE TABLE products(
  id INTEGER PRIMARY KEY,
  designation TEXT,                -- <- this column must exist
  description TEXT,
  productid TEXT,
  imageid TEXT,
  split TEXT CHECK(split IN ('train','test')) NOT NULL
);

CREATE TABLE labels(
  id INTEGER PRIMARY KEY,
  prdtypecode INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_products_split ON products(split);
CREATE INDEX IF NOT EXISTS idx_labels_code   ON labels(prdtypecode);
