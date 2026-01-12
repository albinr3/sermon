#!/usr/bin/env python3
"""
Script para borrar completamente la base de datos y empezar desde cero.
Elimina todas las tablas, tipos ENUM, extensiones y el historial de Alembic.
"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if BASE_DIR not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

from src.config import settings


def drop_all_tables(engine):
    """Elimina todas las tablas, tipos ENUM y extensiones."""
    with engine.connect() as conn:
        # Iniciar transacción
        trans = conn.begin()
        try:
            # Obtener inspector
            inspector = inspect(engine)
            
            # 1. Eliminar todas las tablas (en orden correcto por foreign keys)
            tables = inspector.get_table_names()
            print(f"Encontradas {len(tables)} tablas: {', '.join(tables)}")
            
            if tables:
                # Deshabilitar checks de foreign keys temporalmente
                conn.execute(text("SET session_replication_role = 'replica'"))
                
                # Eliminar tablas (CASCADE para eliminar dependencias)
                for table in tables:
                    print(f"Eliminando tabla: {table}")
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                
                # Rehabilitar checks
                conn.execute(text("SET session_replication_role = 'origin'"))
            
            # 2. Eliminar todos los tipos ENUM
            result = conn.execute(text("""
                SELECT typname 
                FROM pg_type 
                WHERE typtype = 'e'
                AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            """))
            enums = [row[0] for row in result]
            
            if enums:
                print(f"Encontrados {len(enums)} tipos ENUM: {', '.join(enums)}")
                for enum_name in enums:
                    print(f"Eliminando tipo ENUM: {enum_name}")
                    conn.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))
            
            # 3. Eliminar extensiones (opcional, vector si existe)
            extensions_result = conn.execute(text("""
                SELECT extname 
                FROM pg_extension 
                WHERE extname = 'vector'
            """))
            if extensions_result.fetchone():
                print("Eliminando extensión: vector")
                conn.execute(text("DROP EXTENSION IF EXISTS vector CASCADE"))
            
            # 4. Confirmar transacción
            trans.commit()
            print("\n✓ Base de datos borrada completamente")
            
        except Exception as e:
            trans.rollback()
            print(f"\n✗ Error al borrar base de datos: {e}")
            raise


def main():
    """Función principal."""
    print("=" * 60)
    print("RESET COMPLETO DE BASE DE DATOS")
    print("=" * 60)
    
    # Ocultar contraseña en el mensaje
    db_url_display = settings.database_url
    if "@" in db_url_display:
        parts = db_url_display.split("@")
        if "://" in parts[0]:
            protocol_user = parts[0].split("://")[0] + "://"
            rest = parts[0].split("://")[1]
            if ":" in rest:
                user = rest.split(":")[0]
                db_url_display = f"{protocol_user}{user}:****@{parts[1]}"
    
    print(f"\nConexión: {db_url_display}")
    
    confirm = input("\n⚠️  ¿Estás seguro de borrar TODA la base de datos? (escribe 'si' para confirmar): ")
    if confirm.lower() != 'si':
        print("Operación cancelada.")
        return
    
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        
        # Verificar conexión
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("\n✓ Conexión exitosa")
        
        # Borrar todo
        drop_all_tables(engine)
        
        print("\n" + "=" * 60)
        print("PRÓXIMOS PASOS:")
        print("=" * 60)
        print("\nEjecuta el siguiente comando para recrear la base de datos:")
        print("\n  cd apps/api")
        print("  alembic upgrade head")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
