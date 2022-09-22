from socket import socket
import network 
from time import sleep, time
from picozero import pico_temp_sensor, pico_led
from machine import reset
from picographics import PicoGraphics, DISPLAY_LCD_240X240, PEN_P8
from breakout_bme68x import BreakoutBME68X, STATUS_HEATER_STABLE
from breakout_mics6814 import BreakoutMICS6814
from pimoroni_i2c import PimoroniI2C
from json import dumps

ssid = "MIWIFI_D64C"
password = "AEYU6A2E"

PINS_BREAKOUT_GARDEN = {"sda": 4, "scl": 5}

i2c = PimoroniI2C(**PINS_BREAKOUT_GARDEN)

bmp = BreakoutBME68X(i2c)

mics = BreakoutMICS6814(i2c)
mics.set_brightness(1.0)


def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f"IP {ip}")
    return ip

def open_socket(ip):
    address = (ip, 80)
    
    connection = socket()
    connection.bind(address)
    connection.listen(1)
    
    return connection


def webpage(data):
    
    html = f'''
<!DOCTYPE html>
<html>
    <body>
        <div>
            <table border="1px">
                <tr>
                    <td>
                        <form action="./lighton">
                            <input type="submit" value="Light on" />
                        </form>
                    </td>
                    <td>
                        <form action="./lightoff">
                            <input type="submit" value="Light off" />
                        </form>
                    </td>
                    <td>
                        <form action="./json">
                            <input type="submit" value="JSON" />
                        </form>
                    </td>
                </tr>
                <tr>
                    <th>Variable</th>
                    <th>Valor</th>
                    <th>Unidad</th>
                </tr>
                <tr>
                    <td>Temperatura</td>  
                    <td>{data["Temperatura"]}</td>  
                    <td>&deg;C</td>  
                </tr>
                <tr>
                    <td>Presi&oacute;n</td>  
                    <td>{data["Presion"]}</td>  
                    <td>Pa</td>  
                </tr>
                <tr>
                    <td>Humedad</td>  
                    <td>{data["Humedad"]}</td>  
                    <td>%</td>  
                </tr>
                <tr>
                    <td>Gases</td>  
                    <td>{data["Gases"]}</td>  
                    <td>&ohm;</td>  
                </tr>
                <tr>
                    <td>Calentador</td>  
                    <td>{data["Estado"]}</td>  
                    <td> </td>  
                </tr>
                <tr>
                    <td>Oxidantes</td>  
                    <td>{data["Oxidantes"]}</td>  
                    <td>&ohm;</td>  
                </tr>
                <tr>
                    <td>Reductores</td>  
                    <td>{data["Reductores"]}</td>  
                    <td>&ohm;</td>  
                </tr>
                <tr>
                    <td>NH3</td>  
                    <td>{data["NH3"]}</td>  
                    <td>&ohm;</td>  
                </tr>
                <tr>
                    <td>LED</td>  
                    <td>{data["LED"]}</td>  
                    <td> </td>  
                </tr>
                <tr>
                    <td>CPU Temp</td>  
                    <td>{data["CPU Temp"]}</td>  
                    <td>&deg;C</td>  
                </tr>
            </table>
        </div>
    </body>
</html>
            '''
    return html

def readBME():
    temperature, pressure, humidity, gas, status, _, _ = bmp.read()
    
    
    heater = "Estable" if status & STATUS_HEATER_STABLE else "Inestable"
    bme_data = {"Temperatura":round(temperature,2),
                "Presion":round(pressure,2),
                "Humedad":round(humidity,2),
                "Gases":round(gas,2),
                "Estado":heater}
    
    return bme_data

def readMICS():
    oxd = mics.read_oxidising()
    red = mics.read_reducing()
    nh3 = mics.read_nh3()
    
    mics_data = {"Oxidantes":round(oxd,2),
                 "Reductores":round(red,2),
                 "NH3":round(nh3,2)}
    
    return mics_data

def getJSON(led_state):
    json_data = {}
    json_data.update(readBME())
    json_data.update(readMICS())
    cpu_t = round(pico_temp_sensor.temp,1)
    json_data["CPU Temp"] = cpu_t
    json_data["LED"] = led_state
    return json_data

def serve(connection):
    state = "OFF"
    pico_led.off()
    temperature = 0
    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)
        try:
            request = request.split()[1]
        except IndexError:
            pass
        
        
        if "/json" in request:
            data = getJSON(state)
            json_str = dumps(data)
            client.send('HTTP/1.0 200 OK\r\nContent-type: text/plain-text\r\n\r\n')
            client.send(json_str)
            client.close()
        else:
            if request == "/lighton?":
                pico_led.on()
                state = "ON"
            elif request == "/lightoff?":
                pico_led.off()
                state = "OFF"
            
            data = getJSON(state)
            client.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            html = webpage(data)
            client.send(html)
            client.close()
    

try:
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except Exception as e: 
    print(f'Exception! {e}')
    machine.reset()