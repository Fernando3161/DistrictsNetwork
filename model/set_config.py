# %%
from common import DATA_DIR, Districts
from os.path import join
import pandas as pd


def set_configuration(district=Districts.ENAQ, excel_filename="DistrictData_20.07.21.xlsx"):

    EXCEL_DATA = join(DATA_DIR, "Quartiere", excel_filename)
    # All units in kW
    # All costs in EUR
    # All emissions in kgCO2 per kWh

    # %%
    year = 2019
    start = f"{year}-01-01"
    days = 365  # Full year

    # Correct for leap year
    if year % 4 == 0:
        days += 1

    # Set first the datetime objects with the appropriate dates
    dates = pd.date_range(start, periods=days * 24*4+1, freq="15T")
    district = district.value["name"]

    # Electricity Demand
    d_el = pd.read_excel(EXCEL_DATA,
                         "2.power demand series",
                         engine='openpyxl')  # ["DE01"][2:].tolist()

    d_el = d_el.drop([0, 1])  # first two rows are empyt
    d_el = d_el.rename(columns={d_el.columns[0]: "Step"})
    d_el["Step"] = [int(x) for x in d_el["Step"]]
    d_el.set_index("Step", inplace=True)
    d_el = d_el[[district]]
    d_el = d_el.dropna(axis=0)
    d_el = d_el[district]*4  # this is power demand so I want this in kW

    # %%
    # thermal demand
    d_th = pd.read_excel(EXCEL_DATA,
                         "1.heat demand series",
                         engine='openpyxl')
    d_th = d_th.drop([0, 1])  # first two rows are empyt
    d_th = d_th.rename(columns={d_th.columns[0]: "Step"})
    d_th["Step"] = [int(x) for x in d_th["Step"]]
    d_th.set_index("Step", inplace=True)
    d_th = d_th[[district]]
    d_th = d_th.dropna(axis=0)
    d_th = d_th[district]*4
    d_th

    # %%
    # PV Production  and Wind Production per kW installed (as data source, no direct Modeling)
    vol_prof = pd.read_excel(EXCEL_DATA,
                             "2.volatile series",
                             engine='openpyxl')
    vol_prof = vol_prof.drop([0, 1])  # first two rows are empyt

    vol_prof = vol_prof.rename(columns={vol_prof.columns[0]: "Step"})
    vol_prof["Step"] = [int(x) for x in vol_prof["Step"]]
    vol_prof.set_index("Step", inplace=True)

    col_names = list(vol_prof.columns)
    for i in range(len(col_names)):
        if i % 2 == 0:
            try:
                vol_prof = vol_prof.rename(
                    columns={col_names[i+1]: f"{col_names[i]}-Wind"})
            except:
                pass

    # This does need correction since are production profiles per kW installed
    solar_prof = vol_prof[district]
    # This does need correction since are production profiles per kW installed
    wind_prof = vol_prof[f"{district}-Wind"]

    # %%
    hp_cop = pd.read_excel(EXCEL_DATA,
                           "1.heat pump efficiency series",
                           engine='openpyxl')
    hp_cop = hp_cop.drop([0, 1])  # first two rows are empyt
    hp_cop = hp_cop.rename(columns={hp_cop.columns[0]: "Step"})
    hp_cop["Step"] = [int(x) for x in hp_cop["Step"]]
    hp_cop.set_index("Step", inplace=True)
    hp_cop = hp_cop[[district]]
    hp_cop = hp_cop.dropna(axis=0)
    hp_cop = hp_cop[district]

    # %%
    # All list need to have the same lenght
    min_len = min(len(dates),
                  len(d_el),
                  len(d_th),
                  len(wind_prof),
                  len(solar_prof),
                  len(hp_cop))

    dates = dates[0:min_len]
    d_el = d_el[0:min_len]
    d_th = d_th[0:min_len]
    wind_prof = wind_prof[0:min_len]
    solar_prof = solar_prof[0:min_len]
    hp_cop = hp_cop[0:min_len]

    # %%
    # get configuration parameters:
    # this fetches the data from the worksheets and builds a configuration dictionary to be passed to the oemof model

    configuration = {}

    # fetch the emission factor as well
    configuration["name"] = district
    configuration["datetime"] = dates
    heat_sources = pd.read_excel(EXCEL_DATA,
                                 "0.commodity sources",
                                 engine='openpyxl')

    # %%
    gas_grid = heat_sources[heat_sources["fuel"] == "natural gas"]
    gas_grid.set_index("District", inplace=True)

    configuration["gas"] = {}
    configuration["gas"]["fuel"] = gas_grid.at[district, "fuel"]
    configuration["gas"]["emission"] = gas_grid.at[district, "emission"]

    ext_heat = heat_sources[heat_sources["fuel"] == "heat grid"]
    if district in ext_heat.index:
        configuration["ext_grid"] = {}
        configuration["ext_grid"]["type"] = gas_grid.at[district, "fuel"]
        configuration["ext_grid"]["emission"] = gas_grid.at[district, "emission"]

    # %%
    heat_plants = pd.read_excel(EXCEL_DATA,
                                "1.heat plants",
                                engine='openpyxl')

    heat_plants = heat_plants[heat_plants["District"].notna()]

    boilers = heat_plants[heat_plants["Technology"] == "boiler"]
    hps = heat_plants[heat_plants["Technology"] == "heat pump"]

    boilers.set_index("District", inplace=True)
    hps.set_index("District", inplace=True)

    if boilers.at[district, "capacity"] > 0:
        configuration["boiler"] = {}
        configuration["boiler"]["p_kw"] = boilers.at[district, "capacity"]*1000
        configuration["boiler"]["eff"] = boilers.at[district, "efficiency"]

    if hps.at[district, "capacity"] > 0:
        configuration["heat_pump"] = {}
        configuration["heat_pump"]["p_kw_th"] = hps.at[district, "capacity"]*1000
        configuration["heat_pump"]["cop"] = hp_cop

    # %%
    heat_demand = pd.read_excel(EXCEL_DATA,
                                "1.heat demand total",
                                engine='openpyxl')

    heat_demand = heat_demand[heat_demand["District"].notna()]
    heat_demand.set_index("District", inplace=True)
    configuration["heat_demand"] = {}
    configuration["heat_demand"]["total_kWh"] = heat_demand.at[district, "Total"]

    # d_th is in kW and to sum that it needs to be in quarter hours
    configuration["heat_demand"]["profile"] = d_th / \
        (d_th.sum()/4) * configuration["heat_demand"]["total_kWh"]

    # %%
    # pass the reneewables  configurations with factors
    renewables = pd.read_excel(EXCEL_DATA,
                               "2.volatile power plants",
                               engine='openpyxl')
    renewables = renewables[renewables["District"].notna()]
    renewables.set_index("District", inplace=True)

    if renewables.at[district, "PV"] > 0:
        configuration["PV"] = {}
        configuration["PV"]["p_kw"] = renewables.at[district, "PV"]
        configuration["PV"]["profile"] = solar_prof * \
            renewables.at[district, "PV"]

    if renewables.at[district, "Solar Thermal"] > 0:
        configuration["ST"] = {}  # solar thermal
        configuration["ST"]["a_m2"] = renewables.at[district, "Solar Thermal"]
        # Solar thermal has an average anuual yield of 150 kWh thermal per m2
        # This needs to be normalized
        total_production = configuration["ST"]["a_m2"]*150  # kwH
        configuration["ST"]["total"] = total_production
        configuration["ST"]["profile"] = solar_prof / \
            (solar_prof.sum()/4)*total_production

    if renewables.at[district, "Wind"] > 0:
        configuration["Wind"] = {}
        configuration["Wind"]["p_kw"] = renewables.at[district, "Wind"]
        configuration["Wind"]["profile"] = wind_prof * \
            renewables.at[district, "Wind"]

    # %%
    el_demand = pd.read_excel(EXCEL_DATA,
                              "2. Total Electricity Demand",
                              engine='openpyxl')

    el_demand = el_demand[el_demand["District"].notna()]
    el_demand.set_index("District", inplace=True)
    configuration["el_demand"] = {}
    configuration["el_demand"]["total_kWh"] = el_demand.at[district,
                                                           "Total Electricity"]

    # d_th is in kW and to sum that it needs to be in quarter hours
    configuration["el_demand"]["profile"] = d_el / \
        (d_el.sum()/4) * configuration["el_demand"]["total_kWh"]

    # %%
    # chp
    chps = pd.read_excel(EXCEL_DATA,
                         "3.heat-chp plants",
                         engine='openpyxl')
    chps = chps[chps["District"].notna()]
    chps.set_index("District", inplace=True)

    if chps.at[district, "capacity"] > 0:
        configuration["chp"] = {}
        configuration["chp"]["p_kw"] = chps.at[district, "capacity"]*1000
        configuration["chp"]["p_kw_th"] = chps.at[district, "capacity"]*chps.at[district, "efficiency_heat"]*1000
        configuration["chp"]["p_kw_el"] = chps.at[district, "capacity"]*chps.at[district, "efficiency_el"]*1000
        configuration["chp"]["eff_th"] = chps.at[district, "efficiency_heat"]
        configuration["chp"]["eff_el"] = chps.at[district, "efficiency_el"]

    # %%
    # electrolyser
    electrolyzers = pd.read_excel(EXCEL_DATA,
                                  "4.H2 plant",
                                  engine='openpyxl')
    electrolyzers = electrolyzers[electrolyzers["District"].notna()]
    electrolyzers.set_index("District", inplace=True)

    if electrolyzers.at[district, "capacity"] > 0:
        configuration["electrolizer"] = {}
        configuration["electrolizer"]["p_kw"] = chps.at[district,
                                                        "capacity"]*1000
        configuration["electrolizer"]["eff_th"] = chps.at[district,
                                                          "efficiency_heat"]
        configuration["electrolizer"]["eff_h2"] = chps.at[district,
                                                          "efficiency_el"]

    # %%

    # %%
    heat_sto = pd.read_excel(EXCEL_DATA,
                             "1.heat storage",
                             engine='openpyxl')
    heat_sto = heat_sto[heat_sto["District"].notna()]
    heat_sto.set_index("District", inplace=True)

    if heat_sto.at[district, "capacity"] > 0:

        configuration["heat_sto"] = {}
        configuration["heat_sto"]["capacity"] = heat_sto.at[district,
                                                            "capacity"]*1000
        configuration["heat_sto"]["charge_cap"] = heat_sto.at[district,
                                                              "charge capacity"]*1000
        configuration["heat_sto"]["discharge_cap"] = heat_sto.at[district,
                                                                 "discharge capacity"]*1000
        configuration["heat_sto"]["charge_eff"] = heat_sto.at[district,
                                                              "charge efficiency"]
        configuration["heat_sto"]["disch_eff"] = heat_sto.at[district,
                                                             "discharge efficiency"]
        configuration["heat_sto"]["loss_rate"] = heat_sto.at[district, "loss rate"]
        configuration["heat_sto"]["volume"] = heat_sto.at[district, "volume"]
        configuration["heat_sto"]["delta_temp"] = heat_sto.at[district, "delta temp"]

    # %%
    batt_sto = pd.read_excel(EXCEL_DATA,
                             "2.power storages",
                             engine='openpyxl')
    batt_sto = batt_sto[batt_sto["District"].notna()]
    batt_sto.set_index("District", inplace=True)

    if batt_sto.at[district, "capacity"] > 0:

        configuration["batt_sto"] = {}
        configuration["batt_sto"]["capacity"] = batt_sto.at[district,
                                                            "capacity"]*1000
        configuration["batt_sto"]["charge_cap"] = batt_sto.at[district,
                                                              "charge capacity"]*1000
        configuration["batt_sto"]["discharge_cap"] = batt_sto.at[district,
                                                                 "discharge capacity"]*1000
        configuration["batt_sto"]["charge_eff"] = batt_sto.at[district,
                                                              "charge efficiency"]
        configuration["batt_sto"]["disch_eff"] = batt_sto.at[district,
                                                             "discharge efficiency"]
        configuration["batt_sto"]["loss_rate"] = batt_sto.at[district, "loss rate"]

    # %%
    return configuration


if __name__=="__main__":
    for distr in Districts:
        config = set_configuration(district=distr)
        
        print(config)
        # # name = distr.value["name"]
        # # config["datetime"] = [str(x) for x in config["datetime"]]
        # # import json
        # # with open(f"{name}.json", 'w') as f:
        # #     json.dump(config, f)




