#     Copyright 2022. ThingsBoard
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from simplejson import dumps

from thingsboard_gateway.connectors.mqtt.mqtt_uplink_converter import MqttUplinkConverter, log
from thingsboard_gateway.tb_utility.tb_water_utility import MqttWaterUtil


LIVE_DATA_LEN = 45
LIVE_DATA = 76
WARNING = 87

class CustomMqttWaterDgsOperaConverter(MqttUplinkConverter):
    def __init__(self, config):
        self.__config = config.get('converter')
        self.dict_result = {}

    def convert(self, topic, body):
        log.debug("convert: topic: %s, body: %s, config: %s", topic, body, self.__config)
        try:
            self.dict_result["deviceName"] = (self.__config['prefixDeviceName'] if self.__config['prefixDeviceName'] is not None else "DEFAULT")
            self.dict_result["deviceType"] = self.__config['deviceType'] if self.__config['deviceType'] is not None else "default"
            self.dict_result["telemetry"] = []

            # bytes_to_read = body.replace("0x", "")  # Replacing the 0x (if '0x' in body), needs for converting to bytearray
            converted_bytes = bytearray(body, "utf8")  # Converting incoming data to bytearray

            if MqttWaterUtil.validate_crc(converted_bytes):
                length = MqttWaterUtil.read_int(converted_bytes, 1)
                deviceID = MqttWaterUtil.read_id(converted_bytes, 12).rstrip('\x00')
                packetType = MqttWaterUtil.read_int(converted_bytes, 1)
                self.dict_result["deviceName"] += deviceID
                if(length == LIVE_DATA_LEN):
                    if(packetType == LIVE_DATA):
                        typeName = "LiveData."
                    elif(packetType == WARNING):
                        typeName = "Warning."
                    # log.exception("Type cua ID: %s\n", type(self.dict_result["deviceName"]))
                    self.dict_result["telemetry"].append({typeName + "length": length})
                    self.dict_result["telemetry"].append({typeName + "deviceID": deviceID})
                    self.dict_result["telemetry"].append({typeName + "type": packetType})
                    self.dict_result["telemetry"].append({typeName + "signal_Strength": MqttWaterUtil.read_int(converted_bytes, 1)})
                    self.dict_result["telemetry"].append({typeName + "device_Type": MqttWaterUtil.read_int(converted_bytes, 1)})
                    self.dict_result["telemetry"].append({typeName + "state": MqttWaterUtil.read_int(converted_bytes, 1)})
                    self.dict_result["telemetry"].append({typeName + "battery": MqttWaterUtil.read_int(converted_bytes, 1)})
                    self.dict_result["telemetry"].append({typeName + "remain_use_time": MqttWaterUtil.read_int(converted_bytes, 1)})
                    self.dict_result["telemetry"].append({typeName + "interval": MqttWaterUtil.read_int(converted_bytes, 2)})
                    self.dict_result["telemetry"].append({typeName + "consumed_water": MqttWaterUtil.read_int(converted_bytes, 4)})
                    self.dict_result["telemetry"].append({typeName + "decimal_digits": MqttWaterUtil.read_int(converted_bytes, 1)})
                    self.dict_result["telemetry"].append({typeName + "latitude": MqttWaterUtil.read_float(converted_bytes, 4)})
                    self.dict_result["telemetry"].append({typeName + "lontitude": MqttWaterUtil.read_float(converted_bytes, 4)})
                    self.dict_result["telemetry"].append({typeName + "altitude": MqttWaterUtil.read_float(converted_bytes, 4)})
                    self.dict_result["telemetry"].append({typeName + "time": MqttWaterUtil.read_time_string(converted_bytes, 6)})
                else:
                    typeName = "SurveyData."
                    self.dict_result["telemetry"].append({typeName + "length": length})
                    self.dict_result["telemetry"].append({typeName + "deviceID": deviceID})
                    self.dict_result["telemetry"].append({typeName + "type": packetType})
                    self.dict_result["telemetry"].append({typeName + "interval": MqttWaterUtil.read_int(converted_bytes, 2)})
                    self.dict_result["telemetry"].append({typeName + "time": MqttWaterUtil.read_time_string(converted_bytes, 5)})
                    self.dict_result["telemetry"].append({typeName + "decimal_digits": MqttWaterUtil.read_int(converted_bytes, 1)})
                    arr_data_set = MqttWaterUtil.read_int_array(converted_bytes, len(converted_bytes))
                    for i in range(len(arr_data_set)):
                        self.dict_result["telemetry"].append({typeName+"data_set."+i: arr_data_set[i]})
            else:
                self.dict_result["telemetry"] = {"data": int(body,0)}

            return self.dict_result

        except Exception as e:
            log.exception('Error in converter, for config: \n%s\n and message: \n%s\n', dumps(self.__config), body)
            log.exception(e)

class CustomMqttUpUplinkConverter(MqttUplinkConverter):
    def __init__(self, config):
        self.__config = config.get('converter')
        self.dict_result = {}

    def convert(self, topic, body):
        try:
            self.dict_result["deviceName"] = "Custem_Device"  # getting all data after last '/' symbol in this case: if topic = 'devices/temperature/sensor1'>
            self.dict_result["deviceType"] = "default"  # just hardcode this
            self.dict_result["telemetry"] = []  # template for telemetry array
            #bytes_to_read = body.replace("0x", "")  # Replacing the 0x (if '0x' in body), needs for converting to bytearray
            converted_bytes = bytearray(body, "utf8")  # Converting incoming data to bytearray
            if self.__config.get("extension-config") is not None:
                for telemetry_key in self.__config["extension-config"]:  # Processing every telemetry key in config for extension
                    value = 0
                    for _ in range(self.__config["extension-config"][telemetry_key]):  # reading every value with value length from config
                        value = value * 256 + converted_bytes.pop(0)  # process and remove byte from processing
                    telemetry_to_send = {telemetry_key.replace("Bytes", ""): value}  # creating telemetry data for sending into Thingsboard
                    self.dict_result["telemetry"].append(telemetry_to_send)  # adding data to telemetry array
            else:
                self.dict_result["telemetry"] = {"data": int(body, 0)}  # if no specific configuration in config file - just send data which received
            return self.dict_result

        except Exception as e:
            log.exception('Error in converter, for config: \n%s\n and message: \n%s\n', dumps(self.__config), body)
            log.exception(e)
