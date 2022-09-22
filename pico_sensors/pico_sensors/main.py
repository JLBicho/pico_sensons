from tkinter import dialog
import rclpy
from rclpy.node import Node 
from diagnostic_msgs.msg import DiagnosticStatus, KeyValue
import requests

class PicoSensors(Node):
    def __init__(self):
        super().__init__('pico_sensors')
    
        self.timer = self.create_timer(5, self.timerCallback)

        self.diag_msg = DiagnosticStatus()
        self.diag_msg.hardware_id = "PICOW"
        self.diag_msg.level = b'0'
        self.diag_msg.name = "Sensores"
        self.diag_msg.message = "Valores de sensores"

        self.sensors_pub = self.create_publisher(DiagnosticStatus, "/pico_sensors", 10)
        self.sensors_pub

    def timerCallback(self):
        self.diag_msg.values.clear()
        try:
            response = requests.get("http://192.168.1.135/json?", timeout=2.0)
            
            try:
                data = response.json()
                for k,v in data.items():
                    key_val = KeyValue()
                    key_val.key = str(k)
                    key_val.value = str(v)
                    self.diag_msg.values.append(key_val)  
            except Exception as e:
                self.diag_msg.message = f"{e}"
                self.diag_msg.level = b'2'

        except:
            self.diag_msg.message = "No response"
            self.diag_msg.level = b'2'
        
        self.sensors_pub.publish(self.diag_msg)

        



def main(args=None):
  
  rclpy.init(args=args)  

  pico_sensors = PicoSensors()

  rclpy.spin(pico_sensors)
 
  pico_sensors.destroy_node()
  
  rclpy.shutdown()
  
if __name__ == '__main__':
  main()
