#This script is designed for SAT annealing by GW Instek PSS-2005
#Written by Huang Wun Cin, 2023/07/04, modified on 2023/07/07
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
PS.write('CHAN1:CURRent 0')
PS.write('CHAN1:VOLT 0')

#Set the upper limit of current output
i_limit = 0
while (i_limit <= 0 or i_limit > 5) :
    #if (v_limit != 0):
    print('the value should be >0 and <=5')
    i_limit = input('Set the upper limit value of current for tip annealing (in A) --> ')
    i_limit = float(i_limit)
    i_limit = float(format(i_limit, '.2f'))
print('The upper limit value of current for tip annealing is ' + str(i_limit) + ' A.')
PS.write('CHAN1:CURRent ' + str(i_limit))
i_limit = float(i_limit)

#Turn on the output
PS.write(':OUTPut:STATe 1')
print('Connect the heating loop now.')
input()
#print('start annealing')

#Set the parameters for tip annealing
#Set the voltage value for tip annealing(0~20V, to two decimal places)
v = 0
while (v <= 0 or v > 20) :
    #if (i_2 != 0):
    print('the value should be >0 and <=20')
    v = input('Set the annealing voltage (in Volt) --> ')
    v = float(v)
print('The annealing voltage is ' + str(v) + ' V.')

# Set the time value for tip annealing
T1 = input('Set the "annealing heating up time" duration(in seconds) --> ')
print('The duration is ' + T1 + ' s.')
delt1 = input('Set the "annealing waiting time" (in seconds) --> ')
print('The duration is ' + delt1 + ' s.')
T2 = input('Set the "cooling time" duration(in seconds) --> ')
print('The duration is ' + T2 + ' s.')

v = float(format(v, '.2f'))
T1 = float(T1)
delt1 = float(delt1)
T2 = float(T2)
T_est = T1 + delt1 + T2
print('The estimated duration is about ' + str(T_est) + ' s.')
input()
        
# Function for voltage increasing
class Volt : 
    def __init__(self, V_init, V_final, V_d, T_d = 0.15) :
        # PS.write__init__(self)
        self.V_init = V_init
        self.V_final = V_final
        self.V_d = V_d
        self.T_d = T_d
    def VoltCtrl(self):
        #print('V_d is ' + str(self.V_d) + 's')
        Step = int(round(abs((self.V_final - self.V_init)/self.V_d)) + 1)
        Vrange = np.round(np.linspace(self.V_init, self.V_final, Step)/0.01)*0.01
        Vrange[len(Vrange)-1] = self.V_final
        # print(I_step)
        for i in Vrange:
            i = float(format(i, '.2f'))
            print(i)
            PS.write('CHAN1:VOLT ' + str(i))
            #print('T_d is ' + str(self.T_d) + 's')
            time.sleep(self.T_d)
        #Check if all assignment which is sent into PWsupply are done.
        time.sleep(0.1)
        PS.write('*OPC?')
        print(PS.read() == '1\n')

# Function for voltage increasing (Time period setting)
def VoltCtrl_const_slope(V_i, V_f, T = 10) :
    # print(I_inter)
    Nstep = T/0.15     #### 0.15s is the speed limit of your instrument
    Vstep = (V_f - V_i)/Nstep 
    #Vstep = np.round(Vstep/0.01)*0.01   
    #print('Vstep is ' + str(Vstep) + 's')
    V = Volt(V_i, V_f, V_d = Vstep)
    V.VoltCtrl() 
        
#Program for countdown of voltage holding
def Countdown(Twait):
    T_clock = int(Twait)
    for i in range(T_clock+1):
        a = Twait - i
        a = float(format(a, '.2f'))
        print('Time for voltage holding remains : ' + str(a) + 's')
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
v0 = 0
Vup = threading.Thread(target = VoltCtrl_const_slope(v0, v, T = T1))
Vup.start()
Vup.join()

# Check if the output current and voltage 
# is the same with your setting, then anneal the tip
R = Output()
R.I_Read()
R.V_Read()
print('Voltage check: ') 
print(R.v_real == v)
print('v_real is ' + str(R.v_real))
print('setting voltage is ' + str(v))
print('Current check: ') 
print(R.i_real == i_limit)

if (R.v_real == v) or (R.i_real == i_limit):
    if(R.v_real == 0) :
        #Error message
        print('Error : No voltage output!') 
        print('Check the connection and the power supply again.') 
        PS.write(':OUTPut:STATe 0') 
        PS.write('CHAN1:VOLT 0')
    else :
        if (R.v_real != v) :
            print('The final "Voltage is constrained" by the upper limit of current.') 
    
        # Tip annealing
        # Wait delt1 seconds and measure the I&V output value
        Clock = threading.Thread(target = Countdown(delt1))
        Clock.start()
        # I&V Output reading
        R.I_Read()
        R.V_Read()

        #Step 3 Cooling down from v to 0 
        Vdown = threading.Thread(target = VoltCtrl_const_slope(v, v0, T = T2))
        Vdown.start()
        Vdown.join()
        

else :
    #Error message
    print('Error:The final voltage is different from the setup, and the final current is not at the upper limit either.') 
    print('Check the connection and the power supply again.')
    #Cool down from v_real to 0 directly
    Vdown0 = threading.Thread(target = VoltCtrl_const_slope(R.v_real, 0, T = 3))
    Vdown0.start()
    Vdown0.join()

#Disconnet with the power supply
PS.close()
print('process complete')
tEnd = time.time()#計時結束
print("It cost %f sec" % (tEnd - tStart))
input()