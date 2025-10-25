import random
import datetime

def get_river_data(location="Bangladesh"):
    """
    Simulated River Level API for major rivers of Bangladesh.
    In future, can be connected to BWDB (Bangladesh Water Development Board) live data.
    """

    # Bangladesh main rivers and their danger levels (in meters)
    rivers = {
        "Padma": 7.5,
        "Meghna": 6.8,
        "Jamuna": 8.0,
        "Teesta": 5.2,
        "Surma": 4.8
    }

    try:
        river_list = []

        for river_name, danger_level in rivers.items():
            current_level = round(random.uniform(danger_level - 1.0, danger_level + 1.5), 2)

            # Determine status
            if current_level > danger_level:
                status = "⚠️ Above Danger Level"
            elif current_level > danger_level - 0.5:
                status = "🟡 Near Danger Level"
            else:
                status = "🟢 Normal"

            river_info = {
                "river_name": river_name,
                "location": location,
                "current_level_m": current_level,
                "danger_level_m": danger_level,
                "status": status,
                "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            river_list.append(river_info)

        return {
            "country": "Bangladesh",
            "total_rivers": len(river_list),
            "data": river_list
        }

    except Exception as e:
        return {"error": str(e)}
