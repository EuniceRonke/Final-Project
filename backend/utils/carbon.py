import random
def estimate_carbon_emission(soil_moisture: float, vegetation_index: float):
    """
    Estimate carbon emission or environmental status based on soil and vegetation data.
    """

    # Simple rule-based logic
    if soil_moisture < 20:
        status = "Degraded"
        suggestion = "Reforestation or irrigation needed."
    elif soil_moisture < 35:
        status = "At Risk"
        suggestion = "Mulching, cover crops, or moderate irrigation."
    else:
        status = "Healthy"
        suggestion = "Land is healthy. Maintain current practices."

    # Optional: simulate carbon emission score (lower vegetation → higher emission)
    estimated_emission = round((1 - vegetation_index) * 10, 2)

    return {
        "status": status,
        "suggestion": suggestion,
        "estimated_emission": estimated_emission
    }
