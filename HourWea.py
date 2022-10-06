# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 17:09:33 2022
@author: ccchen
"""
import math
import csv
import pandas as pd

# This submodel was written to simulate hourly temperature from daily value. It was designed to
# connect with process based crop model. The following scripts were rewritten from 2DSOIL model,
# simulators for elements of energy movement within soil profile, given from Dr. Timlin. 
# For the concepts of the model, please chek: Timlin, D.J. et al.(2002) Error analysis of soil 
# temperature simulations using measured and estimated hourly weather data with 2DSOIL. 
# Agricultural system 72:215-139.
# Also check Reicosky, D.C. et al. (1989) Accuracy of hourly air temperatures calculated from 
# daily minima and maxima. Agricultural and Forest Meterology, 46: 193-209. That paper describes
# the GLYCIM method on hourly temperature calculation.


# universal variable
DEGRAD = 0.017453293 # 1/180 * pi 

def makeTempList(tmin_lst, tmax_lst, DO2Y):
    posit = DO2Y - 1 # the list value started at position 0
    Tmin_yest = tmin_lst[posit-1]      
    Tmax_yest = tmax_lst[posit-1]
    Tmin = tmin_lst[posit]
    Tmax = tmax_lst[posit]
    Tmin_tom = tmin_lst[posit+1]
    Tmax_tom = tmax_lst[posit+1]
    tempList = [[Tmin_yest,Tmax_yest], [Tmin,Tmax], [Tmin_tom,Tmax_tom]]
        
    return tempList # end of the function
    
    
#--------- (inciden radiation submodel) ----------

class Radiation:    
    SDERP = {1:0.3964, 2:3.631, 3:0.03838, 4:0.07659, 5: 0.0,
             6:-22.97, 7:-0.3885, 8:-0.1587, 9:-0.01021}
    
    def __init__(self,lat):
        self.DAYLNG = 0  # day length        
        self.DEC = 0.3964 # solar declination
        self.lat = lat
        self.XLAT = lat * DEGRAD # latitude in grade
        self.maxDayLength()
        
    
    def theory(self, JDAY):
        DOY = JDAY
        self.solarDeclination(DOY)
        self.dayLength()
        self.WATPOT = self.potentialRad(DOY)

    def solarDeclination(self,JDAY):
        # Roberson and Ruselo (1968)
        self.DEC = self.SDERP[1]
        for i in range(2,6):
            N = i - 1
            j = i + 4
            D11 = N*0.01721*JDAY            
            self.DEC += self.SDERP[i]*math.sin(D11) + self.SDERP[j]*math.cos(D11)
        self.DEC = self.DEC * DEGRAD
                        
    def dayLength(self):
        # Smithonian Meterological Table, 1966 p. 495
        D12 = math.sin(self.XLAT) * math.sin(self.DEC)
        D13 = math.cos(self.XLAT) * math.cos(self.DEC)
        self.DAYLNG = math.acos((-0.014544 - D12)/D13) * 7.6394
        # 7.6394 = 180/3.1416/360*24*2
    
    def maxDayLength(self):
        DOY = 173
        DEC173 = self.SDERP[1]
        for i in range(2,6):
            N = i - 1
            j = i + 4
            D11 = N*0.01721*DOY
            DEC173 += self.SDERP[i]*math.sin(D11) + self.SDERP[j]*math.cos(D11)
        DEC173 = DEC173 * DEGRAD
        D12 = math.sin(self.XLAT) * math.sin(DEC173)
        D13 = math.cos(self.XLAT) * math.cos(DEC173)
        self.DLNGMAX = math.acos((-0.014544 - D12)/D13) * 7.6394
        # 7.639437 = 24/pi
        
        
        
    def potentialRad(self,JDAY):
        # solar radiation indicent
        D12 = math.sin(self.XLAT) * math.sin(self.DEC)
        D13 = math.cos(self.XLAT) * math.cos(self.DEC) 
        D14 = D12 + D13
        RADVEC = 1 + (0.01674*math.sin(JDAY-93.5)*0.9863*DEGRAD)
        WATATM = 1325.4 * D14/(RADVEC*DEGRAD) # radiation incident at the top of the 
        # atmosphere at noon (W/m2)
        
        # atmospheric transmission 
        if JDAY < 145:
            ATRANS = 0.68 + (145-JDAY)*(1.57*self.lat/30 - 0.1)/1000
        elif JDAY <= 237:
            ATRANS = 0.68
        else:
            if self.lat <= 30:
                D15 = (self.lat * 5.25E-5) - 0.1E-3
            else:
                D15 = 0.65E-3 + self.lat * 3.0E-5
            ATRANS = 0.68 + D15 * (JDAY - 237)
        
        # calculate potential direct + diffuce radiation incident on crop at noon
        potRad = WATATM*0.5*(0.93 - 0.02/D14 + pow(ATRANS,1/D14))
        
        return potRad


class TemperatureHr:
    # generate
    def __init__(self):
        self.Tmax_yest = 24
        self.Tmin_yest = 20
        self.Tmax = 24
        self.Tmin = 20
        self.Tmax_tom = 24
        self.Tmin_tom = 20
        self.TDUSKY = 0
        self.WATACT = 200 # W/m2
        self.TempH = {1:10, 2:10, 3:10, 4:10, 5:10, 6:10, 7:10, 8:10, 9:10, 10:10,
                      11:10, 12:10, 13:10, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10,
                      20:10, 21:10, 22:10, 23:10, 24:10} # list content hourly value
    
    def Hourly(self,day_leng,tempList,solRad):

        daylength = day_leng
        self.Tmin_yest = tempList[0][0]
        self.Tmax_yest = tempList[0][1]
        self.Tmin = tempList[1][0]
        self.Tmax = tempList[1][1]
        self.Tmin_tom = tempList[2][0]
        self.Tmax_tom = tempList[1][1]
        # solRad read from TCCIP is W/m2 per hour
        # solRad = solRad*24/(dayLength)
        self.WATACT = solRad/daylength/3600 # same as GLYCIM   line 991
        self.convertHourly(daylength) # end of the method
        
    def convertHourly(self,daylength):
        
        DAYLNG = daylength
        DAWN = 12 - (DAYLNG/2)
        DUSK = 12 + DAYLNG/2
        if self.TDUSKY == 0:
            self.TDUSKY = (self.Tmax + self.Tmin)/2

        # calculate time after doawn in hours when maximum temp is reached
        D20 = 0.0945 - (self.WATACT* 8.06E-05 * 2.0/math.pi)  + (self.Tmax * 6.77E-04)
        D21 = self.Tmax/D20/self.WATACT
        #print("D21=%f" %D21)
        D21 = min(D21,1)
        TMAXHR = DAYLNG/math.pi * (math.pi - math.asin(D21))

        # calculate air temp at dusk TDUSK
        D22 = (self.Tmax - self.Tmin) / 2
        D23 = math.pi/TMAXHR
        D24 = 1.5*math.pi
        TDUSK = (D22 * (1.0 + math.sin((D23*DAYLNG + D24)))) + self.Tmin
        
        # some parts of temperature equation
        XTEMP = 2.0
        if self.Tmin < self.TDUSKY:
            D25 = self.TDUSKY - self.Tmin + XTEMP
            D26 = math.log(D25/XTEMP) / (2 * DAWN)
        else:
            D27 = (self.Tmin - self.TDUSKY)/ (2 * DAWN)
            
        if self.Tmin_tom < TDUSK:
            D28 = TDUSK - self.Tmin_tom + XTEMP
            D29 = math.log(D28/XTEMP) / (2 * DAWN)
        else:
            D30 = (self.Tmin_tom - TDUSK) / (2 * DAWN)
        # calculate air temperature at each time
        for h in range(1,25):
            TIMH = h - 0.0
            if TIMH >= DAWN and TIMH <= DUSK: # 白天
                T01 = self.Tmin + D22 * (1 + math.sin(D23*(TIMH-DAWN)+D24))
                self.TempH[h] = T01
            elif TIMH < DAWN: # 清晨
                if self.Tmin < self.TDUSKY:
                    T01 = self.Tmin - XTEMP + D25/math.exp(D26*(DAWN + TIMH))
                    self.TempH[h] = T01
                else:
                    T01 = self.TDUSKY + D27*(DAWN+TIMH)
                    self.TempH[h] = T01
            elif TIMH > DUSK: # 晚上
                if self.Tmin_tom < TDUSK:
                    T01 = self.Tmin_tom - XTEMP + (D28/math.exp(D29*(TIMH-DUSK)))
                    self.TempH[h] = T01
                else:
                    T01 = TDUSK + D30*(TIMH - DUSK)
                    self.TempH[h] = T01
        self.TDUSKY = TDUSK
        # end of the method

    
class TemperatureHr3:
    # Cesaraccio et al. (2001) An improved model for determining degree-day
    # values from daily temperature data. Int. J. Biometerol. 45:161-169.
    def __init__(self):
        self.Tmax_yest = 24
        self.Tmin_yest = 20
        self.Tmax = 24
        self.Tmin = 20
        self.Tmax_tom = 24
        self.Tmin_tom = 20
        self.TDUSKY = 0
        self.WATACT = 200 # W/m2
        self.TempH = {1:10, 2:10, 3:10, 4:10, 5:10, 6:10, 7:10, 8:10, 9:10, 10:10,
                      11:10, 12:10, 13:10, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10,
                      20:10, 21:10, 22:10, 23:10, 24:10} # list content hourly value
    
    def Hourly(self,day_leng,tempList):

        daylength = day_leng
        self.Tmin_yest = tempList[0][0]
        self.Tmax_yest = tempList[0][1]
        self.Tmin = tempList[1][0]
        self.Tmax = tempList[1][1]
        self.Tmin_tom = tempList[2][0]
        self.Tmax_tom = tempList[1][1]
        #self.WATACT = solRad
        self.convertHourly(daylength) # end of the method
        
    def convertHourly(self,daylength):
                
        DAYLNG = daylength
        Hn = 12 - (DAYLNG/2) # sunrise hour
        Ho = 12 + DAYLNG/2 # sunset hour
        Hx = Ho - 4 # time of maximum temperature
        Hp = Hn + 24 # sunrise hour tomorrow
        
        # calculate air temperature at dust (To)
        # the 0.39 value was the empirical factor in the original paper
        To = self.Tmax - 0.39*(self.Tmax - self.Tmin_tom) # sunset temperature
        ToY = self.Tmax_yest - 0.39*(self.Tmax_yest - self.Tmin) # sunset temperature yesterday

        # calculate variable for three segment temperature
        D01 = self.Tmax - self.Tmin # alpha for 1st segment [eq 8]
        D02 = self.Tmax - To          # R for 2nd segment  [eq 9]
        D03 = (self.Tmin_tom - To)/math.sqrt(Hp - Ho) # b for 3rd segment [eq. 10]
        

        
        for h in range(1,25):
            if h <= Hn: # 清晨之前 用前一天的溫度算
                D00 = (self.Tmin - ToY)/math.sqrt(Hp - Ho)
                T01 = ToY + D00 * math.sqrt(h+24-Ho)
                self.TempH[h] = T01
            # elif h > Hn and h <= Hx: # 清晨到最高溫
            elif h <= Hx: # 清晨到最高溫
                S01 = (h - Hn)/(Hx - Hn)
                T01 = self.Tmin + D01 * math.sin(S01 *math.pi/2)
                self.TempH[h] = T01
            # elif h > Hx and h <= Ho:# 最高溫到日落
            elif h <= Ho:# 最高溫到日落
                S01 = (h - Hx)/4
                T01 = To + D02 * math.sin(math.pi/2 + S01*math.pi/2)
                self.TempH[h] = T01
            # elif h > Ho and h < Hp: # 日落到明天日昇
            else: # 日落到明天日昇
                T01 = To + D03 * math.sqrt(h-Ho)
                self.TempH[h] = T01
        # end of the method

    
            
# DEC - solar declination (太陽赤緯)
# DAYLNG - day length (h)
# WATATM - radiation incident at the top of the atmosphere at noon (W/m2)
# WATPOT - potential radiation incident at earth's surface at noon (W/m2)
# WATACT - actual radiation incident at eath's surface at noon (W/m2)
# JDAY - day of year
# h - hour value (0-24)
# TDUSKY - temperature at dusk in yesterday
# TDUSK - temperature at dusk
        

if __name__ == "__main__" : 
    # --------- read the temperature from TCCIP ---------
    # read weather from TCCIP file with specific location by "ReadWea"
    WEA = Radiation(22.1)
    #print(WEA.DLNGMAX)
    print(WEA.XLAT)
    print(WEA.DLNGMAX)
    


    
  
    
