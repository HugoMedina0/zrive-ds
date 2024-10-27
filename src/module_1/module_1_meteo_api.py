import json
import time
from typing import Dict, List
from urllib.parse import urlencode
import requests
import pandas as pd
import matplotlib.pyplot as plt

API_URL = "https://archive-api.open-meteo.com/v1/archive?"

COORDINATES = {
    "Madrid": {"latitude": 40.416775, "longitude": -3.703790},
    "London": {"latitude": 51.507351, "longitude": -0.127758},
    "Rio": {"latitude": -22.906847, "longitude": -43.172896},
}

VARIABLES = [
    "temperature_2m_mean",
    "precipitation_sum",
    "wind_speed_10m_max",
]


def get_data_meteo_api(latitude: float, longitude: float):
    """
    Esta función construye la solicitud para obtener datos meteorológicos de la API
    según la latitud y longitud dadas. Devuelve un diccionario con los datos climáticos diarios.
    """
    headers = {}

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2010-01-01",
        "end_date": "2020-12-31",
        "daily": ",".join(VARIABLES),
    }

    return request_to_api(API_URL + urlencode(params, safe=","), headers)


def _request_to_api(
    url: str, headers: Dict[str, any], num_attemps: int
) -> requests.Response:
    """
    Realiza una solicitud GET a la API con un sistema de reintentos en caso de error.
    """
    cooloff = 1
    for call_count in range(num_attemps):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response

        except requests.exceptions.ConnectionError as e:
            if call_count != (num_attemps - 1):
                time.sleep(cooloff)
                cooloff *= 2
                continue
            else:
                raise

        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise

            if call_count != (num_attemps - 1):
                time.sleep(cooloff)
                cooloff *= 2
                continue
            else:
                raise

    return response


def request_to_api(
    url: str, headers: Dict[str, any], num_attemps: int = 5
) -> Dict[any, any]:
    """
    Hace la solicitud a la API y devuelve el contenido en formato JSON.
    """
    return json.loads(
        _request_to_api(url, headers, num_attemps).content.decode("utf-8")
    )


def calculo_de_media_mensual(data: pd.DataFrame, variables: List[str]):
    """
    Calcula las estadísticas mensuales (máximo, media, mínimo, desviación estándar)
    para cada variable climática de cada ciudad.
    """
    data["time"] = pd.to_datetime(data["time"])

    group_by = data.groupby([data["city"], data["time"].dt.to_period("M")])

    resultados = []

    for (city, month), group in group_by:
        estadisticas_mensuales = {"city": city, "month": month.to_timestamp()}

        for variable in variables:
            estadisticas_mensuales[f"{variable}_max"] = group[variable].max()
            estadisticas_mensuales[f"{variable}_mean"] = group[variable].mean()
            estadisticas_mensuales[f"{variable}_min"] = group[variable].min()
            estadisticas_mensuales[f"{variable}_std"] = group[variable].std()

        resultados.append(estadisticas_mensuales)

    return pd.DataFrame(resultados)


import matplotlib.dates as mdates


def plot_mensual_stats(data: pd.DataFrame):
    """
    Genera gráficos de estadísticas mensuales para cada variable climática y ciudad.
    """
    rows = len(VARIABLES)
    cols = len(data["city"].unique())

    fig, axs = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows), sharex=True)
    fig.suptitle("Monthly Statistics by City and Variable", fontsize=16)

    for i, variable in enumerate(VARIABLES):
        for k, city in enumerate(data["city"].unique()):
            city_data = data[data["city"] == city]

            ax = axs[i, k] if rows > 1 else axs[k]

            ax.plot(
                city_data["month"],
                city_data[f"{variable}_mean"],
                label=f"{city} - Mean",
            )

            ax.fill_between(
                city_data["month"],
                city_data[f"{variable}_min"],
                city_data[f"{variable}_max"],
                alpha=0.2,
                label=f"{city} - Range",
            )

            ax.set_title(f"{city} - {variable.replace('_', ' ').title()}")
            ax.set_ylabel(f"{variable.replace('_', ' ').title()}")

            ax.set_xlabel("Month")
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            ax.xaxis.set_minor_locator(mdates.MonthLocator())

            ax.legend()
            ax.grid(True)

    fig.autofmt_xdate(rotation=45)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


def main():
    """
    Función principal que obtiene los datos de la API, calcula las estadísticas
    mensuales para las ciudades y genera los gráficos correspondientes.
    """
    data_list = []
    for ciudad, coordenadas in COORDINATES.items():
        latitude = coordenadas["latitude"]
        longitude = coordenadas["longitude"]
        data = pd.DataFrame(get_data_meteo_api(latitude, longitude)["daily"]).assign(
            city=ciudad
        )
        data_list.append(data)

    data = pd.concat(data_list)

    media_mensual = calculo_de_media_mensual(data, VARIABLES)

    print(media_mensual)

    plot_mensual_stats(media_mensual)


if __name__ == "__main__":
    main()
