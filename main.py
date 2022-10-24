# -*- coding: utf-8 -*-
"""
Created on Thu Oct  6 16:17:13 2022

@author: ccchen
"""
from datetime import datetime
import phenGLYCIM 
import csv
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

Stage = {1:"開花期", 2:"開花期", 3:"始莢期", 4:"莢果完全發育", 
         5: "開始充實",6:"完全充實", 7:"開始成熟", 8:"完全成熟期"}

latitude=24.0
date0str = input("請輸入播種日期(yyyy-mm-dd):")
startDate = datetime.strptime(date0str,"%Y-%m-%d")
filename = 'wea.csv'
JdayFirst = startDate.timetuple().tm_yday


daycounter = 0
pltdate =[]
pltVstage =[]
pltRstage = []

#呼叫Development 物件
Soybean = phenGLYCIM.Development(latitude,JdayFirst)

# print("播種日期 = ", date0)
with open(filename, newline='') as csvfile:


  wea = csv.reader(csvfile)
  next(wea) # skip title

  for row in wea:
      date = datetime.strptime(row[0],"%m/%d/%Y")
      DOY = date.timetuple().tm_yday
      datestr = date.strftime("%m/%d/%Y")
#      date = datetime.strptime(row[0],"%Y-%m-%d")
      if date < startDate:
          continue
 
      Temp = row[1:24]
      Soybean.update(DOY,Temp)
      vstage = Soybean.VSTAGE
      rstage = Soybean.RSTAGE
      if rstage < 1:
          Rname = "營養生長期"
      elif rstage <= 6:
          Rname = Stage[math.floor(rstage)]
      elif rstage < 6.5:
          Rname = "毛豆採收適期"
      elif rstage < 7:
          Rname = Stage[7]
      else:
          Rname = Stage[math.floor(rstage)]
      #leaftip = int(maize.leafAppeared)
      cumTemp = round(float(Soybean.DDAE),0)
      
      #print(datestr, "V=",round(vstage,1),"R=",round(rstage,1))
      print(datestr, Rname, cumTemp)
      
      if Soybean.RSTAGE >= 8:
          break
    
#       # making plot
      pltdate.append(date)
      pltRstage.append(float(Soybean.RSTAGE))
      pltVstage.append(float(Soybean.VSTAGE))
      daycounter += 1

#lable_corn =  ["Sowing","Germination","Sowing","Flowering","Silking"]
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b%d'))
plt.xlabel('Date')
plt.ylabel('Stage')


plt.scatter(pltdate,pltRstage, c=pltRstage)
plt.scatter(pltdate,pltVstage)
# # plt.scatter(obs.dateleaf,obs.leaftip,marker='x')
# # plt.scatter(obs.dateflowering,obs.flowering, marker='D')
# # plt.scatter(obs.datesilking,obs.silking, marker='s')

plt.show()
