
import math
import pgeocode

def UVC(House_Size,Location_Input,Occupants_Num,EPC_Space_Heating):
    # EPC iterative calculations for Thermal Transmittance
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
    
    EPC_Occupants_Num = 1 + 1.76 * (1 - math.exp(-0.000349 * (House_Size - 13.9) ** 2)) + 0.0013 * (House_Size - 13.9)
    EPC_Body_Gain = (EPC_Occupants_Num * 60) / 1000  # kWh

    if Location_Input[0:2] == "AL" or Location_Input[0:4] == "CM21" or Location_Input[0:4] == "CM22" or \
            Location_Input[0:4] == "CM23" or Location_Input[0:2] == "CR" or Location_Input[0:2] == "EC" or \
            Location_Input[0:2] == "HA" or Location_Input[0:2] == "HP" or Location_Input[0:2] == "KT" or \
            Location_Input[0:2] == "LU" or Location_Input[0:2] == "MK" or Location_Input[0:2] == "NW" or \
            Location_Input[0:2] == "OX" or Location_Input[0:2] == "SE" or Location_Input[0:2] == "SG" or \
            Location_Input[0:2] == "SL" or Location_Input[0:2] == "SM" or Location_Input[0:3] == "SN7" or \
            Location_Input[0:2] == "SW" or Location_Input[0:2] == "TW" or Location_Input[0:2] == "UB" or \
            Location_Input[0:2] == "WC" or Location_Input[0:2] == "WD":
        EPC_Ambient = [5.1, 5.6, 7.4, 9.9, 13.0, 16.0, 17.9, 17.8, 15.2, 11.6, 8.0, 5.1]  # Region 1
        EPC_Irradiance = [30, 56, 98, 157, 195, 217, 203, 173, 127, 73, 39, 24]  # Thames
    elif Location_Input[0:2] == "BN" or Location_Input[0:2] == "BR" or Location_Input[0:2] == "CT" or \
            Location_Input[0:2] == "DA" or Location_Input[0:4] == "GU28" or Location_Input[0:4] == "GU29" or \
            Location_Input[0:2] == "ME" or Location_Input[0:4] == "PO18" or Location_Input[0:4] == "PO19" or \
            Location_Input[0:4] == "PO20" or Location_Input[0:4] == "PO21" or Location_Input[0:4] == "PO22" or \
            Location_Input[0:4] == "RH10" or Location_Input[0:4] == "RH11" or Location_Input[0:4] == "RH12" or \
            Location_Input[0:4] == "RH13" or Location_Input[0:4] == "RH14" or Location_Input[0:4] == "RH15" or \
            Location_Input[0:4] == "RH16" or Location_Input[0:4] == "RH17" or Location_Input[0:4] == "RH18" or \
            Location_Input[0:4] == "RH19" or Location_Input[0:4] == "RH20" or Location_Input[0:2] == "TN":
        EPC_Ambient = [5.0, 5.4, 7.1, 9.5, 12.6, 15.4, 17.4, 17.5, 15.0, 11.7, 8.1, 5.2]  # Region 2
        EPC_Irradiance = [32, 59, 104, 170, 208, 231, 216, 182, 133, 77, 41, 25]  # South East England
    elif Location_Input[0:2] == "BH" or Location_Input[0:2] == "DT" or Location_Input[0:4] == "GU11" or \
            Location_Input[0:4] == "GU12" or Location_Input[0:4] == "GU14" or Location_Input[0:4] == "GU30" or \
            Location_Input[0:4] == "GU31" or Location_Input[0:4] == "GU32" or Location_Input[0:4] == "GU33" or \
            Location_Input[0:4] == "GU34" or Location_Input[0:4] == "GU35" or Location_Input[0:4] == "GU46" or \
            Location_Input[0:4] == "GU51" or Location_Input[0:4] == "GU52" or Location_Input[0:2] == "PO" or \
            Location_Input[0:4] == "RG21" or Location_Input[0:4] == "RG22" or Location_Input[0:4] == "RG23" or \
            Location_Input[0:4] == "RG24" or Location_Input[0:4] == "RG25" or Location_Input[0:4] == "RG26" or \
            Location_Input[0:4] == "RG27" or Location_Input[0:4] == "RG28" or Location_Input[0:4] == "RG29" or \
            Location_Input[0:2] == "SO" or Location_Input[0:3] == "SP6" or Location_Input[0:3] == "SP7" or \
            Location_Input[0:3] == "SP8" or Location_Input[0:3] == "SP9" or Location_Input[0:4] == "SP10" or \
            Location_Input[0:4] == "SP11":
        EPC_Ambient = [5.4, 5.7, 7.3, 9.6, 12.6, 15.4, 17.3, 17.3, 15.0, 11.8, 8.4, 5.5]  # Region 3
        EPC_Irradiance = [35, 62, 109, 172, 209, 235, 217, 185, 138, 80, 44, 27]  # Southern England
    elif Location_Input[0:2] == "EX" or Location_Input[0:2] == "PL" or Location_Input[0:2] == "TQ" or \
            Location_Input[0:2] == "TR":
        EPC_Ambient = [6.1, 6.4, 7.5, 9.3, 11.9, 14.5, 16.2, 16.3, 14.6, 11.8, 9.0, 6.4]  # Region 4
        EPC_Irradiance = [36, 63, 111, 174, 210, 233, 204, 182, 136, 78, 44, 28]  # South West England
    elif Location_Input[0:2] == "BA" or Location_Input[0:2] == "BS" or Location_Input[0:2] == "CF" or \
            Location_Input[0:2] == "GL" or Location_Input[0:2] == "TA":
        EPC_Ambient = [4.9, 5.3, 7.0, 9.3, 12.2, 15.0, 16.7, 16.7, 14.4, 11.1, 7.8, 4.9]  # Region 5
        EPC_Irradiance = [32, 59, 105, 167, 201, 226, 206, 175, 130, 74, 40, 25]  # Severn England and Wales
    elif Location_Input[0:2] == "CV" or Location_Input[0:2] == "DE" or Location_Input[0:2] == "DY" or \
            Location_Input[0:2] == "HR" or Location_Input[0:2] == "LE" or Location_Input[0:2] == "NN" or \
            Location_Input[0:3] == "S18" or Location_Input[0:3] == "S32" or Location_Input[0:3] == "S33" or \
            Location_Input[0:3] == "S40" or Location_Input[0:3] == "S41" or Location_Input[0:3] == "S42" or \
            Location_Input[0:3] == "S43" or Location_Input[0:3] == "S44" or Location_Input[0:3] == "S45" or \
            Location_Input[0:4] == "SK13" or Location_Input[0:4] == "SK17" or Location_Input[0:4] == "SK22" or \
            Location_Input[0:4] == "SK23" or Location_Input[0:2] == "ST" or Location_Input[0:2] == "TF" or \
            Location_Input[0:2] == "WR" or Location_Input[0:2] == "WS" or Location_Input[0:2] == "WV":
        EPC_Ambient = [4.3, 4.8, 6.6, 9.0, 11.8, 14.8, 16.6, 16.5, 14.0, 10.5, 7.1, 4.2]  # Region 6
        EPC_Irradiance = [28, 55, 97, 153, 191, 208, 194, 163, 121, 69, 35, 23]  # Midlands
    elif Location_Input[0:2] == "BB" or Location_Input[0:2] == "BL" or Location_Input[0:2] == "CH" or \
            Location_Input[0:2] == "CW" or Location_Input[0:2] == "FY" or Location_Input[0:2] == "OL" or \
            Location_Input[0:2] == "PR" or Location_Input[0:4] == "SY14" or Location_Input[0:2] == "WA" or \
            Location_Input[0:2] == "WN":
        EPC_Ambient = [4.7, 5.2, 6.7, 9.1, 12.0, 14.7, 16.4, 16.3, 14.1, 10.7, 7.5, 4.6]  # Region 7
        EPC_Irradiance = [24, 51, 95, 152, 191, 203, 186, 152, 115, 65, 31, 20]  # West Pennines England and Wales
    elif Location_Input[0:2] == "CA" or Location_Input[0:2] == "DG" or Location_Input[0:3] == "LA7" or \
            Location_Input[0:3] == "LA8" or Location_Input[0:3] == "LA9" or Location_Input[0:4] == "LA10" or \
            Location_Input[0:4] == "LA11" or Location_Input[0:4] == "LA12" or Location_Input[0:4] == "LA13" or \
            Location_Input[0:4] == "LA14" or Location_Input[0:4] == "LA15" or Location_Input[0:4] == "LA16" or \
            Location_Input[0:4] == "LA17" or Location_Input[0:4] == "LA18" or Location_Input[0:4] == "LA19" or \
            Location_Input[0:4] == "LA20" or Location_Input[0:4] == "LA21" or Location_Input[0:4] == "LA22" or \
            Location_Input[0:4] == "LA23":
        EPC_Ambient = [3.9, 4.3, 5.6, 7.9, 10.7, 13.2, 14.9, 14.8, 12.8, 9.7, 6.6, 3.7]  # Region 8
        EPC_Irradiance = [23, 51, 95, 157, 200, 203, 194, 156, 113, 62, 30, 19]  # NW England and SW Scotland
    elif Location_Input[0:3] == "DH4" or Location_Input[0:3] == "DH5" or Location_Input[0:4] == "EH43" or \
            Location_Input[0:4] == "EH44" or Location_Input[0:4] == "EH45" or Location_Input[0:4] == "EH46" or \
            Location_Input[0:2] == "NE" or Location_Input[0:2] == "TD":
        EPC_Ambient = [4.0, 4.5, 5.8, 7.9, 10.4, 13.3, 15.2, 15.1, 13.1, 9.7, 6.6, 3.7]  # Region 9
        EPC_Irradiance = [23, 50, 92, 151, 200, 196, 187, 153, 11, 61, 30, 18]  # Boarders
    elif Location_Input[0:4] == "BD23" or Location_Input[0:4] == "BD24" or Location_Input[0:2] == "DH" or \
            Location_Input[0:2] == "DL" or Location_Input[0:2] == "HG" or Location_Input[0:4] == "LS24" or \
            Location_Input[0:3] == "SR7" or Location_Input[0:3] == "SR8" or Location_Input[0:2] == "TS":
        EPC_Ambient = [4.0, 4.6, 6.1, 8.3, 10.9, 13.8, 15.8, 15.6, 13.5, 10.1, 6.7, 3.8]  # Region 10
        EPC_Irradiance = [25, 51, 95, 152, 196, 198, 190, 156, 115, 64, 32, 20]  # North East England
    elif Location_Input[0:2] == "BD" or Location_Input[0:2] == "DN" or Location_Input[0:2] == "HD" or \
            Location_Input[0:2] == "HU" or Location_Input[0:2] == "HX" or Location_Input[0:2] == "LN" or \
            Location_Input[0:2] == "LS" or Location_Input[0:2] == "NG" or Location_Input[0:3] == "PE9" or \
            Location_Input[0:4] == "PE10" or Location_Input[0:4] == "PE11" or Location_Input[0:4] == "PE12" or \
            Location_Input[0:4] == "PE20" or Location_Input[0:4] == "PE21" or Location_Input[0:4] == "PE22" or \
            Location_Input[0:4] == "PE23" or Location_Input[0:4] == "PE24" or Location_Input[0:4] == "PE25" or \
            Location_Input[0:2] == "WF" or Location_Input[0:4] == "YO15" or Location_Input[0:4] == "YO16" or \
            Location_Input[0:4] == "YO25":
        EPC_Ambient = [4.3, 4.9, 6.5, 8.9, 11.7, 14.6, 16.6, 16.4, 14.1, 10.6, 7.1, 4.2]  # Region 11
        EPC_Irradiance = [26, 54, 96, 150, 192, 200, 189, 157, 115, 66, 33, 21]  # East Pennines
    elif Location_Input[0:2] == "CB" or Location_Input[0:2] == "CM" or Location_Input[0:2] == "CO" or \
            Location_Input[0:3] == "EN9" or Location_Input[0:2] == "IG" or Location_Input[0:2] == "IP" or \
            Location_Input[0:2] == "NR" or Location_Input[0:2] == "PE" or Location_Input[0:2] == "RM" or \
            Location_Input[0:2] == "SS":
        EPC_Ambient = [4.7, 5.2, 7.0, 9.5, 12.5, 15.4, 17.6, 17.6, 15.0, 11.4, 7.7, 4.7]  # Region 12
        EPC_Irradiance = [30, 58, 101, 165, 203, 220, 206, 173, 128, 74, 39, 24]  # East Anglia
    elif Location_Input[0:2] == "LD" or Location_Input[0:4] == "LL23" or Location_Input[0:4] == "LL24" or \
            Location_Input[0:4] == "LL25" or Location_Input[0:4] == "LL26" or Location_Input[0:4] == "LL27" or \
            Location_Input[0:4] == "LL30" or Location_Input[0:4] == "LL31" or Location_Input[0:4] == "LL32" or \
            Location_Input[0:4] == "LL33" or Location_Input[0:4] == "LL34" or Location_Input[0:4] == "LL35" or \
            Location_Input[0:4] == "LL36" or Location_Input[0:4] == "LL37" or Location_Input[0:4] == "LL38" or \
            Location_Input[0:4] == "LL39" or Location_Input[0:4] == "LL40" or Location_Input[0:4] == "LL41" or \
            Location_Input[0:4] == "LL42" or Location_Input[0:4] == "LL43" or Location_Input[0:4] == "LL44" or \
            Location_Input[0:4] == "LL45" or Location_Input[0:4] == "LL46" or Location_Input[0:4] == "LL47" or \
            Location_Input[0:4] == "LL48" or Location_Input[0:4] == "LL49" or Location_Input[0:4] == "LL50" or \
            Location_Input[0:4] == "LL51" or Location_Input[0:4] == "LL52" or Location_Input[0:4] == "LL53" or \
            Location_Input[0:4] == "LL54" or Location_Input[0:4] == "LL55" or Location_Input[0:4] == "LL56" or \
            Location_Input[0:4] == "LL57" or Location_Input[0:4] == "LL58" or Location_Input[0:4] == "LL59" or \
            Location_Input[0:4] == "LL60" or Location_Input[0:4] == "LL61" or Location_Input[0:4] == "LL62" or \
            Location_Input[0:4] == "LL63" or Location_Input[0:4] == "LL64" or Location_Input[0:4] == "LL65" or \
            Location_Input[0:4] == "LL66" or Location_Input[0:4] == "LL67" or Location_Input[0:4] == "LL68" or \
            Location_Input[0:4] == "LL69" or Location_Input[0:4] == "LL70" or Location_Input[0:4] == "LL71" or \
            Location_Input[0:4] == "LL72" or Location_Input[0:4] == "LL73" or Location_Input[0:4] == "LL74" or \
            Location_Input[0:4] == "LL75" or Location_Input[0:4] == "LL76" or Location_Input[0:4] == "LL77" or \
            Location_Input[0:4] == "LL78" or Location_Input[0:3] == "NP8" or Location_Input[0:4] == "SA14" or \
            Location_Input[0:4] == "SA15" or Location_Input[0:4] == "SA16" or Location_Input[0:4] == "SA17" or \
            Location_Input[0:4] == "SA18" or Location_Input[0:4] == "SA19" or Location_Input[0:4] == "SA20" or \
            Location_Input[0:4] == "SA31" or Location_Input[0:4] == "SA32" or Location_Input[0:4] == "SA33" or \
            Location_Input[0:4] == "SA34" or Location_Input[0:4] == "SA35" or Location_Input[0:4] == "SA36" or \
            Location_Input[0:4] == "SA37" or Location_Input[0:4] == "SA38" or Location_Input[0:4] == "SA39" or \
            Location_Input[0:4] == "SA40" or Location_Input[0:4] == "SA41" or Location_Input[0:4] == "SA42" or \
            Location_Input[0:4] == "SA43" or Location_Input[0:4] == "SA44" or Location_Input[0:4] == "SA45" or \
            Location_Input[0:4] == "SA46" or Location_Input[0:4] == "SA47" or Location_Input[0:4] == "SA48" or \
            Location_Input[0:4] == "SA61" or Location_Input[0:4] == "SA62" or Location_Input[0:4] == "SA63" or \
            Location_Input[0:4] == "SA64" or Location_Input[0:4] == "SA65" or Location_Input[0:4] == "SA66" or \
            Location_Input[0:4] == "SA67" or Location_Input[0:4] == "SA68" or Location_Input[0:4] == "SA69" or \
            Location_Input[0:4] == "SA70" or Location_Input[0:4] == "SA71" or Location_Input[0:4] == "SA72" or \
            Location_Input[0:4] == "SA73" or Location_Input[0:4] == "SY15" or Location_Input[0:4] == "SY16" or \
            Location_Input[0:4] == "SY17" or Location_Input[0:4] == "SY18" or Location_Input[0:4] == "SY19" or \
            Location_Input[0:4] == "SY20" or Location_Input[0:4] == "SY21" or Location_Input[0:4] == "SY22" or \
            Location_Input[0:4] == "SY23" or Location_Input[0:4] == "SY24" or Location_Input[0:4] == "SY25":
        EPC_Ambient = [5.0, 5.3, 6.5, 8.5, 11.2, 13.7, 15.3, 15.3, 13.5, 10.7, 7.8, 5.2]  # Region 13
        EPC_Irradiance = [29, 57, 104, 164, 205, 220, 199, 167, 120, 68, 35, 22]  # Wales
    elif Location_Input[0:2] == "FK" or Location_Input[0:2] == "KA" or Location_Input[0:2] == "ML" or \
            Location_Input[0:2] == "PA" or Location_Input[0:4] == "PH49" or Location_Input[0:4] == "PH50":
        EPC_Ambient = [4.0, 4.4, 5.6, 7.9, 10.4, 13.0, 14.5, 14.4, 12.5, 9.3, 6.5, 3.8]  # Region 14
        EPC_Irradiance = [19, 46, 88, 148, 196, 193, 185, 150, 101, 55, 25, 15]  # West Scotland
    elif Location_Input[0:2] == "DD" or Location_Input[0:2] == "EH" or Location_Input[0:2] == "KY":
        EPC_Ambient = [3.6, 4.0, 5.4, 7.7, 10.1, 12.9, 14.6, 14.5, 12.5, 9.2, 6.1, 3.2]  # Region 15
        EPC_Irradiance = [21, 46, 89, 146, 198, 191, 183, 150, 106, 57, 27, 15]  # East Scotland
    elif Location_Input[0:2] == "AB" or Location_Input[0:4] == "IV30" or Location_Input[0:4] == "IV31" or \
            Location_Input[0:4] == "IV32" or Location_Input[0:4] == "IV36" or Location_Input[0:4] == "PH26":
        EPC_Ambient = [3.3, 3.6, 5.0, 7.1, 9.3, 12.2, 14.0, 13.9, 12.0, 8.8, 5.7, 2.9]  # Region 16
        EPC_Irradiance = [19, 45, 89, 143, 194, 188, 177, 144, 101, 54, 25, 14]  # North East Scotland
    elif Location_Input[0:2] == "IV" or Location_Input[0:4] == "PH19" or Location_Input[0:4] == "PH20" or \
            Location_Input[0:4] == "PH21" or Location_Input[0:4] == "PH22" or Location_Input[0:4] == "PH23" or \
            Location_Input[0:4] == "PH24" or Location_Input[0:4] == "PH25" or Location_Input[0:4] == "PH30" or \
            Location_Input[0:4] == "PH31" or Location_Input[0:4] == "PH32" or Location_Input[0:4] == "PH33" or \
            Location_Input[0:4] == "PH34" or Location_Input[0:4] == "PH35" or Location_Input[0:4] == "PH36" or \
            Location_Input[0:4] == "PH37" or Location_Input[0:4] == "PH38" or Location_Input[0:4] == "PH39" or \
            Location_Input[0:4] == "PH40" or Location_Input[0:4] == "PH41" or Location_Input[0:4] == "PH42" or \
            Location_Input[0:4] == "PH43" or Location_Input[0:4] == "PH44":
        EPC_Ambient = [3.1, 3.2, 4.4, 6.6, 8.9, 11.4, 13.2, 13.1, 11.3, 8.2, 5.4, 2.7]  # Region 17
        EPC_Irradiance = [17, 43, 85, 145, 189, 185, 170, 139, 98, 51, 22, 12]  # Highlands
    elif Location_Input[0:2] == "HS":
        EPC_Ambient = [5.2, 5.0, 5.8, 7.6, 9.7, 11.8, 13.4, 13.6, 12.1, 9.6, 7.3, 5.2]  # Region 18
        EPC_Irradiance = [16, 41, 87, 155, 205, 206, 185, 148, 101, 51, 21, 11]  # Western Isles
    elif Location_Input[0:4] == "KW15" or Location_Input[0:4] == "KW16" or Location_Input[0:4] == "KW17":
        EPC_Ambient = [4.4, 4.2, 5.0, 7.0, 8.9, 11.2, 13.1, 13.2, 11.7, 9.1, 6.6, 4.3]  # Region 19
        EPC_Irradiance = [14, 39, 84, 143, 205, 201, 178, 145, 100, 50, 19, 9]  # Orkney
    elif Location_Input[0:2] == "ZE":
        EPC_Ambient = [4.6, 4.1, 4.7, 6.5, 8.3, 10.5, 12.4, 12.8, 11.4, 8.8, 6.5, 4.6]  # Region 20
        EPC_Irradiance = [12, 34, 79, 135, 196, 190, 168, 144, 90, 46, 16, 7]  # Shetland
    elif Location_Input[0:2] == "BT":
        EPC_Ambient = [4.8, 5.2, 6.4, 8.4, 10.9, 13.5, 15.0, 14.9, 13.1, 10.0, 7.2, 4.7]  # Region 21
        EPC_Irradiance = [24, 52, 96, 155, 201, 198, 183, 150, 107, 61, 30, 18]  # Northern Ireland

    # Need to be after other options
    elif Location_Input[0:2] == "NP" or Location_Input[0:2] == "SA" or Location_Input[0:2] == "SN" or \
            Location_Input[0:2] == "SP":
        EPC_Ambient = [4.9, 5.3, 7.0, 9.3, 12.2, 15.0, 16.7, 16.7, 14.4, 11.1, 7.8, 4.9]
        # Region 5 "NP" before "N"
        EPC_Irradiance = [32, 59, 105, 167, 201, 226, 206, 175, 130, 74, 40, 25]  # Severn England and Wales
    elif Location_Input[0:1] == "E" or Location_Input[0:2] == "EN" or Location_Input[0:2] == "GU" or \
            Location_Input[0:1] == "N" or Location_Input[0:2] == "RG" or Location_Input[0:2] == "RH" or \
            Location_Input[0:1] == "W":
        EPC_Ambient = [5.1, 5.6, 7.4, 9.9, 13.0, 16.0, 17.9, 17.8, 15.2, 11.6, 8.0, 5.1]  # Region 1
        EPC_Irradiance = [30, 56, 98, 157, 195, 217, 203, 173, 127, 73, 39, 24]  # Thames
    elif Location_Input[0:1] == "B" or Location_Input[0:2] == "SY":
        EPC_Ambient = [4.3, 4.8, 6.6, 9.0, 11.8, 14.8, 16.6, 16.5, 14.0, 10.5, 7.1, 4.2]  # Region 6
        EPC_Irradiance = [28, 55, 97, 153, 191, 208, 194, 163, 121, 69, 35, 23]  # Midlands
    elif Location_Input[0:1] == "L" or Location_Input[0:2] == "LA" or Location_Input[0:2] == "LL" or \
            Location_Input[0:1] == "M" or Location_Input[0:2] == "SK":
        EPC_Ambient = [4.7, 5.2, 6.7, 9.1, 12.0, 14.7, 16.4, 16.3, 14.1, 10.7, 7.5, 4.6]  # Region 7
        EPC_Irradiance = [24, 51, 95, 152, 191, 203, 186, 152, 115, 65, 31, 20]  # West Pennines England and Wales
    elif Location_Input[0:2] == "SR":
        EPC_Ambient = [4.0, 4.5, 5.8, 7.9, 10.4, 13.3, 15.2, 15.1, 13.1, 9.7, 6.6, 3.7]  # Region 9
        EPC_Irradiance = [23, 50, 92, 151, 200, 196, 187, 153, 11, 61, 30, 18]  # Boarders
    elif Location_Input[0:2] == "YO":
        EPC_Ambient = [4.0, 4.6, 6.1, 8.3, 10.9, 13.8, 15.8, 15.6, 13.5, 10.1, 6.7, 3.8]  # Region 10
        EPC_Irradiance = [25, 51, 95, 152, 196, 198, 190, 156, 115, 64, 32, 20]  # North East England
    elif Location_Input[0:1] == "S":
        EPC_Ambient = [4.3, 4.9, 6.5, 8.9, 11.7, 14.6, 16.6, 16.4, 14.1, 10.6, 7.1, 4.2]  # Region 11
        EPC_Irradiance = [26, 54, 96, 150, 192, 200, 189, 157, 115, 66, 33, 21]  # East Pennines
    elif Location_Input[0:1] == "G":
        EPC_Ambient = [4.0, 4.4, 5.6, 7.9, 10.4, 13.0, 14.5, 14.4, 12.5, 9.3, 6.5, 3.8]  # Region 14
        EPC_Irradiance = [19, 46, 88, 148, 196, 193, 185, 150, 101, 55, 25, 15]  # West Scotland
    elif Location_Input[0:2] == "PH":
        EPC_Ambient = [3.6, 4.0, 5.4, 7.7, 10.1, 12.9, 14.6, 14.5, 12.5, 9.2, 6.1, 3.2]  # Region 15
        EPC_Irradiance = [21, 46, 89, 146, 198, 191, 183, 150, 106, 57, 27, 15]  # East Scotland
    elif Location_Input[0:2] == "KW":
        EPC_Ambient = [3.1, 3.2, 4.4, 6.6, 8.9, 11.4, 13.2, 13.1, 11.3, 8.2, 5.4, 2.7]  # Region 17
        EPC_Irradiance = [17, 43, 85, 145, 189, 185, 170, 139, 98, 51, 22, 12]  # Highlands
    else:
        print("Postcode region can not be found")
        exit()

    # EPC CALCULATIONS
    def function_epc_day_calculation():
        nonlocal EPC_Day
        if m == 5 or m == 6 or m == 7 or m == 8:  # NO HEATING Jun, Jul, Aug, Sep, -1 for count
            epc_tstat = [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7]
        elif EPC_Day % 7 == 0 or (EPC_Day + 1) % 7 == 0:  # Weekend, not summer
            epc_tstat = [7, 7, 7, 7, 7, 7, 7, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
        else:  # Weekday, not summer
            epc_tstat = [7, 7, 7, 7, 7, 7, 7, 20, 20, 20, 7, 7, 7, 7, 7, 7, 20, 20, 20, 20, 20, 20, 20, 20]
        for h in range(24):
            nonlocal Inside_Temp
            nonlocal EPC_Demand
            
            incident_irradiance_gain = EPC_Irradiance[m] * (Ratio_SG_South[m] + Ratio_SG_North[m])
            solar_gain = incident_irradiance_gain * (House_Size * 0.15 / 2) * 0.77 * 0.7 * 0.76 * 0.9 / 1000  # kW
            heat_flow_out = (House_Size * Dwelling_U_Value_Current * (Inside_Temp - EPC_Ambient[m])) / 1000
            # heat_flow_out in kWh, +ve means heat flows out of building, -ve heat flows into building
            Inside_Temp += ((- heat_flow_out + solar_gain + EPC_Body_Gain) / Heat_Capacity)

            if Inside_Temp > epc_tstat[h]:  # Warm enough already, NO heating required
                space_hr_demand = 0
            else:  # Requires heating
                space_hr_demand = (epc_tstat[h] - Inside_Temp) * Heat_Capacity
                Inside_Temp = epc_tstat[h]
            EPC_Demand += (space_hr_demand / 0.9)  # 90% efficient gas boiler
        EPC_Day += 1

    Dwelling_U_Value_Current = 0.5
    Optimised_EPC_Demand = EPC_Demand_Previous = 0
    for Iteration in range(251):  # 0.5 to 3.0
        EPC_Day = 1
        Inside_Temp = 20  # Initial temperature
        EPC_Demand = 0
        for m in range(12):  # EPC LOOP
            if m == 3 or m == 5 or m == 8 or m == 10:  # Months with 30 days -1, as for loop starts at 0
                for d in range(30):
                    function_epc_day_calculation()
            elif m == 1:
                for d in range(28):
                    function_epc_day_calculation()
            else:
                for d in range(31):
                    function_epc_day_calculation()
        if ((EPC_Space_Heating - EPC_Demand) ** 2) ** 0.5 < ((EPC_Space_Heating - Optimised_EPC_Demand) ** 2) ** 0.5:
            Optimised_EPC_Demand = EPC_Demand
            Dwelling_U_Value = Dwelling_U_Value_Current
        elif ((EPC_Space_Heating - EPC_Demand) ** 2) ** 0.5 > ((EPC_Space_Heating - EPC_Demand_Previous) ** 2) ** 0.5:
            break  # finishes U-Value for loop
        EPC_Demand_Previous = EPC_Demand
        Dwelling_U_Value_Current += 0.01
        
    return Dwelling_U_Value

