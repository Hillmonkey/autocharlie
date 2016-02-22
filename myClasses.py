# -*- coding: utf-8 -*-
"""
Created on Sun Feb 14 15:45:49 2016

@author: lmadeo
"""
import admin
import datetime as DT
from dateutil.relativedelta import *
import calendar

class CurrentTime(object):
    '''
    CurrentTime is an object that needs to be instantiated each time 
    autoCharlie runs, presumably every hour, 15 minutes after the hour
    possible usage:
    charlieTime = CurrentTime()
    The CurrentTime object contains date/time data that all the shows in the 
        sched can reference as necessary, instead of each show maintaining its
        own copy
    '''   
    CTnow = DT.datetime.now() + relativedelta(hour=0, minute=0, second=0, microsecond=0)
    
    def __init__(self, CTnow):
        '''
        '''
        #expanded week, including SaturdayBEFORE and SundayAFTER
        #TODO: analyze which code needs to share this broadened num2day dict
        #which includes the day before the beginning of the week and the day
        #after
        self.num2day = { -1: 'SaturdayBEFORE', 0: 'Sunday' , 1 : 'Monday' , 
                        2 : 'Tuesday' , 3 :'Wednesday',  4 : 'Thursday' , 
                        5 : 'Friday' , 6 :'Saturday', 7 : 'SundayAFTER'}
            
        #bump now to minute #zero of new day
        self.now = CTnow
        self.today = DT.date.today()
        self.week = self.setWeek() # dict of datetimes for each day in week
        self.OWOMdict = {} #Ordinal Week of Month key=int, value = OWOM
        for day in self.week:
            self.OWOMdict[day] = setOrdinalWeekdayOfMonth(self,week[day])
        self.isEvenWeek = setIsEvenWeek(self)
        
    def setWeek(self):
        '''
        create a dict with same keys as self.num2day range(-1,8)
            values are time = 00:00:00 for each day of week
            type(value) = datetime.datetime
        '''
        myWeek = {}
        myWeek[0] = self.now + relativedelta(weekday = SU(-1))
        myWeek[-1] = myWeek[0] + relativedelta(days = -1)
        for day in range(1,8):
            myWeek[day] = myWeek[day-1] + relativedelta(days = +1) 
        return myWeek
        
    def setIsEvenWeek(self):
        '''
        '''
        jan1 = DT.datetime(year = self.now.year, month =1, day =1)
        diff = now - jan1
        weeks = (diff.days)/7
        if weeks % 2 == 0:
            return True
        else:
            return False
        
    def setOrdinalWeekdayOfMonth(self, aDT):
        '''
        aDT is a datetime
        type(aDT) = datetime.datetime
        returns OWOM int between 1 and 5
        OWOM = Ordinal Weekday of Month (ex: 3 = 3rd Thursday of (this) month)
        '''
        OWOM = aDT.day / 7 + 1 # int division works in Python 2.x
        return OWOM
            
