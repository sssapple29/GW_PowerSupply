# GW_PowerSupply
These programs are designed for a three-step heating process for GW Power supply. 

You can choose current controll or voltage controll mode for heating based on your need.

The heating process has 3 steps. 
1. Heating process : The power supply will increase in current/voltage from 0 to the target value in a certain time period. 
2. Holding process : Following the step 1, the power supply will maintain the target current/voltage for a certain time period.
3. Cooling process :  Finally, the power supply will decrease in current/voltage from the target value to 0 in a defined time period.
At the commencement of the program, users have the flexibility to customize both the time periods for each step and the target values according to their preferences.

For your convenience, you can employ "pyinstaller -F .\FileName.py" to package your Python file into an executable (.exe) file.
