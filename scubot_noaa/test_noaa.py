# pylint: disable C0103
import datetime

import pytest
from noaa import tides

from . import noaa


class TestNoaa:
    def test_split_data(self):
        today = datetime.datetime.now()
        tomorrow = today + datetime.timedelta(days=1)
        after = tomorrow + datetime.timedelta(days=1)
        tide_1 = tides.PredictionsRow(today, 0.0, 'L')
        tide_2_1 = tides.PredictionsRow(tomorrow, 0.0, 'L')
        tide_2_2 = tides.PredictionsRow(tomorrow, 0.0, 'H')
        tide_3 = tides.PredictionsRow(after, 0.0, 'L')
        data = [tide_1, tide_2_1, tide_2_2, tide_3]
        output = noaa.split_data(data)
        assert output == [[tide_1], [tide_2_1, tide_2_2], [tide_3]]
