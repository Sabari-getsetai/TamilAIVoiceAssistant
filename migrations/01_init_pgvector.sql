-- Initialize database with pgVector extension
-- This script runs automatically when the PostgreSQL container starts

-- Enable the pgVector extension for similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify pgVector extension is available
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Create a function to check vector similarity (cosine distance)
CREATE OR REPLACE FUNCTION cosine_distance(a vector, b vector)
RETURNS float AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$ LANGUAGE plpgsql;

-- Create a function to check vector similarity (L2 distance)
CREATE OR REPLACE FUNCTION l2_distance(a vector, b vector)
RETURNS float AS $$
BEGIN
    RETURN a <-> b;
END;
$$ LANGUAGE plpgsql;

-- Create a function to check vector similarity (inner product)
CREATE OR REPLACE FUNCTION inner_product(a vector, b vector)
RETURNS float AS $$
BEGIN
    RETURN a <#> b;
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'pgVector extension initialized successfully';
END $$;