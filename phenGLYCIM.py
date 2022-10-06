# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 14:32:40 2019

@author: ccchen
"""

import HourWea


# latitude = 22.4

# WEA = HourWea.Radiation(latitude)
# DLNGMAX = WEA.DLNGMAX
# WEA.theory(JDAY)
# DAYLNG = WEA.DAYLNG
# DATE1 = "2022/02/03"


class Development:
    # Parameter of KH9
    Parm2 = 0.0125 #slope of V stage
    Parm3 = 8 # max V stage
    Parm4 = 1 #effect of clay to early V stage
    Parm5 = 0.087 #progress to R0 before Solstice
    Parm6 = 0.0262 #progress to R0 at Solstice
    Parm7 = 0.0212 #progress to R0 after Solstice
    Parm8 = 0.24 #R0 to R2
    Parm9 = 0.9656 #slope of R2 end on the RDFRST
    Parm10 = 40.068 #intercept R2 end on the RDFRST
    Parm11 = 0.01 #R2 to R6
    Parm12 = 190 # R5 plateau
    Parm13 = 280 # R6 plateau
    Parm14 = 1 #R6 decay as stress
    Parm15 = 0.00334 # rate to R7
    Parm16 = 5 #R stage stop V growth
    
    def __init__(self,lat,startday):
        # initialization 
        self.JDFRST = int(startday)
        self.DDAE = 0    # degree days after emergence
        self.DAE = 0     # days after emergence
        self.dt = 1/24
        self.VSTAGE = 0
        self.RSTAGE = -1
        self.IRFLAG1 = 0 #R1 
        self.IRFLAG4 = 0 #R4
        #latitude = 22.4
        self.DAYLNG = 0

        self.WEA = HourWea.Radiation(lat)
        self. DLNGMAX = self.WEA.DLNGMAX
        self.U5 = 0
        self.DU6 = 0

        #WEA.theory(JDAY)
        #DAYLNG = WEA.DAYLNG
        #DATE1 = "2022/02/03"

        # CALCULATE PROGRESS BETWEEN VSTAGES. DEGREE-DAYS, DAYS AFTER EMERGENCE, DEFICIT

    def update(self, jday,dayTemp):
        # should be called in daily timestep
        self.WEA.theory(jday)
        self.DAYLNG = self.WEA.DAYLNG

        # hourly time loop
        for tempH in dayTemp:
            tempH = float(tempH)
            self.DDAE += tempH * self.dt
            self.DAE += self.dt
            self.updateVstage(tempH)
            self.updateRstage(jday,tempH)
 
    # progress in V stage
    def updateVstage(self, hourT):
        
        U0=4E+04 * self.Parm2 -255.0  # degree days to V1
        UMAX= U0 + self.Parm3 / self.Parm2
        VMAX= self.Parm3            
        VOLD = self.VSTAGE
        
        if self.DDAE <= U0:
            self.VSTAGE = 0
        elif self.DDAE >= UMAX:
            self.VSTAGE = VMAX
        else:
            DV = self.Parm2 * hourT * self.dt
            self.VSTAGE += DV
            DV = self.VSTAGE - VOLD
    
    def updateRstage(self,jday, hourT):
        # Calculate progress in R stage
        # Progress towards R0(FLORAL INDUCTION)
        DR2=self.JDFRST* self.Parm9 + self.Parm10 -self.JDFRST # R2 date
        DDU5= self.Parm12  #degree days of R5 plateau
        # ILOW = 3
        # NTOPLF = self.VSTAGE
        
        ROLD = self.RSTAGE
        if self.RSTAGE < 0:
            if jday < 173:
                DR = (self.Parm5 + self.Parm6*(self.DAYLNG-self.DLNGMAX)) * self.dt
            else:
                DR = (self.Parm5 + self.Parm7*(self.DAYLNG-self.DLNGMAX)) * self.dt
            self.RSTAGE = self.RSTAGE + DR
        
            if self.RSTAGE >0:
                D11 = 1*(1+ROLD/DR)
                self.RSTAGE = D11 * self.Parm8
                
        # Progress toward R2 
        elif self.RSTAGE < 2:
            DR = self.Parm8 * self.dt
            self.RSTAGE = min(self.RSTAGE+DR, 2)
            if self.DAE > DR2:
                self.RSTAGE = 2 + (self.DAE-DR2)*self.Parm11 * hourT
            if self.RSTAGE >= 1 and self.IRFLAG1 == 0:
#                R1DATE = DATE1  # date of R1 stage
                self.IRGLAG = 1
                
        # R2 Plateau
        elif self.RSTAGE == 2.0:
            if self.DAE > DR2:
                #D12 = self.DAE-DR2
                self.RSTAGE = 2 + (self.DAE-DR2) * self.Parm11 * hourT
                
        # Progress to R5
        elif self.RSTAGE < 5:
            DR = self.Parm11 * hourT * self.dt   
            self.RSTAGE +=  DR
            # at find R4 date
            if self.RSTAGE >= 4 and self.IRFLAG4 == 0:
                #R4DATE = DATE1
                self.IRFLAG4 = 1
            # make the update R stage equal to R5 before finishing the R5 plateau
            
            if self.RSTAGE > 5:
               U5 = self.DDAE - ((self.RSTAGE-5)/DR) * hourT * self.dt
               self.U5 = U5
               #print("U5=",round(U5), "RSTAGE=",round(self.RSTAGE,2))
               self.RSTAGE = 5
               if self.DDAE > self.DDAE + DDU5: # R5 plateau
                   self.RSTAGE = 5 + (self.DDAE-U5-DDU5) * self.Parm11
           
        #R5 plateau
        elif self.RSTAGE == 5:

            if self.DDAE > self.U5 + DDU5:
                self.RSTAGE = 5 + (self.DDAE-self.U5-DDU5) * self.Parm11
        elif self.RSTAGE < 6:
           DR = self.Parm11 * hourT * self.dt
           self.RSTAGE += DR
           if self.RSTAGE > 6:
               U6 = self.DDAE - ((self.RSTAGE-6.0)/DR) * hourT * self.dt
               DDU6 = (self.DDAE-U6)/self.Parm13
               self.DU6 += DDU6
               self.RSTAGE = 6
               if self.DU6 > 1.0:
                   self.RSTAGE = 6.0 + self.Parm15 * hourT*(self.DU6-1.0)/DDU6
        
        # R6 plateau
        elif self.RSTAGE == 6.0 :
            # PLATEAU R6
            DDU6 = hourT/min(self.Parm13, max(0.001,self.Parm13-self.Parm14)) * self.dt
            self.DU6 += DDU6
            if self.DU6 > 1.0 :
                # PARTIAL PROGRESS TOWARDS R7
                self.RSTAGE = 6.0 + self.Parm15* hourT*(self.DU6-1.0)/DDU6
                
        elif self.RSTAGE < 7.0 :
            #  PROGRESS TOWARDS R7
            DR= self.Parm15 * hourT * self.dt
            self.RSTAGE += DR
              # # the original GLYCIM calculate the leaf drop by deficiency
              # ILOW = 3
              # J8 = NTOPLF-ILOW
              # if J8 <= 0 :
              #     DR8=DR
              # else :
              #     IPERD = 24
              #     DR8=1.0/(NTOPLF-ILOW)/IPERD
        else :
            # use the same rate from R7 to R8
            DR= self.Parm15 * hourT * self.dt
            self.RSTAGE += DR
            #  PROGRESS TOWARDS R8
            #DROP = 1
            #self.RSTAG += DR8
            if self.RSTAGE >= 8.0:
                MATURE = 1
   
if __name__ == "__main__" : 
    #print("hello")
    tempLst=[]
    for h in range(24):
        tempLst.append(20)
    Soybean = Development(22.1,22)
    for doy in range(20,300):
        Soybean.update(doy,tempLst)

        #print(Soybean.RSTAGE)
        print("JDAY=%d DAYLNG=%.2f"%(doy,Soybean.DAYLNG))
        if Soybean.RSTAGE>8:
            break
    #print(Soybean.RSTAGE)
    