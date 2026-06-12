import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import os

# ============================
# Daten laden
# ============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "steam_trends.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# ============================
# Review-Prozent Trend
# ============================
years = np.array(sorted(map(int, data["review_percent_by_year"].keys())))
values = np.array([data["review_percent_by_year"][str(y)] for y in years])

X = years.reshape(-1, 1)
y = values

# ============================
# Train/Test Split
# ============================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

# ============================
# Lineare Regression
# ============================
lin_model = LinearRegression()
lin_model.fit(X_train, y_train)

y_pred_lin = lin_model.predict(X_test)

mse_lin = mean_squared_error(y_test, y_pred_lin)
r2_lin = r2_score(y_test, y_pred_lin)

# ============================
# Polynomiale Regression (Grad 2–5)
# ============================
best_degree = None
best_mse = float("inf")
best_model = None
best_poly = None

for degree in range(2, 6):
    poly = PolynomialFeatures(degree=degree)
    X_poly_train = poly.fit_transform(X_train)
    X_poly_test = poly.transform(X_test)

    model = LinearRegression()
    model.fit(X_poly_train, y_train)

    y_pred = model.predict(X_poly_test)

    mse = mean_squared_error(y_test, y_pred)

    if mse < best_mse:
        best_mse = mse
        best_degree = degree
        best_model = model
        best_poly = poly

# ============================
# Zukunft vorhersagen (2027–2030)
# ============================
future_years = np.array([2027, 2028, 2029, 2030]).reshape(-1, 1)

future_lin = lin_model.predict(future_years)
future_poly = best_model.predict(best_poly.transform(future_years))

# ============================
# GENRE-TRENDS
# ============================
genre_by_year = data["genre_by_year"]

all_genres = set()
for year in genre_by_year:
    all_genres.update(genre_by_year[year].keys())

genre_forecasts = {}

for genre in all_genres:
    # historische Daten extrahieren
    g_years = []
    g_values = []

    for year in sorted(genre_by_year.keys()):
        year_int = int(year)
        g_years.append(year_int)
        g_values.append(genre_by_year[year].get(genre, 0))

    g_years = np.array(g_years)
    g_values = np.array(g_values)

    Xg = g_years.reshape(-1, 1)
    yg = g_values

    # lineares Modell
    lin_g = LinearRegression()
    lin_g.fit(Xg, yg)
    future_lin_g = lin_g.predict(future_years)

    # polynomial (Grad 2)
    poly_g = PolynomialFeatures(degree=2)
    Xg_poly = poly_g.fit_transform(Xg)
    model_g = LinearRegression()
    model_g.fit(Xg_poly, yg)
    future_poly_g = model_g.predict(poly_g.transform(future_years))

    genre_forecasts[genre] = {
        "years": g_years.tolist(),
        "values": g_values.tolist(),
        "future_linear": future_lin_g.tolist(),
        "future_poly": future_poly_g.tolist()
    }

# ============================
# JSON speichern
# ============================
output = {
    "review_trend": {
        "years": years.tolist(),
        "values": y.tolist(),
        "linear": future_lin.tolist(),
        "polynomial": future_poly.tolist(),
        "best_poly_degree": best_degree
    },
    "genre_trends": genre_forecasts
}

save_path = os.path.join(BASE_DIR, "prediction_output.json")

with open(save_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4, ensure_ascii=False)

print(f"\nPrediction gespeichert unter: {save_path}")
