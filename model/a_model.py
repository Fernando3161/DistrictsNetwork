"""
This is the main model schema that serves as template for the districts.

This model has a structure and parameters that vary according to the 
technologies present in the district. Each district has a configuration 
file that activates the components and the respective exchanges.

"""

import pandas as pd
from oemof.solph import (EnergySystem, Bus, Sink, Source, Flow,
                         Transformer, GenericStorage)
from oemof.solph import views, processing
import matplotlib.pyplot as plt
import logging
from enum import Enum
import os
from os.path import join
import json
import warnings
from electricity_markets.market_price_generator import create_markets_info

warnings.simplefilter(action='ignore', category=FutureWarning)
logging.basicConfig(level=logging.INFO)

#first: get district structure
# use the set_config function. 


#second: geet external market info
def get_market_dataframe(days=7, year=2017):
    """
    :param days: Days of the year, beginning on 01/01/YYYY.
    :param year: Year

    """

    # Get market data as per the price generator
    market_data = create_markets_info(
        year=year, save_csv=False,).head(
        days * 24 * 4)
    # Definition of scenarios.
    # Inflation of market prices for functionality evaluation

    return market_data

market_data = get_market_dataframe(year=2019)
print(market_data)

#third: build model structure
