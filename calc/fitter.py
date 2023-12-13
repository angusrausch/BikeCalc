from fitparse import FitFile
import math
import threading
import queue
import concurrent.futures
import numpy as np
from numba import jit, prange

from datetime import datetime, timezone, timedelta
# from timezonefinder import TimezoneFinder 
#python -m auto_py_to_exe

    
def process_l(l, lengths, recordArray, maxPower):
    for i in range(len(recordArray)):
        if i < len(recordArray) - lengths[l]:
            rollingavg = 0  
            for j in range(lengths[l]):
                if "power" in recordArray[i+j] and recordArray[i+j]["power"] is not None:
                    rollingavg += recordArray[i+j]["power"]
                            
            if rollingavg / lengths[l] > maxPower[l][0]: 
                maxPower[l] = [int(round(rollingavg / lengths[l], 0)), recordArray[i]]

def maxPowerFinder(recordArray, lengths):
    maxPower = [[0, None]] * len(lengths)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_l, l, lengths, recordArray, maxPower) for l in range(len(lengths))]
        # Wait for all threads to finish
        concurrent.futures.wait(futures)

    return maxPower

def averageFinder(recordArray):
    totalPower = 0
    totalPowerIterations = 0
    totalSpeed = 0
    totalSpeedIterations = 0
    totalHeartRate = 0
    totalHeartRateIterations = 0
    for i in range(len(recordArray)):
        if "power" in recordArray[i] and recordArray[i]["power"] != None and recordArray[i]["power"] != 0:
            totalPower += recordArray[i]['power']
            totalPowerIterations += 1
        if "enhanced_speed" in recordArray[i] and recordArray[i]["enhanced_speed"] != None and recordArray[i]["enhanced_speed"] != 0:
            totalSpeed += recordArray[i]['enhanced_speed'] * 3.6
            totalSpeedIterations += 1
        if 'heart_rate' in recordArray[i] and recordArray[i]["heart_rate"] != None and recordArray[i]["heart_rate"] != 0:
            totalHeartRate += recordArray[i]['heart_rate']
            totalHeartRateIterations += 1

    averageHeartRate = 0
    averagePower = 0
    averageSpeed = 0

    if totalPowerIterations > 0: averagePower = round(totalPower / totalPowerIterations, 1)
    if totalSpeedIterations > 0: averageSpeed = round(totalSpeed / totalSpeedIterations, 1)
    if totalHeartRateIterations > 0: averageHeartRate = round(totalHeartRate / totalHeartRateIterations, 0)

    return [averagePower, averageSpeed, averageHeartRate]

def gradeFinder(recordArray):
    steepest = None
    for i in range(len(recordArray)):
        if "grade" in recordArray[i]:
            if steepest == None or recordArray[i]["grade"] > steepest["grade"]:
                steepest = recordArray[i + 1]
    return steepest

def speedFinder(recordArray):
    fastest = None
    for i in range(len(recordArray)):
        if "enhanced_speed" in recordArray[i]:
                if fastest == None or recordArray[i]["enhanced_speed"] > fastest["enhanced_speed"]:
                    fastest = recordArray[i]
    return fastest

def torqueFinder(recordArray):
    maxTorque = None
    for i in range(len(recordArray)):        
        if "power" in recordArray[i] and recordArray[i]["power"] != None: 
            if recordArray[i]["power"] > 0 and recordArray[i]["cadence"] > 30:
                torque = round(float(recordArray[i]["power"] * 60) / float(2 * math.pi * recordArray[i]["cadence"]), 1)
                recordArray[i]["torque"] = torque
                if maxTorque == None or torque > maxTorque['torque']:
                    maxTorque = recordArray[i]
    return maxTorque

def splitIntArray(input_string):
    # Split the input string into individual values using comma as the delimiter
    values = input_string.split(',')
    
    # Initialize an empty list to store the resulting integers
    int_array = []
    
    # Convert the split values to integers, handling conversion errors
    for value in values:
        try:
            int_value = int(value)
            int_array.append(int_value)
        except ValueError:
            print(f"Error: Could not convert '{value}' to an integer. Skipping.")
    
    return int_array




