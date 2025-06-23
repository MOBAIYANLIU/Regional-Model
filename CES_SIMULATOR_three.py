
import pgeocode
import os
import csv
import math
import pandas as pd
import numpy as np
from datetime import datetime
import random
import time
import sys

def simulate_heating_system(Location_Input, House_Size, TES_Max_Volume, Occupants_Num, Tstat, Dwelling_U_Value, EPC_Space_Heating, Fixed_Grid_Emissions):

    # Add path handling setup
    def get_data_path(folder_name, file_name):
        """Get the absolute path for data files relative to the script location"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, folder_name)
        
        # Create the directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        return os.path.join(data_dir, file_name)

    def create_example_weather_file(file_path, lat, lon):
        """Create an example weather file with realistic data"""
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write headers
            writer.writerow(['time', 'wind', 'temp', 'irradiance'])
            writer.writerow(['', 'm/s', 'celsius', 'W/m2'])
            writer.writerow([f'Latitude: {lat}, Longitude: {lon}'])
            writer.writerow(['datetime', 'wind', 'temp', 'irradiance'])
            
            # Generate example hourly data for a year
            for month in range(12):
                days_in_month = 31
                if month in [3, 5, 8, 10]:  # April, June, September, November
                    days_in_month = 30
                elif month == 1:  # February
                    days_in_month = 28
                    
                for day in range(days_in_month):
                    for hour in range(24):
                        # Temperature varies between 0 and 25°C seasonally
                        temp = 12.5 + 12.5 * math.cos((month - 1) * math.pi / 6)
                        # Add daily variation
                        temp += 5 * math.cos(hour * math.pi / 12)
                        # Irradiance follows a daily pattern
                        if 6 <= hour <= 18:  # Daylight hours
                            irradiance = 1000 * math.sin(math.pi * (hour - 6) / 12)
                        else:
                            irradiance = 0
                        writer.writerow([f'2020-{month+1:02d}-{day+1:02d} {hour:02d}:00', 5, f'{temp:.1f}', f'{irradiance:.1f}'])

    def create_example_agile_tariff(file_path):
        """Create an example Agile tariff file"""
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            for _ in range(8760):  # One year of hourly data
                writer.writerow(['2020', '15.0'])  # Example fixed rate of 15p/kWh

    def create_example_grid_emissions(file_path):
        """Create an example grid emissions file"""
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            for _ in range(8760):  # One year of hourly data
                writer.writerow(['2020', '0.233'])  # Example emissions factor

    # MODELS
    Heating = "y"  # "y" for heating on
    Baseload = "y"  # "y" for baseload on
    Transport = "y"  # "y" for transport on

    # CONSTANTS
    Hot_Water_Temp = 51
    # https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2021
    NPC_Years = 20
    Discount_Rate = 1.035  # 3.5% standard for UK HMRC
    # https://www.finance-ni.gov.uk/articles/step-eight-calculate-net-present-values-and-assess-uncertainties

    # Thermostat profiles
    Tstat_Boiler = [Tstat-2, Tstat-2, Tstat-2, Tstat-2, Tstat-2, Tstat-2, Tstat-2, Tstat, Tstat, Tstat, Tstat, Tstat,
                    Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat-2, Tstat-2]
    Tstat_HP = [Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat,
                Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat, Tstat]

    nomi = pgeocode.Nominatim("GB")  # GB code includes Northern Ireland
    Location = nomi.query_postal_code(Location_Input)
    Latitude = Location.latitude
    Longitude = Location.longitude

    # SPACE HEATING DWELLING CONSTANTS
    Heat_Capacity = (250 * House_Size) / 3600  # kWh/K, 250 kJ/m2K average UK dwelling specific heat capacity in SAP
    Body_Heat_Gain = (Occupants_Num * 60) / 1000  # kWh
    PF_sg = math.sin(math.pi / 180 * 90 / 2)  # Assume windows are vertical, so no in roof windows
    Asg_s = (-0.66 * PF_sg ** 3) + (-0.106 * PF_sg ** 2) + (2.93 * PF_sg)
    Bsg_s = (3.63 * PF_sg ** 3) + (-0.374 * PF_sg ** 2) + (-7.4 * PF_sg)
    Csg_s = (-2.71 * PF_sg ** 3) + (-0.991 * PF_sg ** 2) + (4.59 * PF_sg) + 1
    Asg_n = (26.3 * PF_sg ** 3) + (-38.5 * PF_sg ** 2) + (14.8 * PF_sg)
    Bsg_n = (-16.5 * PF_sg ** 3) + (27.3 * PF_sg ** 2) + (-11.9 * PF_sg)
    Csg_n = (-1.06 * PF_sg ** 3) + (-0.0872 * PF_sg ** 2) + (-0.191 * PF_sg) + 1
    Solar_Declination = [-20.7, -12.8, -1.8, 9.8, 18.8, 23.1, 21.2, 13.7, 2.9, -8.7, -18.4, -23.0]  # Monthly values
    Ratio_SG_South = []
    Ratio_SG_North = []
    for m in range(12):
        Solar_Height_Factor = math.cos(math.pi / 180 * (Latitude - Solar_Declination[m]))
        Ratio_SG_South.append(Asg_s * Solar_Height_Factor ** 2 + Bsg_s * Solar_Height_Factor + Csg_s)
        Ratio_SG_North.append(Asg_n * Solar_Height_Factor ** 2 + Bsg_n * Solar_Height_Factor + Csg_n)

    # DHW DWELLING CONSTANTS
    # Hourly ratios and temperature source "Measurement of Domestic Hot Water Consumption in Dwellings"
    DHW_Hourly_Ratios = (0.025, 0.018, 0.011, 0.010, 0.008, 0.013, 0.017, 0.044, 0.088, 0.075, 0.060, 0.056, 0.050,
                        0.043, 0.036, 0.029, 0.030, 0.036, 0.053, 0.074, 0.071, 0.059, 0.050, 0.041)
    if Latitude < 52.2:  # South of England
        Cold_Water_Temp = (12.1, 11.4, 12.3, 15.2, 16.1, 19.3, 21.2, 20.1, 19.5, 16.8, 13.7, 12.4)
    elif Latitude < 53.3:  # Middle of England and Wales
        Cold_Water_Temp = (12.9, 13.3, 14.4, 16.3, 17.7, 19.7, 21.8, 20.1, 20.3, 17.8, 15.3, 14.0)
    elif Latitude < 54.95:  # North of England and Northern Ireland
        Cold_Water_Temp = (9.6, 9.3, 10.7, 13.7, 15.3, 17.3, 19.3, 18.6, 17.9, 15.5, 12.3, 10.5)
    else:  # Scotland
        Cold_Water_Temp = (9.6, 9.2, 9.8, 13.2, 14.5, 16.8, 19.4, 18.5, 17.5, 15.1, 13.7, 12.4)
    DHW_Monthly_Factor = (1.10, 1.06, 1.02, 0.98, 0.94, 0.90, 0.90, 0.94, 0.98, 1.02, 1.06, 1.10)  # SAP plus below values
    Showers_Vol = (0.45 * Occupants_Num + 0.65) * 28.8  # Litres, 28.8 equivalent of Mixer with TES
    Bath_Vol = (0.13 * Occupants_Num + 0.19) * 50.8  # Assumes shower is present
    Other_Vol = 9.8 * Occupants_Num + 14
    DHW_Avg_Daily_Vol = Showers_Vol + Bath_Vol + Other_Vol

    Lat_Rounded = str(round(Latitude * 2) / 2)
    Lon_Rounded = str(round(Longitude * 2) / 2)
    File_Name = "ninja_weather_" + Lat_Rounded + "000_" + Lon_Rounded + "000_uncorrected.csv"
    Ambient = []
    Irradiance = []
    Coldest_Outside_Temp = 5  # Initial set point, then reduced depending on location weather

    # Update file paths to use the new path handling function
    weather_file_path = get_data_path("NinjaData", File_Name)
    if not os.path.isfile(weather_file_path):
        print(f"Weather file not found: {File_Name}")
        create_example_weather_file(weather_file_path, Latitude, Longitude)

    # print("Loading weather data...")
    with open(weather_file_path, "r") as Weather_File:
        Weather_Data = csv.reader(Weather_File)
        next(Weather_Data)  # Skip header row
        next(Weather_Data)  # Skip units row
        next(Weather_Data)  # Skip metadata row
        next(Weather_Data)  # Skip column names
        for Row in Weather_Data:
            Ambient.append(float(Row[2]))
            Irradiance.append(float(Row[3]))
            if (float(Row[2])) < Coldest_Outside_Temp:
                Coldest_Outside_Temp = (float(Row[2]))

    # Validate weather data
    if len(Ambient) != 8760:
        print(f"Error: Weather data should contain exactly 8760 hours, but found {len(Ambient)} hours")
        print("This might cause simulation errors. Please check your weather data file.")
        exit()

    Agile_Tariff = []  # Octopus Agile tariff 2020, excluding Feb29 https://www.energy-stats.uk/octopus-agile/
    agile_file_path = get_data_path("Data", "Agile Tariff.csv")
    if not os.path.isfile(agile_file_path):
        print("Agile tariff file not found")
        create_example_agile_tariff(agile_file_path)

    with open(agile_file_path) as Agile_File:
        Agile_Data = csv.reader(Agile_File)
        for Row in Agile_Data:
            Agile_Tariff.append(float(Row[1]))

    Grid_Emissions = []
    if Fixed_Grid_Emissions == 1:  # 1 for use 2020 variable emissions
        emissions_file_path = get_data_path("Data", "Grid Emissions.csv")
        if not os.path.isfile(emissions_file_path):
            print("Grid emissions file not found")
            create_example_grid_emissions(emissions_file_path)
            
        with open(emissions_file_path) as Emissions_File:
            Emissions_Data = csv.reader(Emissions_File)
            for Row in Emissions_Data:
                if (float(Row[1])-0.0) < 0:
                    Grid_Emissions.append(0)
                else:
                    Grid_Emissions.append(float(Row[1])-0.0)
    else:  # Use input fixed emissions
        for Row in range(8760):
            Grid_Emissions.append(Fixed_Grid_Emissions)

    # Typical UK household base electricity demand and cooking demands
    # Sources CREST Demand Model and Household Electricity Survey
    Baseload_Record = []
    Cooking_Record = []
    if Baseload == "y":
        Baseload_Weekday = (0.07, 1.2, 0.07, 0.07, 0.07, 0.07, 0.07, 0.29, 0.22, 0.92, 1.32, 0.07, 0.07, 0.07, 0.07, 0.07,
                            0.19, 0.406, 0.49, 0.595, 0.695, 0.595, 0.595, 0.07)
        Baseload_Weekend = (0.07, 0.07, 0.07, 0.07, 0.07, 0.07, 0.07, 0.07, 0.29, 0.32, 0.72, 0.59, 0.29, 0.19, 0.19, 0.59,
                            0.49, 0.49, 0.395, 0.695, 0.845, 0.695, 0.595, 0.07)
        Cooking_Weekday = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.24, 0, 0, 0, 0, 0, 0)
        Cooking_Weekend = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.92, 0, 0, 0, 0, 1.24, 0, 0, 0, 0, 0)
        for d in range(365):
            if ((d+1) % 7 == 0) or (d % 7 == 0):  # Saturday or Sunday, Sunday first day of the year
                for i in range(24):
                    Baseload_Record.append(Baseload_Weekend[i])
                    Cooking_Record.append(Cooking_Weekend[i])
            else:  # Weekday
                for i in range(24):
                    Baseload_Record.append(Baseload_Weekday[i])
                    Cooking_Record.append(Cooking_Weekday[i])
    else:
        for i in range(365*24):
            Baseload_Record.append(0)
            Cooking_Record.append(0)

    # TECHNOLOGY CONSTANTS
    Ground_Temp = 15 - (Latitude - 50) * (4 / 9)  # Linear regression ground temp across UK at 100m depth
    # Based on data in https://www.sciencedirect.com/science/article/pii/S0378778821004825?dgcid=rss_sd_all
    Solar_Maximum = (int((House_Size / 4) / 2)) * 2  # Quarter of the roof for solar, even number
    PF_Roof = math.sin(math.pi / 180 * 35 / 2)  # Assume roof is 35° from horizontal
    A_Roof = (-0.66 * PF_Roof ** 3) + (-0.106 * PF_Roof ** 2) + (2.93 * PF_Roof)  # Roof is south facing
    B_Roof = (3.63 * PF_Roof ** 3) + (-0.374 * PF_Roof ** 2) + (-7.4 * PF_Roof)
    C_Roof = (-2.71 * PF_Roof ** 3) + (-0.991 * PF_Roof ** 2) + (4.59 * PF_Roof) + 1
    Ratio_Roof = []
    for m in range(12):
        Solar_Height_Factor = math.cos(math.pi / 180 * (Latitude - Solar_Declination[m]))
        Ratio_Roof.append(A_Roof * Solar_Height_Factor ** 2 + B_Roof * Solar_Height_Factor + C_Roof)
    EV_Capacity = 61.2  # 61.2kWh https://ev-database.uk/cheatsheet/useable-battery-capacity-electric-car
    EV_Max_Charge = 7.0  # Typical domestic charger on single phase
    EV_Min_Charge = 1.4  # 1.4kW minimum allowable charging rate in EV standard
    EV_Efficiency = (2.75, 2.90, 3.05, 3.25, 3.45, 3.55, 3.75, 3.60, 3.45, 3.25, 3.05, 2.95)  # Monthly values
    # Average 3.25m/kWh https://ev-database.uk/cheatsheet/energy-consumption-electric-car
    EV_Charge_Efficiency = 0.968  # 96.8% charging and discharging efficiency
    # https://www.sciencedirect.com/science/article/pii/S0038092X19304281
    BES_Capacity = 8.2  # GivEnergy 8.2kWh https://nakedsolar.co.uk/storage/
    BES_Max_Charge = 3.0  # GivEnergy 8.2kWh
    Output_Record = []

    # HEATING DEMAND CALCULATIONS
    def function_demand_day_calculation():
        nonlocal Count  # Make sure Count is global
        for h in range(24):
            nonlocal Inside_Temp
            nonlocal Count
            nonlocal profile

            # DHW HOUR CALCULATIONS
            dhw_hr_demand = (DHW_Avg_Daily_Vol * 4.18 * (Hot_Water_Temp - Cold_Water_Temp[m]) / 3600) * \
                DHW_Monthly_Factor[m] * DHW_Hourly_Ratios[h]

            # SPACE HEATING HOUR CALCULATIONS
            incident_irradiance_gain = Irradiance[Count] * (Ratio_SG_South[m] + Ratio_SG_North[m])
            solar_gain = incident_irradiance_gain * (House_Size * 0.15 / 2) * 0.77 * 0.7 * 0.76 * 0.9 / 1000  # kW
            heat_loss = (House_Size * Dwelling_U_Value * (Inside_Temp - Ambient[Count])) / 1000
            # heat_loss in kWh, +ve means heat flows out of building, -ve heat flows into building
            Inside_Temp += ((- heat_loss + solar_gain + Body_Heat_Gain) / Heat_Capacity)

            if Inside_Temp > Tstat_Profile[h]:  # Warm enough already, NO heating required
                space_hr_demand = 0
            else:  # Requires heating
                space_hr_demand = (Tstat_Profile[h] - Inside_Temp) * Heat_Capacity
                Inside_Temp = Tstat_Profile[h]
            Count += 1
            Demand_Record.append(dhw_hr_demand + space_hr_demand)
            if profile == 0:
                DHW_Record.append(dhw_hr_demand)
                HP_Space_Heating_Record.append(space_hr_demand)
            else:
                Gas_Space_Heating_Record.append(space_hr_demand)

    # HEATING DEMAND LOOP
    HP_Max_Demand = Boiler_Max_Demand = HP_Demand_Total = Boiler_Demand_Total = 0
    Gas_Space_Heating_Record = []
    HP_Space_Heating_Record = []
    DHW_Record = []
    Count = 0  # Initialize Count here
    for profile in range(2):
        if profile == 0:  # HP demand
            Tstat_Profile = Tstat_HP
        else:  # Boilers / electric heating demand
            Tstat_Profile = Tstat_Boiler
        Inside_Temp = Tstat  # Initial temperature
        Count = 0  # Reset Count for each profile
        Demand_Record = []
        for m in range(12):
            if m == 3 or m == 5 or m == 8 or m == 10:  # Months with 30 days -1, as for loop starts at 0
                for d in range(30):
                    function_demand_day_calculation()
            elif m == 1:
                for d in range(28):
                    function_demand_day_calculation()
            else:
                for d in range(31):
                    function_demand_day_calculation()
        if profile == 0:  # HP & Fuel Cells
            HP_Demand_Total = sum(Demand_Record)
            HP_Max_Demand = max(Demand_Record)
        else:  # Boilers, including electrical
            Boiler_Demand_Total = sum(Demand_Record)
            Boiler_Max_Demand = max(Demand_Record)

    # HOURLY SIMULATIONS
    def function_day_calculation():
        for h in range(24):
            nonlocal Inside_Temp
            nonlocal Count
            nonlocal TES_SoC
            nonlocal OpEx_Peak
            nonlocal OpEx_Off_Peak
            nonlocal Emissions
            nonlocal EV_SoC
            nonlocal EV_SoH
            nonlocal BES_SoC
            nonlocal BES_SoH
            nonlocal Heating_OpEx
            nonlocal Baseload_OpEx
            nonlocal Cooking_OpEx
            nonlocal Transport_OpEx
            nonlocal Export_OpEx
            nonlocal Heating_Emissions
            nonlocal Baseload_Emissions
            nonlocal Cooking_Emissions
            nonlocal Transport_Emissions

            # DHW demand
            dhw_demand = (DHW_Avg_Daily_Vol * 4.18 * (Hot_Water_Temp - Cold_Water_Temp[m]) / 3600) * \
                DHW_Monthly_Factor[m] * DHW_Hourly_Ratios[h]

            # Space heating demand
            incident_irradiance_gain = Irradiance[Count] * (Ratio_SG_South[m] + Ratio_SG_North[m])
            solar_gain = incident_irradiance_gain * (House_Size * 0.15 / 2) * 0.77 * 0.7 * 0.76 * 0.9 / 1000  # kW
            heat_loss = (House_Size * Dwelling_U_Value * (Inside_Temp - Ambient[Count])) / 1000
            # heat_loss in kWh, +ve means heat flows out of building, -ve heat flows into building
            Inside_Temp += ((- heat_loss + solar_gain + Body_Heat_Gain) / Heat_Capacity)

            # TES temperature and losses
            if TES_SoC <= TES_Full_Capacity:  # Currently at nominal temperature ranges
                tes_upper_temp = 51
                tes_lower_temp = Cold_Water_Temp[m]  # Bottom of the tank would still be at CWT,
                tes_thermocline_height = TES_SoC / TES_Full_Capacity  # %, from top down, .25 is top 25%
            else:  # At max tes temperature
                tes_upper_temp = 95
                tes_lower_temp = 51
                tes_thermocline_height = (TES_SoC - TES_Full_Capacity) / (TES_Max_Capacity - TES_Full_Capacity)
            if tes_thermocline_height > 1:
                tes_thermocline_height = 1
            elif tes_thermocline_height < 0:
                tes_thermocline_height = 0
            tes_upper_losses = (tes_upper_temp - Inside_Temp) * TES_U_Value * (math.pi * TES_Radius * 2 *
                (tes_thermocline_height * TES_Radius * 2) + math.pi * TES_Radius ** 2) / 1000  # losses in kWh
            tes_lower_losses = (tes_lower_temp - Inside_Temp) * TES_U_Value * (math.pi * TES_Radius * 2 *
                ((1 - tes_thermocline_height) * TES_Radius * 2) + math.pi * TES_Radius ** 2) / 1000
            TES_SoC += - (tes_upper_losses + tes_lower_losses)
            Inside_Temp += (tes_upper_losses + tes_lower_losses) / Heat_Capacity  # TES inside house

            # Solar energy generation
            incident_irradiance_roof = Irradiance[Count] * Ratio_Roof[m] / 1000  # kW/m2
            if Solar_Option == 6:  # PVT
                pv_efficiency = (14.7 * (1 - 0.0045 * ((tes_upper_temp + tes_lower_temp) / 2 - 25))) / 100
                # https://www.sciencedirect.com/science/article/pii/S0306261919313443#b0175
            else:
                pv_efficiency = 0.1928  # Technology Library https://zenodo.org/record/4692649#.YQEbio5KjIV
                # monocrystalline used for domestic
            pv_generation = PV_Size * pv_efficiency * incident_irradiance_roof * 0.8  # 80% shading factor
            if Solar_Option >= 2 and incident_irradiance_roof > 0:
                solar_thermal_collector_temp = (tes_upper_temp + tes_lower_temp) / 2
                # Collector to heat from tes lower temperature to tes upper temperature, so use the average temperature
                if Solar_Option == 2 or Solar_Option == 4:  # Flat plate
                    # https://www.sciencedirect.com/science/article/pii/B9781782422136000023
                    solar_thermal_generation = Solar_Thermal_Size * (0.78 * incident_irradiance_roof -
                        0.0035 * (solar_thermal_collector_temp - Ambient[Count]) -
                        0.000038 * (solar_thermal_collector_temp - Ambient[Count]) ** 2) * 0.8
                elif Solar_Option == 6:  # PVT https://www.sciencedirect.com/science/article/pii/S0306261919313443#b0175
                    solar_thermal_generation = PV_Size * (0.726 * incident_irradiance_roof -
                        0.003325 * (solar_thermal_collector_temp - Ambient[Count]) -
                        0.0000176 * (solar_thermal_collector_temp - Ambient[Count]) ** 2) * 0.8
                else:  # Evacuated tube https://www.sciencedirect.com/science/article/pii/B9781782422136000023
                    solar_thermal_generation = Solar_Thermal_Size * (0.625 * incident_irradiance_roof -
                        0.0009 * (solar_thermal_collector_temp - Ambient[Count]) -
                        0.00002 * (solar_thermal_collector_temp - Ambient[Count]) ** 2) * 0.8
                if solar_thermal_generation < 0:
                    solar_thermal_generation = 0
                TES_SoC += solar_thermal_generation
                if TES_SoC > TES_Max_Capacity:  # Excess solar generated heat is lost to prevent boiling TES
                    TES_SoC = TES_Max_Capacity

            # Heater efficiencies
            if Heater_Option == 0 or 3 < Heater_Option < 8:
                cop = 0.85  # 90% efficient combustion boilers
            elif Heater_Option == 1:  # DEH
                cop = 1
            elif Heater_Option == 2:  # ASHP, source A review of domestic heat pumps
                cop = 6.81 - 0.121 * (Hot_Water_Temp - Ambient[Count]) + 0.00063 * (Hot_Water_Temp - Ambient[Count]) ** 2
            elif Heater_Option == 3:  # GSHP, source A review of domestic heat pumps
                cop = 8.77 - 0.150 * (Hot_Water_Temp - Ground_Temp) + 0.000734 * (Hot_Water_Temp - Ground_Temp) ** 2
            else:  # Fuel cell
                cop = 0.55  # 55% thermal efficiency
                # https://www.sciencedirect.com/science/article/pii/S0360319914031383#bib14

            # Sets achievable space heating demand and inside temperature
            if Inside_Temp > Tstat_Profile[h]:
                space_demand = 0
            else:  # Requires space heating
                space_demand = (Tstat_Profile[h] - Inside_Temp) * Heat_Capacity
                if (space_demand + dhw_demand) < (TES_SoC + Heater_Power * cop):
                    Inside_Temp = Tstat_Profile[h]
                else:  # Not capable of meeting hourly demand, priority dhw over space heating
                    if TES_SoC > 0:  # Can reach slight negative values at odd occasion
                        space_demand = (TES_SoC + Heater_Power * cop) - dhw_demand
                    else:  # Priority to space demand over TES charging
                        space_demand = (Heater_Power * cop) - dhw_demand
                    Inside_Temp += space_demand / Heat_Capacity

            # Determines heater demand for space and dhw demands
            if (space_demand + dhw_demand) < TES_SoC:  # TES can provide all demand
                # Default option as all heat goes through TES
                TES_SoC -= (space_demand + dhw_demand)
                heater_demand = 0
            elif (space_demand + dhw_demand) < (TES_SoC + Heater_Power * cop):
                if TES_SoC > 0:
                    heater_demand = (space_demand + dhw_demand - TES_SoC) / cop
                    TES_SoC = 0  # TES needs support so taken to empty if it had any charge
                else:
                    heater_demand = (space_demand + dhw_demand) / cop
            else:  # TES and HP can't meet hour demand
                heater_demand = Heater_Power
                if TES_SoC > 0:
                    TES_SoC = 0

            # Determine if off-peak time
            if ((Tariff == 1 and (h == 23 or h < 6)) or (Tariff == 2 and 0 < h < 5)
                    or (Tariff == 3 and Agile_Tariff[Count] < 9.0)):  # Agile < 9.0 OR 31.0 for high tariff
                # Flat rate is always peak cost, agile is off-peak if less than the average of 9p/kWh
                off_peak = "y"
            else:
                off_peak = "n"

            # Charge TES
            if 0 < Heater_Option < 4:  # Only for electrified heating (and cooking) with variable costs
                pv_surplus = pv_generation - Baseload_Record[Count] - Cooking_Record[Count] - heater_demand
                if off_peak == "y" and TES_SoC < TES_Full_Capacity:  # Maximum charge at off-peak times
                    if (TES_Full_Capacity - TES_SoC) < ((Heater_Power - heater_demand) * cop):  # Small top up
                        heater_demand += (TES_Full_Capacity - TES_SoC) / cop
                        TES_SoC = TES_Full_Capacity
                    else:  # HP can not fully top up in one hour
                        TES_SoC += (Heater_Power - heater_demand) * cop
                        heater_demand = Heater_Power
                elif pv_surplus > 0 and TES_SoC < TES_Full_Capacity:  # Use surplus pv energy for charging TES
                    if ((TES_Full_Capacity - TES_SoC) < (pv_surplus * cop)) and \
                            ((TES_Full_Capacity - TES_SoC) < ((Heater_Power - heater_demand) * cop)):
                        heater_demand += (TES_Full_Capacity - TES_SoC) / cop
                        TES_SoC = TES_Full_Capacity
                    else:  # Can not fully top up in one hour
                        if pv_surplus < (Heater_Power - heater_demand):
                            TES_SoC += pv_surplus * cop
                            heater_demand += pv_surplus
                        else:
                            TES_SoC += (Heater_Power - heater_demand) * cop
                            heater_demand = Heater_Power
            if TES_SoC < TES_Min_Capacity:  # Take back up to 10L capacity if possible no matter what time, all tech
                if (TES_Min_Capacity - TES_SoC) < (Heater_Power - heater_demand) * cop:
                    heater_demand += (TES_Min_Capacity - TES_SoC) / cop
                    TES_SoC = TES_Min_Capacity
                elif heater_demand < Heater_Power:  # Can't take all the way back up to 10L charge, but still got capacity
                    TES_SoC += (Heater_Power - heater_demand) * cop

            if Heater_Option > 7:  # Fuel cell
                pv_generation += heater_demand * 0.39  # 39% electrical efficiency
                # https://www.sciencedirect.com/science/article/pii/S0360319914031383#bib14

            if Heating != "y":
                heater_demand = 0

            # Transport demand and EV charging
            ev_demand = mileage = 0
            ev_home = "y"  # default option
            if Transport == "y":
                if (int(Count / 24) + 1) % 7 == 0:  # Saturday
                    if h > 12:
                        ev_home = "n"
                    if h == 13:  # Weekend outbound trip
                        mileage = 16
                elif int(Count / 24) % 7 == 0:  # Sunday, first day of year
                    if h <= 12:
                        ev_home = "n"
                    if h == 12:  # Weekend return trip
                        mileage = 16
                else:  # Weekday
                    if 8 < h <= 18:  # At work / commuting
                        ev_home = "n"
                    if h == 9:  # Outbound commute
                        mileage = 11
                    if h == 17:  # Return commute
                        mileage = 11

                if (Heating != "y" and Car_Option == 1) or (Heating == "y" and Heater_Option < 5 and Car_Option > 0):  # EV
                    EV_SoC -= (mileage / EV_Efficiency[m])
                    if ev_home == "y" and EV_SoC < EV_Capacity:  # charge EV

                        if 0 < Heater_Option < 4:  # Electrified heating and cooking
                            pv_surplus = pv_generation - Baseload_Record[Count] - Cooking_Record[Count] - heater_demand
                        elif Heater_Option == 4:  # Biomass, electrified cooking
                            pv_surplus = pv_generation - Baseload_Record[Count] - Cooking_Record[Count]
                        else:  # Not electric fuel for heating and cooking
                            pv_surplus = pv_generation - Baseload_Record[Count]

                        if off_peak == "y":
                            if (EV_Capacity - EV_SoC) < EV_Max_Charge:  # can fill up
                                ev_demand = (EV_Capacity - EV_SoC) / EV_Charge_Efficiency
                                EV_SoC = EV_Capacity
                            else:  # Can not reach full charge
                                EV_SoC += EV_Max_Charge
                                ev_demand = EV_Max_Charge / EV_Charge_Efficiency
                        elif EV_SoC < (EV_Capacity * 0.25):  # Max charge for an hour if low SoC, even at peak times
                            EV_SoC += EV_Max_Charge
                            ev_demand = EV_Max_Charge / EV_Charge_Efficiency
                        elif pv_surplus > EV_Min_Charge:
                            if ((EV_Capacity - EV_SoC) < pv_surplus * EV_Charge_Efficiency) and \
                                    ((EV_Capacity - EV_SoC) < EV_Max_Charge):  # can fill
                                ev_demand = (EV_Capacity - EV_SoC) / EV_Charge_Efficiency
                                EV_SoC = EV_Capacity
                            else:  # Can not reach full charge
                                if pv_surplus * EV_Charge_Efficiency < EV_Max_Charge:
                                    ev_demand = pv_surplus * EV_Charge_Efficiency
                                    EV_SoC += pv_surplus * EV_Charge_Efficiency
                                else:
                                    ev_demand = EV_Max_Charge / EV_Charge_Efficiency
                                    EV_SoC += EV_Max_Charge

            # Wall BES charging
            bes_demand = 0
            if BES == "y":  # Charge Wall BES
                if 0 < Heater_Option < 4:  # Electrified heating and cooking
                    pv_surplus = pv_generation - Baseload_Record[Count] - Cooking_Record[Count] - heater_demand - ev_demand
                elif Heater_Option == 4:  # Biomass, electrified cooking
                    pv_surplus = pv_generation - Baseload_Record[Count] - Cooking_Record[Count] - ev_demand
                else:  # Not electric fuel for heating and cooking
                    pv_surplus = pv_generation - Baseload_Record[Count] - ev_demand

                if off_peak == "y":  # Charge as much as possible at off-peak
                    if (BES_Capacity - BES_SoC) < BES_Max_Charge:
                        bes_demand = (BES_Capacity - BES_SoC) / EV_Charge_Efficiency
                        BES_SoC = BES_Capacity
                    else:  # can not reach full charge
                        BES_SoC += BES_Max_Charge
                        bes_demand = BES_Max_Charge / EV_Charge_Efficiency
                elif pv_surplus > 0:
                    if ((BES_Capacity - BES_SoC) < pv_surplus * EV_Charge_Efficiency) and \
                            ((BES_Capacity - BES_SoC) < BES_Max_Charge):  # can fill
                        bes_demand = (BES_Capacity - BES_SoC) / EV_Charge_Efficiency
                        BES_SoC = BES_Capacity
                    else:  # Can not reach full charge
                        if pv_surplus * EV_Charge_Efficiency < BES_Max_Charge:
                            bes_demand = pv_surplus * EV_Charge_Efficiency
                            BES_SoC += pv_surplus * EV_Charge_Efficiency
                        else:
                            bes_demand = BES_Max_Charge / EV_Charge_Efficiency
                            BES_SoC += BES_Max_Charge

            if 0 < Heater_Option < 4:  # Electrified heating and cooking
                elec_import = Baseload_Record[Count] + Cooking_Record[Count] + heater_demand + ev_demand + bes_demand \
                            - pv_generation
            elif Heater_Option == 4:  # Biomass with electrified cooking
                elec_import = Baseload_Record[Count] + Cooking_Record[Count] + ev_demand + bes_demand - pv_generation
            else:
                elec_import = Baseload_Record[Count] + ev_demand + bes_demand - pv_generation
            if elec_import < 0:  # Exporting
                pv_surplus = - elec_import
                elec_import = 0
            else:
                pv_surplus = 0

                # BES or EV2H discharging calculations
                if BES == "y" and BES_SoC > 0 and off_peak != "y":
                    if elec_import < BES_SoC * EV_Charge_Efficiency and elec_import < BES_Max_Charge:  # BES provides all
                        BES_SoC -= elec_import / EV_Charge_Efficiency
                        bes_demand -= elec_import
                        elec_import = 0
                    else:  # BES can NOT provide all energy for household demands
                        if BES_SoC < BES_Max_Charge:  # Stored energy is limiting factor
                            elec_import -= BES_SoC * EV_Charge_Efficiency
                            bes_demand -= BES_SoC * EV_Charge_Efficiency
                            BES_SoC = 0
                        else:  # BES power is limiting factor
                            elec_import -= BES_Max_Charge * EV_Charge_Efficiency
                            bes_demand -= BES_Max_Charge * EV_Charge_Efficiency
                            BES_SoC -= BES_Max_Charge
                    # BES State of Health degradation, source Yunfei paper
                    bes_c_rate = abs(bes_demand) / BES_Capacity  # C-rate, charges per full hour
                    bes_correction_factor = 0.0023 * (bes_c_rate ** 2) - 0.1014 * bes_c_rate + 1.1146
                    bes_degradation_factor = (-bes_demand / bes_correction_factor) / (5000 * BES_Capacity)
                    BES_SoH -= bes_degradation_factor * 100
                elif EV2H == "y" and ev_home == "y" and (EV_SoC > EV_Capacity * 0.25) and off_peak != "y":
                    # EV charge greater than 25%, at home and peak times
                    if elec_import < (EV_SoC - EV_Capacity * 0.25) * EV_Charge_Efficiency:  # EV can provide all demand
                        ev2home_demand = elec_import / EV_Charge_Efficiency
                        EV_SoC -= elec_import / EV_Charge_Efficiency
                        ev_demand -= elec_import
                        elec_import = 0
                    else:  # EV can NOT provide all energy for household demands
                        ev2home_demand = (EV_SoC - EV_Capacity * 0.25)
                        elec_import -= (EV_SoC - EV_Capacity * 0.25) * EV_Charge_Efficiency
                        ev_demand -= (EV_SoC - EV_Capacity * 0.25) * EV_Charge_Efficiency
                        EV_SoC = EV_Capacity * 0.25
                    # EV State of Health degradation from EV2Home, source Yunfei paper
                    ev_c_rate = abs(ev2home_demand) / EV_Capacity  # C-rate, charges per full hour
                    ev_correction_factor = 0.0023 * (ev_c_rate ** 2) - 0.1014 * ev_c_rate + 1.1146
                    ev_degradation_factor = (ev2home_demand / ev_correction_factor) / (5000 * EV_Capacity)
                    EV_SoH -= ev_degradation_factor * 100

            # Electrical OpEx and emissions
            export_tariff = 0.055  # 0.055 0.075
            # https://octopus.energy/tariffs/ Low tariffs 2020, high tariffs 2022
            # https://octopus.energy/outgoing/
            if Tariff == 0:  # Flat rate tariff
                import_tariff = 0.1335  # 0.1335 0.3242
            elif Tariff == 1:  # Economy 7 tariff
                if off_peak == "y":
                    import_tariff = 0.0891  # 0.0891 0.2163
                else:  # Peak
                    import_tariff = 0.1533  # 0.1533 0.3593
            else:  # Octopus Agile file 2020, without Feb29 or average from 2022 so far
                import_tariff = (Agile_Tariff[Count] / 100)
            if Baseload == "y":  # No additional self consumption assumptions
                if off_peak == "y":
                    OpEx_Off_Peak += elec_import * import_tariff
                    OpEx_Off_Peak -= pv_surplus * export_tariff  # No additional self consumption assumptions
                else:
                    OpEx_Peak += elec_import * import_tariff
                    OpEx_Peak -= pv_surplus * export_tariff  # No additional self consumption assumptions
                Emissions += elec_import * Grid_Emissions[Count]  # kgCO2e
            else:  # Baseload off, assume 50% of surplus used
                if off_peak == "y":
                    OpEx_Off_Peak += elec_import * import_tariff - (pv_surplus / 2) * import_tariff
                    OpEx_Off_Peak -= (pv_surplus / 2) * export_tariff
                else:
                    OpEx_Peak += elec_import * import_tariff - (pv_surplus / 2) * import_tariff
                    OpEx_Peak -= (pv_surplus / 2) * export_tariff
                Emissions += elec_import * Grid_Emissions[Count] - (pv_surplus / 2) * Grid_Emissions[Count]  # kgCO2e

            # Other tech OpEx and emissions
            if Heater_Option == 0:  # Gas for heating and cooking
                OpEx_Peak += (heater_demand + Cooking_Record[Count]) * 0.021
                # https://octopus.energy/tariffs/ Lowest in the year 2020
                Emissions += (heater_demand + Cooking_Record[Count]) * 0.183  # 0.183 kgCO2e/kWh
                # https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2021
                Cooking_OpEx += Cooking_Record[Count] * 0.021
                Cooking_Emissions += Cooking_Record[Count] * 0.183
                Heating_OpEx += heater_demand * 0.021
                Heating_Emissions += heater_demand * 0.183

            # Demand distribution of OpEx and Emissions, surplus not correct if no Baseload, not an issue
            if 0 < Heater_Option < 4:  # Electrified heating and cooking
                # PV priority to baseload, then cooking, then heating, then ev
                if pv_generation <= Baseload_Record[Count]:
                    Baseload_OpEx += (Baseload_Record[Count] - pv_generation) * import_tariff
                    Baseload_Emissions += (Baseload_Record[Count] - pv_generation) * Grid_Emissions[Count]  # kgCO2e
                    Cooking_OpEx += Cooking_Record[Count] * import_tariff
                    Cooking_Emissions += Cooking_Record[Count] * Grid_Emissions[Count]
                    Heating_OpEx += heater_demand * import_tariff
                    Heating_Emissions += heater_demand * Grid_Emissions[Count]
                    Transport_OpEx += ev_demand * import_tariff
                    Transport_Emissions += ev_demand * Grid_Emissions[Count]
                elif pv_generation <= Baseload_Record[Count] + Cooking_Record[Count]:
                    # No baseload OpEx or emissions
                    Cooking_OpEx += (Cooking_Record[Count] + Baseload_Record[Count] - pv_generation) * import_tariff
                    Cooking_Emissions += (Cooking_Record[Count] + Baseload_Record[Count] - pv_generation) * \
                                        Grid_Emissions[Count]
                    Heating_OpEx += heater_demand * import_tariff
                    Heating_Emissions += heater_demand * Grid_Emissions[Count]
                    Transport_OpEx += ev_demand * import_tariff
                    Transport_Emissions += ev_demand * Grid_Emissions[Count]
                elif pv_generation <= Baseload_Record[Count] + Cooking_Record[Count] + heater_demand:
                    # No baseload or cooking OpEx or emissions
                    Heating_OpEx += (heater_demand + Cooking_Record[Count] + Baseload_Record[Count] - pv_generation) \
                        * import_tariff
                    Heating_Emissions += (heater_demand + Cooking_Record[Count] + Baseload_Record[Count] - pv_generation) \
                        * Grid_Emissions[Count]
                    Transport_OpEx += ev_demand * import_tariff
                    Transport_Emissions += ev_demand * Grid_Emissions[Count]
                elif pv_generation <= Baseload_Record[Count] + Cooking_Record[Count] + heater_demand + \
                            ev_demand:  # Only transport demands
                    Transport_OpEx += (ev_demand + heater_demand + Cooking_Record[Count] + Baseload_Record[Count]
                        - pv_generation) * import_tariff
                    Transport_Emissions += (ev_demand + heater_demand + Cooking_Record[Count] + Baseload_Record[Count]
                        - pv_generation) * Grid_Emissions[Count]

            if pv_surplus > 0:
                Export_OpEx -= pv_surplus * export_tariff

            Inside_Temp_Record.append(Inside_Temp)
            Heater_Record.append(heater_demand)
            TES_Record.append(TES_SoC)
            PV_Record.append(pv_generation)
            EV_Record.append(ev_demand)
            EV_SoC_Record.append(EV_SoC)
            BES_SoC_Record.append(BES_SoC)
            Count += 1


    # TECHNOLOGY LOOPS
    if Heating == "y":
        Heater_Range = 3 #11
    else:
        Heater_Range = 1
    for Heater_Option in range(Heater_Range):
        # Heater_Range 0=Gas 1=DEH 2=ASHP 3=GSHP 4=Biomass 5=GreyB 6=BlueB 7=ElectrolysedB 8=GreyFC 9=BlueFC 10=ElecFC
        # Heater_Option = 1
        if Transport != "y":  # Transport off
            Car_Range = 1
        else:  # Transport on
            if 0 < Heater_Option < 4:  # Elec
                Car_Range = 4
            else:
                Car_Range = 2  # Only Petrol or EV(Biomass)/H2
        for Car_Option in range(Car_Range):  # Car_Range + BES, Transport off, 0=None
            # Transport on, gas or elec, 0=Petrol, 1=EV, 2=EV+BES, 3=EV2H
            # Transport on, H2 or biomass, 0=Petrol, 1=H2/EV
            Technology_NPC = 1000000  # Keep same level as Specification Record
            if (0 < Heater_Option < 4) and (Transport != "y" or Car_Option == 1):
                # Electrified heating only, when transport off or EV
                Solar_Range = 7  # 7
            elif 0 < Heater_Option < 4:
                Solar_Range = 2  # Elec with or without PV for petrol car
            else:
                Solar_Range = 1  # No solar option
            for Solar_Option in range(Solar_Range):  # Solar_Range, 0=None, 1=PV, 2=FP, 3=ET, 4=FP+PV, 5=ET+PV, 6=PVT
                Heater_NPC = 1000000
                if Solar_Option == 0:
                    Solar_Size_Range = 1
                elif Solar_Option == 4 or Solar_Option == 5:  # One less option when combined
                    Solar_Size_Range = Solar_Maximum / 2 - 1
                else:
                    Solar_Size_Range = Solar_Maximum / 2  # 2m2 increments
                for Solar_Size in range(int(Solar_Size_Range)):  # Solar_Size_Range, 2m2 min up to max
                    # Solar_Size = 0
                    if (0 < Heater_Option < 4) or (Solar_Option > 2):  # TES for Elec or ST
                        TES_Range = TES_Max_Volume / 0.1
                    else:
                        TES_Range = 1
                    for TES_Size in range(int(TES_Range)):  # TES_Range
                        for Tariff in range(4):  # 4, 0=Flat rate, 1=Economy7, 2=EV, 3=Time of Use
                            # Tariff = 3
                            Inside_Temp_Record = []
                            Heater_Record = []
                            TES_Record = []
                            PV_Record = []
                            EV_Record = []
                            EV_SoC_Record = []
                            BES_SoC_Record = []
                            Count = OpEx_Peak = OpEx_Off_Peak = Emissions = 0
                            Heating_OpEx = Baseload_OpEx = Cooking_OpEx = Transport_OpEx = Export_OpEx = 0
                            Heating_Emissions = Baseload_Emissions = Cooking_Emissions = Transport_Emissions = 0
                            Inside_Temp = Tstat  # Initial temp

                            TES_Volume = 0.1 + TES_Size * 0.1  # m3

                            TES_Radius = (TES_Volume / (2 * math.pi)) ** (1 / 3)  # For cylinder with height = 2x radius
                            TES_Full_Capacity = TES_Volume * 1000 * 4.18 * (Hot_Water_Temp - 40) / 3600  # 40 min temp
                            TES_Max_Capacity = TES_Volume * 1000 * 4.18 * (95 - 40) / 3600  # kWh, 95C and solar
                            TES_Min_Capacity = 10 * 4.18 * (Hot_Water_Temp - 10) / 3600  # 10litres hot min amount
                            # CWT coming in from DHW re-fill, accounted for by DHW out, DHW min useful temp 40°C
                            # Space heating return temperature would also be ~40°C with flow at 51°C
                            TES_SoC = TES_Full_Capacity  # kWh, for H2O, starts full to prevent initial demand spike
                            TES_U_Value = 1.30  # 1.30 W/m2K linearised from
                            # https://zenodo.org/record/4692649#.YQEbio5KjIV &
                            # https://www.sciencedirect.com/science/article/pii/S0306261916302045

                            if 2 <= Solar_Option < 6:  # Solar thermal, not PVT
                                Solar_Thermal_Size = 2 + Solar_Size * 2
                            else:
                                Solar_Thermal_Size = 0
                            if Solar_Option == 1 or Solar_Option == 6:
                                PV_Size = Solar_Maximum - Solar_Size * 2
                            elif Solar_Option == 4 or Solar_Option == 5:
                                PV_Size = Solar_Maximum - Solar_Thermal_Size
                            else:
                                PV_Size = 0

                            if Heater_Option == 1:  # DEH
                                cop_ref = 1.0 # yunfei set
                                Heater_Power = Boiler_Max_Demand / cop_ref
                                Tstat_Profile = Tstat_Boiler
                                # if Heater_Power > 7.0:  # Typical maximum domestic electrical power
                                #     Heater_Power = 7.0
                            elif Heater_Option == 2 or Heater_Option == 3:  # ASHP or GSHP
                                if Heater_Option == 2:  # ASHP, source A review of domestic heat pumps
                                    cop_worst = 6.81 - 0.121 * (Hot_Water_Temp - Coldest_Outside_Temp) + \
                                        0.000630 * (Hot_Water_Temp - Coldest_Outside_Temp) ** 2  # ASHP at coldest temp
                                    cop_ref = 6.81 - 0.121 * (35 - 7) + 0.000630 * (35 - 7) ** 2
                                    # ASHP heating capacity at reference conditions A7/W35
                                    Heater_Power = HP_Max_Demand / cop_worst
                                    if Heater_Power * cop_ref < 4.0:  # Mitsubishi have 4kWth ASHP
                                        Heater_Power = 4.0 / cop_ref
                                else:  # GSHP, source A review of domestic heat pumps
                                    cop_worst = 8.77 - 0.150 * (Hot_Water_Temp - Ground_Temp) + \
                                        0.000734 * (Hot_Water_Temp - Ground_Temp) ** 2  # GSHP ~constant temp at 100m
                                    cop_ref = 8.77 - 0.150 * (35 - 0) + 0.000734 * (35 - 0) ** 2
                                    # GSHP heating capacity at reference conditions B0/W35
                                    Heater_Power = HP_Max_Demand / cop_worst
                                    if Heater_Power * cop_ref < 6.0:  # Kensa 6kWth GSHP
                                        Heater_Power = 6.0 / cop_ref
                                Tstat_Profile = Tstat_HP
                            else:  # Combustion boiler
                                cop_ref = 0.85
                                Heater_Power = Boiler_Max_Demand / cop_ref  # Power = energy in
                                Tstat_Profile = Tstat_Boiler

                            if Transport == "y" and Car_Option == 2:
                                BES = "y"
                            else:
                                BES = "n"
                            if Transport == "y" and Car_Option == 3:
                                EV2H = "y"
                            else:
                                EV2H = "n"
                            EV_SoC = EV_Capacity
                            BES_SoC = BES_Capacity
                            EV_SoH = BES_SoH = 100  # State of Health, starts at 100%

                            for m in range(12):
                                if m == 3 or m == 5 or m == 8 or m == 10:
                                    for d in range(30):
                                        function_day_calculation()
                                elif m == 1:
                                    for d in range(28):
                                        function_day_calculation()
                                else:
                                    for d in range(31):
                                        function_day_calculation()

                            if (0 < Heater_Option < 4) or Baseload == "y":  # Low tariffs 2020, high tariffs 2022
                                if Tariff < 2:  # Flat or Eco7
                                    Standing_Charge = 0.2006 * 365  # 0.2006 0.2376
                            else:
                                Standing_Charge = 0

                            if Heater_Option == 0:  # Gas Boiler
                                Standing_Charge += (0.1785 * 365)
                                CapEx = 1500 + EPC_Space_Heating / 25  # £500 less than H2 boilers
                                Heating_NPC = CapEx
                                if CapEx > 2500:
                                    CapEx = 2500
                                Emissions += 192 / NPC_Years  # 192kgCO2e typical gas boiler
                                # https://iopscience.iop.org/article/10.1088/1757-899X/161/1/012094
                                Current_Options = "Gas " + "%.1f" % (Heater_Power) + "kW, " # Heater_Power * cop_ref
                                Heating_Emissions += 192 / NPC_Years
                            elif Heater_Option == 1:  # DEH              
                                CapEx = 100 + 1000  # Negligible emissions over TES, £1000 installation cost
                                # Small additional cost to a TES, https://zenodo.org/record/4692649#.YQEbio5KjIV
                                Heating_NPC = CapEx
                                Current_Options = "DEH " + "%.1f" % (Heater_Power) + "kW, "
                            elif Heater_Option == 2:  # ASHP
                                CapEx = ((200 + 4750 / ((Heater_Power * cop_ref) ** 1.25)) *
                                        (Heater_Power * cop_ref) + 1500)  # £s
                                # https://pubs.rsc.org/en/content/articlepdf/2012/ee/c2ee22653g
                                Heating_NPC = CapEx
                                Emissions += 280 / NPC_Years  # 280kgCO2e for 10kW ASHP
                                # https://www.sciencedirect.com/science/article/pii/S0378778817323101
                                Current_Options = "ASHP " + "%.1f" % (Heater_Power) + "kW, "
                                Heating_Emissions += 280 / NPC_Years

                            if (0 < Heater_Option < 4) or (Solar_Option > 2):  # TES for Elec or ST
                                CapEx += 2068.3 * TES_Volume ** 0.553  # TES cost
                                Emissions += 60 / NPC_Years  # 1/3 of boiler emissions scaled down from weight
                                Heating_Emissions += 60 / NPC_Years
                            # Formula based on this data https://assets.publishing.service.gov.uk/government/uploads/
                            # [rest of address] system/uploads/attachment_data/file/545249/DELTA_EE_DECC_TES_Final__1_.pdf
                            if Heating != "y":  # No cost for a heater or TES, can still have solar tech cost
                                CapEx = 0
                                Current_Options = ""

                            if Heating == "y":
                                Current_Options += "TES " + ("%.1f" % TES_Volume) + "m3, "
                            if Tariff == 0:
                                Current_Options += "flat OpEx total £" + ("%.2f" % (OpEx_Peak + Standing_Charge))
                            elif Tariff == 1:
                                Current_Options += "Eco7"

                            for Year in range(NPC_Years):  # 20 years cost
                                Heating_NPC += (OpEx_Peak + OpEx_Off_Peak + Standing_Charge) / \
                                    (Discount_Rate ** Year)
                            Current_Options += ", NPC £" + ("%.0f" % Heating_NPC)
                            Current_Options += ", Emissions Heating " + ("%.0f" % Heating_Emissions) + "kgCO2e"

                            Output_Record.append(Current_Options)

        Output_Record.append("")
        
    return Output_Record