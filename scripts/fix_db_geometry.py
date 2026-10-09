import sqlite3
import json

db_path = r"d:\VIT\data\database\timeseries.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

p102_geom = {
    "type": "Polygon",
    "coordinates": [[[77.4483839, 8.7146695], [77.4496483, 8.7143928], [77.4497387, 8.7156796], [77.4484981, 8.7157868], [77.4483839, 8.7146695]]]
}

cur.execute('UPDATE parcel_observations SET geom_json = ? WHERE parcel_id = "PARCEL_0102" OR geom_json = "{}" OR geom_json = "" OR geom_json IS NULL', (json.dumps(p102_geom),))
conn.commit()
print("Updated rows in timeseries.db:", cur.rowcount)

cur.execute('SELECT parcel_id, geom_json FROM parcel_observations WHERE geom_json = "{}" OR geom_json = "" OR geom_json IS NULL')
remaining = cur.fetchall()
print("Remaining bad geometries:", len(remaining))

conn.close()