def processing(fit_file, crank):

    crank = crank / 1000

    recordArray = []
    recordNumber = 0
    for record in fit_file.get_messages("record"):
        dict = record.get_values()
        recordArray.append(dict)
        recordNumber += 1

    
    averageReturn = averageFinder(recordArray)
    averageSpeed = averageReturn[1]
    averagePower = averageReturn[0]
    averageHR = averageReturn[2]

    lengths = [1,3,5,10,20,60, 300,1200]
    maxPower = maxPowerFinder(recordArray, lengths)
    steepest = gradeFinder(recordArray)
    fastest = speedFinder(recordArray)
    maxTorque = torqueFinder(recordArray)

    
    # # print(recordArray[int(len(recordArray) / 2)])
    # # 'position_lat': -32 8000740
    # # 'position_long': 182 6033027
    # lat = recordArray[int(len(recordArray) / 2)]['position_lat']
    # long = recordArray[int(len(recordArray) / 2)]['position_long']
    # # print(lat)
    # # print(len(str(lat)))
    # str_lat = str(lat)
    # revised_lat = float(str_lat[ : (len(str_lat) - 7)] + "." + str_lat[(len(str_lat) - 7): ])
    # # print(revised_lat)
    # str_long = str(long)
    # revised_long = float(str_long[ : (len(str_long) - 8)] + "." + str_long[(len(str_long) - 8): ])
    # # print(revised_long)
    # tzfinder = TimezoneFinder() 
    # # print(tzfinder.timezone_at(lng=revised_long, lat=revised_lat))

    date = recordArray[0]['timestamp']
    date = date + timedelta(hours=10)

    timeDelta = recordArray[len(recordArray) - 1]['timestamp'] - recordArray[0]['timestamp']
    distance = round(recordArray[len(recordArray) - 1]['distance'] / 1000, 1)
    altGain = recordArray[len(recordArray) - 1]['ascent']

    processed_max_power = []
    for i in range(len(lengths)):
        processed_max_power.append({'time': lengths[i], 'power': maxPower[i][0], 'distance': round(maxPower[i][1]['distance'] / 1000, 1), 'grade': maxPower[i][1]['grade'], 'cadence': maxPower[i][1]['cadence'], 'heartrate': maxPower[i][1]['heart_rate'], 'speed': round(maxPower[i][1]['enhanced_speed']*3.6, 1), 'torque': maxPower[i][1]['torque'] })

    processed_fastest = {'speed': round(fastest['enhanced_speed']*3.6, 1), 'grade': fastest['grade'], 'power': fastest['power'], 'distance': fastest['distance'], 'cadence': fastest['cadence']}
    processed_steepest = {'grade': steepest["grade"], 'speed': round(steepest['enhanced_speed']*3.6, 1), 'cadence': steepest['cadence']}
    processed_max_torque = {'torque': maxTorque['torque'], 'power': maxTorque['power'], 'cadence': maxTorque['cadence'], 'grade': maxTorque['grade'], 'kgs':round((maxTorque['torque']/crank)/9.80665, 1)}

    return {'avgspd': averageSpeed,
            'avghr': averageHR,
            'avgpower': averagePower,
            'maxpower': processed_max_power,
            'steepest': processed_steepest,
            'fastest': processed_fastest,
            'maxtorque': processed_max_torque,
            'date': date.strftime("%A, %B %d, %Y"),
            'time': timeDelta,
            'distance': distance,
            'altgained': altGain}





@jit(nopython=True, parallel=True)
def powerCurveEfficient(recordArray, power_curve):
    length = len(recordArray)
    maxavg = 0.0  # Initial value for maxavg

    for l in prange(1, length + 1):  # Adjust the range to avoid zero-size arrays
        maxavg = 0.0

        for i in range(length - l + 1):
            subarray = recordArray[i:i + l]

            # Replace None values with zeros
            subarray = np.array([value if value is not None else 0.0 for value in subarray], dtype=np.float64)

            # Calculate the average power for the subarray
            total = np.sum(subarray)
            count = np.count_nonzero(subarray)
            avg_power = total / count if count > 0 else 0

            maxavg = max(maxavg, avg_power)

        # Update power_curve with the maximum average power for the given subarray size
        power_curve[l - 1] = maxavg
        # print(f"Maximum Average Power for subarray size {l}: {maxavg}")

    return power_curve

def powerCurveMaker(recordArray):
    recordArray = np.array(recordArray, dtype=np.float64)  # Convert to NumPy array with specific dtype
    length = len(recordArray)
    power_curve = np.zeros(length, dtype=np.float64)

    power_curve = powerCurveEfficient(recordArray, power_curve)

    return power_curve