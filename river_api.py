from flask import Flask, jsonify, request
import pandas as pd

app = Flask(__name__)

# CSV লোড করো
df = pd.read_csv("data/bwdb_rivers.csv")

@app.route("/rivers", methods=["GET"])
def get_rivers():
    zone = request.args.get("zone")
    if zone:
        filtered = df[df["Zone"].str.upper() == zone.upper()]
        return jsonify(filtered.to_dict(orient="records"))
    return jsonify(df.to_dict(orient="records"))

@app.route("/rivers/<int:serial>", methods=["GET"])
def get_river_by_serial(serial):
    row = df[df["Serial No"] == serial]
    if row.empty:
        return jsonify({"error": "River not found"}), 404
    return jsonify(row.to_dict(orient="records")[0])

if __name__ == "__main__":
    app.run(debug=True)
  
