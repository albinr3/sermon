-- Script SQL para borrar completamente la base de datos
-- Uso: psql -h localhost -U sermon -d sermon -f reset_db.sql
-- O usando la conexión desde docker-compose:
-- docker compose exec postgres psql -U sermon -d sermon -f /tmp/reset_db.sql

-- Desconectar todas las conexiones activas
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = current_database()
  AND pid <> pg_backend_pid();

-- Deshabilitar checks de foreign keys temporalmente
SET session_replication_role = 'replica';

-- Eliminar todas las tablas (CASCADE para eliminar dependencias)
DO $$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
        RAISE NOTICE 'Eliminada tabla: %', r.tablename;
    END LOOP;
END $$;

-- Eliminar todos los tipos ENUM
DO $$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT typname 
        FROM pg_type 
        WHERE typtype = 'e'
        AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    ) 
    LOOP
        EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
        RAISE NOTICE 'Eliminado tipo ENUM: %', r.typname;
    END LOOP;
END $$;

-- Eliminar extensión vector si existe
DROP EXTENSION IF EXISTS vector CASCADE;

-- Rehabilitar checks de foreign keys
SET session_replication_role = 'origin';

-- Verificar que todo esté borrado
SELECT 
    'Tablas restantes: ' || COUNT(*)::text as status
FROM pg_tables 
WHERE schemaname = 'public';

SELECT 
    'Tipos ENUM restantes: ' || COUNT(*)::text as status
FROM pg_type 
WHERE typtype = 'e'
AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');

DO $$ 
BEGIN
    RAISE NOTICE 'Base de datos borrada completamente. Ejecuta: alembic upgrade head';
END $$;