class SchedTempTime(object):
    '''
    CurrentTime object should be initialized before SchedTempTime
    TempTime contains *show attributes* that need to be calculated each time
    the Sched is loaded from the drive, presumably by autoCharlie, then 
    attached to a show (see TempTime.__init__ docstring)
    '''
    Num2Day = { 0: 'Sunday' , 1 : 'Monday' , 2 : 'Tuesday' , 3 : 'Wednesday' ,
               4 : 'Thursday' , 5 : 'Friday' , 6 : 'Saturday',
               7: 'SundayAFTER'}
    Day2Num = {'Monday': 1, 'Tuesday': 2, 'Friday': 5, 'Wednesday': 3, 
               'Thursday': 4, 'Sunday': 0, 'Saturday': 6}
    D2Num = {'Sun': 0, 'Mon': 1, 'Tue': 2, 'Fri': 5, 'Wed': 3, 'Thu': 4, 'Sat': 6}
        #D2Num can be used to extract Num from aShow['Weekdays']
               
    def __init__(self, aShow, CTobj):
        '''
        instantiate  like so:
        aShow['TempTime'] = TempTime(aShow, aDay, CTobj)
        CTobj is a CurrentTime object that has already been instantiated
        '''
        #following line is separate for sake of possible future debugging
        self.DayOffset = setDayOffset(self, aShow) # zero or one
        self.fixedWeekday = D2Num[aShow['Weekdays']] + self.DayOffset #int
        self.OWOM = CTobj.OWOMdict[self.fixedWeekday]
        if aShow['Scheduled']:
            self.happensThisWeek = setHappensThisWeek(self, aShow, CTobj.OWOMdict)
        else:
            self.happensThisWeek = False
        
    def setHappensThisWeek(self, aShow, OWOMdict, CTobj):
        '''
        accepts aShow, and OrdinalWeekOfMonth dict
        returns true if aShow happens this week
        '''
        if aShow['SchedInfo'].alternationMethod == 'Every Week':
            return True
        elif aShow['SchedInfo'].alternationMethod == 'Alternate':
            if aShow['SchedInfo'].evenOdd == 'All':
                print 'AlternationMethod = Alternate, but evenOdd = all ...'
                admin.displayShow(aShow)
                print 'Fix this Shite!'
                continue ## maybe get to error handling situation
            if aShow['SchedInfo'].evenOdd == 'Even':
                if CTobj.obj.isEvenWeek:
                    return True
                else:
                    return False
            if aShow['SchedInfo'].evenOdd == 'Odd':
                if CTobj.obj.isEvenWeek:
                    return False
                else:
                    return True
            if aShow['SchedInfo'].evenOdd == 'N/A':
                print 'alternation = Alternate, but evenOdd = N/A!!!'
                print 'Fix this Schtuff!!!!
                continue # maybe get to bottom error condition???
        elif aShow['SchedInfo'].alternationMethod == "Week of the Month":
            if self.OWOM is in aShow['SchedInfo'].weekOfTheMonth:
                return True
            else:
                return False
        else:
            print 'you got to the bottom of the setHappensThisWeek function.'
            print "You're so effed!"
            admin.displayShow(aShow)
                
        
    def setDayOffset(self, aShow):
        '''
        returns either 0 or 1 to aid in compensating for the fact that overnight
            shows (0aam -6am) are associated with the previous day.
        NOTE: If a show straddles the traditional 6a.m. start of the broadcasting 
            day, chaos may ensue!
        '''
        dayOffset = 0
        myHour = int(aShow['OnairTime'].split(':')[0])
        #print 'myHour : ', str(myHour)
        if myHour <6: # show starts before 6am
            dayOffset = 1 
        return dayOffset
    
    def isInHour(self, lastHour):
        '''
        get lastHour from lastCompleteHour()
        boolean
        '''
        if int(self.HIW) == lastHour:
            return True
        else:
            return False
        
    def lastCompleteHour():
        '''
        OPTION #1:
        return hour, daydelta
            hour =int (last complete hour in range [0:23])
            dayDelta = 0 if day of lastCompleteHour = today
                     = -1 if lastCompleteHour is called during the first hour 
                         of today
        
        '''
        
class SchedInfo(object):
    '''
    SchedInfo contains show attributes that I am locally tacking onto
    the Schedule that was originally grab from Spinitron via the API.
    '''
    alternationMethodList = ['Every Week','Alternate','Week of the Month']
    evenOddList = ['Even','Odd','All','N/A']
    WOTMList = [1,2,3,4,5]
    
    def __init__(self, alternationMethod ='Every Week', evenOdd = 'All', WOTMList = [1,2,3,4,5]):
        '''
        create SchedInfo object with default values
        '''
        self.alternationMethod = alternationMethod
        self.evenOdd = evenOdd
        self.weekOfTheMonth = WOTMList #how does scope deal with definitions at top of class???
        
    def __str__(self):
        tab = '    '
        print
        print tab + self.alternationMethod
        print tab + self.evenOdd
        print tab + str(self.weekOfTheMonth)
        
    def __repr__(self):

        a = str( "{* ")
        a +=  str(self.alternationMethod) + ' , '
        a +=  str(self.evenOdd) + ', '
        a +=  str(self.weekOfTheMonth) + ' *}'
        return a
        
def NegOne():
    return -1

### MAIN ###
if __name__ == '__main__':
    print 'myClasses.py'