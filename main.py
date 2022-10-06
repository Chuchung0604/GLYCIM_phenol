# -*- coding: utf-8 -*-
"""
Created on Thu Oct  6 16:17:13 2022

@author: ccchen
"""

from datetime import datetime
import phenGLYCIM 
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

latitude=24.0
date0str = input("請輸入播種日期(yyyy-mm-dd):")
startDate = datetime.strptime(date0str,"%Y-%m-%d")
filename = 'wea.csv'
JdayFirst = startDate.timetuple().tm_yday


daycounter = 0
pltdate =[]
pltlv =[]
pltstage = []

#呼叫Development 物件
Soybean = phenGLYCIM.Development(24.0,JdayFirst)



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
 
      Temp = row[4:28]
      Soybean.update(DOY,Temp)
      vstage = Soybean.VSTAGE
      rstage = Soybean.RSTAGE
      #leaftip = int(maize.leafAppeared)
      cumTemp = round(float(Soybean.DDAE))
      
      if Soybean.RSTAGE >= 8:
          break
     
      print(datestr, "V=",round(vstage,1),"R=",round(rstage,1))
      
#       # making plot
#       pltdate.append(date)
#       pltlv.append(float(Soybean.RSTAGE))
#       pltstage.append(stg)
#       daycounter += 1



# lable_corn =  ["Sowing","Germination","Sowing","Flowering","Silking"]
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b%d'))
# plt.xlabel('Date')
# plt.ylabel('Leaf tip')



# plt.scatter(pltdate,pltlv, c=pltstage)
# # plt.scatter(obs.dateleaf,obs.leaftip,marker='x')
# # plt.scatter(obs.dateflowering,obs.flowering, marker='D')
# # plt.scatter(obs.datesilking,obs.silking, marker='s')

# plt.show()