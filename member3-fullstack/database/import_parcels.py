"""
VIT MAPATHON — Member 3 (Full Stack / GIS Application Engineer)
PostGIS Importer Script: Ingests classified_parcels.geojson into PostgreSQL / PostGIS.
"""

import os
import sys
import json
import argparse
import logging
from typing import Optional, Dict, Any

try:
    import psycopg2
    from psycopg2.extras import execute_batch
except ImportError:
    psycopg2 = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("PostGIS_Importer")


def resolve_geojson_path(cli_path: Optional[str] = None) -> str:
    """Resolves GeoJSON input path prioritizing Member 1 output, then Member 3 inputs."""
    if cli_path and os.path.exists(cli_path):
        return os.path.abspath(cli_path)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    repo_root = os.path.abspath(os.path.join(base_dir, ".."))

    candidates = [
        os.path.join(repo_root, "member1-ml", "outputs", "classified_parcels.geojson"),
        os.path.join(base_dir, "inputs", "classified_parcels.geojson"),
    ]

    for cand in candidates:
        if os.path.exists(cand):
            return cand

    raise FileNotFoundError(
        "No classified_parcels.geojson found. Checked:\n" +
        "\n".join(f"  - {c}" for c in candidates)
    )


def import_geojson_to_postgis(
    geojson_path: str,
    db_config: Dict[str, Any],
    init_schema: bool = True,
    dry_run: bool = False
) -> int:
    """
    Ingests GeoJSON parcels into PostGIS agricultural_parcels table.
    """
    logger.info(f"Loading GeoJSON data from: {geojson_path}")
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    total_count = len(features)
    logger.info(f"Parsed {total_count} parcel features from GeoJSON.")

    if total_count == 0:
        logger.warning("GeoJSON contains 0 features. Nothing to import.")
        return 0

    if dry_run:
        logger.info("[DRY RUN] Validated GeoJSON structure. Skipping DB connection.")
        return total_count

    if psycopg2 is None:
        raise RuntimeError("psycopg2 is required for database import. Install with: pip install psycopg2-binary")

    conn_str = db_config.get("url")
    if conn_str:
        conn = psycopg2.connect(conn_str)
    else:
        conn = psycopg2.connect(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 5432),
            dbname=db_config.get("dbname", "postgres"),
            user=db_config.get("user", "postgres"),
            password=db_config.get("password", "postgres")
        )

    try:
        with conn.cursor() as cur:
            if init_schema:
                logger.info("Initializing PostGIS schema...")
                schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
                if os.path.exists(schema_path):
                    with open(schema_path, "r", encoding="utf-8") as sf:
                        try:
                            cur.execute(sf.read())
                            conn.commit()
                            logger.info("Schema applied successfully.")
                        except Exception as e:
                            conn.rollback()
                            logger.warning(
                                f"PostGIS schema execution note: {e}\n"
                                "If PostGIS extension is not installed in PostgreSQL, install it via PostGIS installer.\n"
                                "The FastAPI backend will automatically use the high-performance GeoJSON fallback."
                            )
                            raise e

            logger.info("Upserting parcels into agricultural_parcels...")
            upsert_sql = """
                INSERT INTO agricultural_parcels (
                    parcel_id,
                    predicted_crop,
                    confidence,
                    area_sq_km,
                    area_ha,
                    prob_paddy,
                    prob_banana,
                    prob_other,
                    geom
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
                )
                ON CONFLICT (parcel_id) DO UPDATE SET
                    predicted_crop = EXCLUDED.predicted_crop,
                    confidence = EXCLUDED.confidence,
                    area_sq_km = EXCLUDED.area_sq_km,
                    area_ha = EXCLUDED.area_ha,
                    prob_paddy = EXCLUDED.prob_paddy,
                    prob_banana = EXCLUDED.prob_banana,
                    prob_other = EXCLUDED.prob_other,
                    geom = EXCLUDED.geom,
                    updated_at = CURRENT_TIMESTAMP;
            """

            records = []
            for f in features:
                props = f.get("properties", {})
                geom = json.dumps(f.get("geometry", {}))
                records.append((
                    props.get("parcel_id"),
                    props.get("predicted_crop"),
                    float(props.get("confidence", 0.0)),
                    float(props.get("area_sq_km", 0.0)),
                    float(props.get("area_ha", 0.0)),
                    float(props.get("prob_paddy", 0.0)) if props.get("prob_paddy") is not None else None,
                    float(props.get("prob_banana", 0.0)) if props.get("prob_banana") is not None else None,
                    float(props.get("prob_other", 0.0)) if props.get("prob_other") is not None else None,
                    geom
                ))

            execute_batch(cur, upsert_sql, records, page_size=200)
            conn.commit()

            cur.execute("SELECT COUNT(*), SUM(area_sq_km) FROM agricultural_parcels;")
            db_count, db_area = cur.fetchone()
            logger.info(f"Successfully ingested {len(records)} parcels.")
            logger.info(f"Database table agricultural_parcels now contains {db_count} records covering {db_area:.2f} sq. km.")

        return len(records)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest classified parcels into PostGIS")
    parser.add_argument("--geojson", type=str, default=None, help="Path to classified_parcels.geojson")
    parser.add_argument("--host", type=str, default=os.getenv("POSTGRES_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("POSTGRES_PORT", 5432)))
    parser.add_argument("--dbname", type=str, default=os.getenv("POSTGRES_DB", "postgres"))
    parser.add_argument("--user", type=str, default=os.getenv("POSTGRES_USER", "postgres"))
    parser.add_argument("--password", type=str, default=os.getenv("POSTGRES_PASSWORD", "postgres"))
    parser.add_argument("--url", type=str, default=os.getenv("DATABASE_URL"))
    parser.add_argument("--no-init-schema", action="store_true", help="Skip schema initialization")
    parser.add_argument("--dry-run", action="store_true", help="Validate without database execution")

    args = parser.parse_args()
    geojson_path = resolve_geojson_path(args.geojson)

    db_config = {
        "url": args.url,
        "host": args.host,
        "port": args.port,
        "dbname": args.dbname,
        "user": args.user,
        "password": args.password,
    }

    try:
        import_geojson_to_postgis(
            geojson_path=geojson_path,
            db_config=db_config,
            init_schema=not args.no_init_schema,
            dry_run=args.dry_run
        )
    except Exception as e:
        logger.error(f"Error importing parcels: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
