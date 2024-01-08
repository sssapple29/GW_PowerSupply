#This script is designed for SAT annealing via GW Instek PSS-2005 power supply
#Written by Huang Wun Cin, 2023/07/04, modified on 2023/10/24
import pyvisa
import time
import numpy as np
import threading

# instrument Setup
print('Notice : Donnot connect your power supply to the heating loop at this step!')
input()
rm = pyvisa.ResourceManager()
Device = rm.list_resources()
print('Device list:')
for k in range(len(Device)):
    print('<' + Device[k] + '> : Number ' + str(k))
print('\n')
N_device = input('Input the <Number> of device you want to connect (ex. 0, 1, 2......) --> ')
PS = rm.open_resource(Device[int(N_device)])  # choose the proper address for your instrument
print('Power supply detected => ' + PS.query('*IDN?'))  # chk communication is established or NOT
#PS.write(':SYSTem:ERRor ?')
print('Notice : Make sure this is your device again before doing next step!\n')
input()

#Set the initial condtion
PS.write(':OUTPut:STATe 0')
PS.write('CHAN1:VOLT 0')
PS.write('CHAN1:CURRent 0')

#Set the upper limit of voltage output
v_limit = 0
while (v_limit <= 0 or v_limit > 20) :
    #if (v_limit != 0):
    print('the value should be >0 and <=20')
    v_limit = input('Set the upper limit value of current for tip annealing (in volt) --> ')
    v_limit = float(v_limit)
    v_limit = float(format(v_limit, '.2f'))
print('The upper limit of voltage for tip annealing is ' + str(v_limit) + ' V.')
PS.write('CHAN1:VOLT ' + str(v_limit))
i_limit = float(v_limit)

#Turn on the output
PS.write(':OUTPut:STATe 1')
print('Connect the heating loop now.')
input()
#print('start annealing')

#Set the parameters for tip annealing
#Set the current value for tip annealing(0~5A, to two decimal places)
i = 0
while (i <= 0 or i > 5) :
    #if (i_2 != 0):
    print('the value should be >0 and <=5')
    i = input('Set the current for annealing  (in Ampere) --> ')
    i = float(i)
print('The current for annealing is ' + str(i) + ' A.')

# Set the time value for tip annealing
T1 = input('Set the "annealing heating up time" duration(in seconds) --> ')
print('The duration is ' + T1 + ' s.')
delt1 = input('Set the "annealing waiting time" (in seconds) --> ')
print('The duration is ' + delt1 + ' s.')
T2 = input('Set the "cooling time" duration(in seconds) --> ')
print('The duration is ' + T2 + ' s.')

i = float(format(i, '.2f'))
T1 = float(T1)
delt1 = float(delt1)
T2 = float(T2)
T_est = T1 + delt1 + T2
print('The estimated duration is about ' + str(T_est) + ' s.')
input()
        
# Function for current increasing
class Curr : 
    def __init__(self, I_init, I_final, I_d, T_d = 0.15) :
        # PS.write__init__(self)
        self.I_init = I_init
        self.I_final = I_final
        self.I_d = I_d
        self.T_d = T_d
    def CurrCtrl(self):
        #print('I_d is ' + str(self.I_d) + 's')
        Step = int(round(abs((self.I_final - self.I_init)/self.I_d)) + 1)
        Irange = np.round(np.linspace(self.I_init, self.I_final, Step)/0.01)*0.01
        Irange[len(Irange)-1] = self.I_final
        # print(I_step)
        for k in Irange:
            k = float(format(k, '.2f'))
            print(k)
            PS.write('CHAN1:CURRent ' + str(k))
            #print('T_d is ' + str(self.T_d) + 's')
            time.sleep(self.T_d)
        #Check if all assignment which is sent into PWsupply are done.
        time.sleep(0.1)
        PS.write('*OPC?')
        print(PS.read() == '1\n')

# Function for current increasing (Time period Controlling)
def CurrCtrl_const_slope(I_i, I_f, T = 10) :
    # print(I_inter)
    Nstep = T/0.15     #### 0.15s is the speed limit of your instrument
    Istep = (I_f - I_i)/Nstep 
    #Vstep = np.round(Vstep/0.01)*0.01   
    #print('Vstep is ' + str(Vstep) + 's')
    I = Curr(I_i, I_f, I_d = Istep)
    I.CurrCtrl() 
        
#Program for countdown the time period of current maintaining
def Countdown(Twait):
    T_clock = int(Twait)
    for i in range(T_clock+1):
        a = Twait - i
        a = float(format(a, '.2f'))
        print('Time for current holding remains : ' + str(a) + 's')
        time.sleep(1)
    time.sleep(Twait-T_clock)
#Program for output reading
class Output :
    def __init__(self, i_real = None, v_real = None) :
        self.i_real = i_real
        self.v_real = v_real
    def I_Read(self) :        
        PS.write('CHAN1:MEASure:CURRent ?')
        self.i_real = PS.read()
        self.i_real = float(self.i_real)
        print('i_real is ' + str(self.i_real) + ' A')
        return Output()

    def V_Read(self) :
        PS.write('CHAN1:MEASure:VOLT ?')
        self.v_real = PS.read()
        self.v_real = float(self.v_real)
        print('v_real is ' + str(self.v_real) + ' Volt')
        return Output()

tStart = time.time()

print('start annealing')
#Step1. Heating up from 0 to v
i0 = 0
Iup = threading.Thread(target = CurrCtrl_const_slope(i0, i, T = T1))
Iup.start()
Iup.join()

# Check if the output current and voltage 
# is the same with your setting, then anneal the tip at this current/volt setting
R = Output()
R.I_Read()
R.V_Read()
print('Setting Current Check: ') 
print(R.i_real == i)
print('i_real is ' + str(R.i_real) + ' A')
print('setting current is ' + str(i) + ' A')
print('Voltage Limit Check: ') 
print(R.v_real == v_limit)

if (R.i_real == i) or (R.v_real == v_limit):
    if(R.i_real == 0) :
        #Error message
        print('Error : No current output!') 
        print('Check the connection and the power supply again.') 
        PS.write(':OUTPut:STATe 0') 
        PS.write('CHAN1:CURRent 0')
    else :
        if (R.i_real != i) :
            print('The final "Current is constrained" by the upper limit of current.') 
    
        # Tip annealing
        # Wait delt1 seconds and measure the I&V output value
        Clock = threading.Thread(target = Countdown(delt1))
        Clock.start()
        # I&V Output reading
        R.I_Read()
        R.V_Read()

        #Step 3 Cooling down from v to 0 
        Idown = threading.Thread(target = CurrCtrl_const_slope(i, i0, T = T2))
        Idown.start()
        Idown.join()
        

else :
    #Error message
    print('Error:The final current is different from the setup, and the final voltage is not at the upper limit either.') 
    print('Check the connection and the power supply again.')
    #Cool down from v_real to 0 directly
    Idown0 = threading.Thread(target = CurrCtrl_const_slope(R.i_real, 0, T = 3))
    Idown0.start()
    Idown0.join()

#Disconnet with the power supply
PS.close()
print('process complete')
tEnd = time.time()#計時結束
print("It cost %f sec" % (tEnd - tStart))
input()