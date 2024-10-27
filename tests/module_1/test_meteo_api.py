import json
import pandas as pd
import requests
from unittest.mock import MagicMock, Mock
import pytest

from src.module_1.module_1_meteo_api import (
    calculo_de_media_mensual,
    VARIABLES,
    _request_to_api,
    request_to_api,
)


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"Error: {self.status_code}")


def test_calculo_de_media_mensual():
    test_variable = "test_variable"

    # Crear el DataFrame de datos de entrada
    data = pd.DataFrame(
        {
            "city": ["Madrid"] * 3,
            "time": pd.date_range(start="2020-01-01", periods=3),
            f"{test_variable}": [10, 12, 8],
        }
    )

    # Crear el DataFrame esperado (resultado esperado)
    expected = pd.DataFrame(
        {
            "city": ["Madrid"],
            "month": pd.to_datetime(["2020-01-01"]),
            f"{test_variable}_max": [12],
            f"{test_variable}_mean": [10.0],
            f"{test_variable}_min": [8.0],
            f"{test_variable}_std": [2.0],
        }
    )

    # Ejecutar la función a probar
    actual = calculo_de_media_mensual(data, [test_variable])

    # Verificar que el DataFrame generado es igual al esperado
    pd.testing.assert_frame_equal(
        actual, expected, check_dtype=False, check_index_type=False
    )


def test_request_to_api_success(monkeypatch):
    # Simulamos una respuesta exitosa
    headers = {}
    mock_response = Mock(return_value=MockResponse("json_dummy", 200))
    monkeypatch.setattr(requests, "get", mock_response)
    response = _request_to_api("url", headers, 5)
    assert response.status_code == 200
    assert response.json() == "json_dummy"


def test_request_to_api_error_404(monkeypatch):
    # Simulamos una respuesta exitosa
    with pytest.raises(requests.exceptions.HTTPError):
        headers = {}
        mock_response = Mock(return_value=MockResponse("json_dummy", 404))
        monkeypatch.setattr(requests, "get", mock_response)
        _ = _request_to_api("url", headers, 5)
