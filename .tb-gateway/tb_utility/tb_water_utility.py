from logging import getLogger
from datetime import datetime
import struct

log = getLogger("service")

class MqttWaterUtil:
    default_scale = {
        "mode_operator": 1,
        "temperature": 0.01,
        "pH": 0.01,
        "oxy": 0.01,
        "salinity": 0.01,
        "canxi": 0.01,
        "magie": 0.01,
        "kali": 0.01,
        "NH3-NH4+": 0.01,
        "NO2-NO3": 0.01,
        "intensity_wave": 1,
        "clo": 0.01,
        "orp": 1,
        "ntu": 0.01,
        "pressure": 0.01,
        "voltage_battery": 0.01
    }

    default_obis = {
        "stime": 0x01,
        "mode_operator": 0x02,
        "temperature": 0x03,
        "pH": 0x04,
        "oxy": 0x05,
        "salinity": 0x06,
        "canxi": 0x07,
        "magie": 0x08,
        "kali": 0x09,
        "NH3-NH4+": 0x0A,
        "NO2-NO3": 0x0B,
        "intensity_wave": 0x0C,
        "clo": 0x0E,
        "orp": 0x0F,
        "ntu": 0x10,
        "pressure": 0x11, #12
        "voltage_battery": 0x12 #19
    }


    @staticmethod
    def stime(buffer):
        obis = MqttWaterUtil.read_int(buffer, 1)
        dataLength = MqttWaterUtil.read_int(buffer, 1)
        data = MqttWaterUtil.read_time(buffer, dataLength)
        log.debug("stime payload: obis: %s -- dataLength: %s -- data: %s", obis, dataLength, data)
        return data

    @staticmethod
    def current_index(buffer):
        obis = MqttWaterUtil.read_int(buffer, 1)
        dataLength = MqttWaterUtil.read_int(buffer, 1)
        data = MqttWaterUtil.read_int(buffer, dataLength)
        scale = MqttWaterUtil.read_int(buffer, 1)
        log.debug("current_index payload: obis: %s -- dataLength: %s -- data: %s -- scale: %s", \
        obis, dataLength, data, MqttWaterUtil.get_scale(scale))
        return round(data * MqttWaterUtil.get_scale(scale), 5)

    @staticmethod
    def voltage_battery(buffer):
        obis = MqttWaterUtil.read_int(buffer, 1)
        dataLength = MqttWaterUtil.read_int(buffer, 1)
        data = MqttWaterUtil.read_int(buffer, dataLength)
        scale = MqttWaterUtil.read_int(buffer, 1)
        log.debug("voltage_battery payload: obis: %s -- dataLength: %s -- data: %s -- scale: %s", \
        obis, dataLength, data, MqttWaterUtil.get_scale(scale))
        return round(data * MqttWaterUtil.get_scale(scale), 5)

    @staticmethod
    def freq_send_date(buffer):
        obis = MqttWaterUtil.read_int(buffer, 1)
        dataLength = MqttWaterUtil.read_int(buffer, 1)
        data = MqttWaterUtil.read_int(buffer, dataLength)
        scale = MqttWaterUtil.read_int(buffer, 1)
        log.debug("freq_send_date payload: obis: %s -- dataLength: %s -- data: %s -- scale: %s", \
        obis, dataLength, data, MqttWaterUtil.get_scale(scale))
        return data * MqttWaterUtil.get_scale(scale)

    @staticmethod
    def intensity_wave(buffer):
        obis = MqttWaterUtil.read_int(buffer, 1)
        dataLength = MqttWaterUtil.read_int(buffer, 1)
        data = MqttWaterUtil.read_int(buffer, dataLength)
        scale = MqttWaterUtil.read_int(buffer, 1)
        log.debug("intensity_wave payload: obis: %s -- dataLength: %s -- data: %s -- scale: %s", \
        obis, dataLength, data, MqttWaterUtil.get_scale(scale))
        return round(data * MqttWaterUtil.get_scale(scale), 5)
    @staticmethod
    def sim_id(buffer):
        obis = MqttWaterUtil.read_int(buffer, 1)
        dataLength = MqttWaterUtil.read_int(buffer, 1)
        data = MqttWaterUtil.read_bytearray(buffer, dataLength).hex()
        scale = MqttWaterUtil.read_int(buffer, 1)
        log.debug("intensity_wave payload: obis: %s -- dataLength: %s -- data: %s -- scale: %s", \
        obis, dataLength, data, MqttWaterUtil.get_scale(scale))
        return data
        
    @staticmethod
    def orp(value):
        return value / 10 - 1000
        
    @staticmethod
    def read_data_int_next(buffer, message_type, has_scale=False):
        obis = MqttWaterUtil.read_int(buffer, 1)
        dataLength = MqttWaterUtil.read_int(buffer, 1)
        data = MqttWaterUtil.read_int(buffer, dataLength)
        if has_scale:
            scale = MqttWaterUtil.read_int(buffer, 1)
        else:
            scale = MqttWaterUtil.default_scale.get(message_type)

        if obis != MqttWaterUtil.default_obis.get(message_type):
            log.error("Message %s dont match obis value %s", message_type, obis)
        return None

        log.debug("%s payload: obis: %s -- dataLength: %s -- data: %s -- scale: %s", message_type, obis, dataLength, data, scale)
        return round(data * scale, 5)

    @staticmethod
    def crc(buffer):
        crc = MqttWaterUtil.read_int(buffer, 1)
        log.debug("crc payload: crc: %s ", crc) 
        return crc

    @staticmethod
    def read_id(buffer, length, order='big', signed=False):
        return str(MqttWaterUtil.read_bytearray(buffer, length, order), "UTF-8")

    @staticmethod
    def read_int(buffer, length, order='big', signed=False):
        return int.from_bytes(MqttWaterUtil.read_bytearray(buffer, length, order), byteorder='big', signed=signed)

    @staticmethod
    def read_bytearray(buffer, length, order='big'):
        value = bytearray()
        for _ in range(length):  # reading every value with value length from config
            value.append(buffer.pop(0))  # process and remove byte from processing
        if order == 'little':
            value.reverse()
        return value
        
    @staticmethod
    def read_float(buffer, length):
        value = MqttWaterUtil.read_bytearray(buffer, length)
        return struct.unpack('>f', value)[0]

    @staticmethod
    def read_string(buffer, length, order='big', zpad=True):
        value = []
        for _ in range(length):
            value.append(format(buffer.pop(0), 'x') if zpad == False else format(buffer.pop(0), 'x').zfill(2))
        return "".join(value) if order == 'big' else "".join(value[::-1])

    @staticmethod
    def read_int_array(buffer, length, order='big', length_int=4):
        if length % length_int != 0:
            log.error("length_int must multiples length buffer: length: %s, length_int: %s", length, length_int)
            return []
        value = []
        for _ in range(int(length / length_int)):
            value.append(MqttWaterUtil.read_int(buffer, length_int))
        return value

    @staticmethod
    def read_time(buffer, length, date_format = "%y-%m-%d %H:%M:%S", order='big'):
        data = MqttWaterUtil.read_bytearray(buffer, length, order)
        if length == 6:
            dd = str(data.pop(0))
            MM = str(data.pop(0))
            yy = str(data.pop(0))
            HH = str(data.pop(0))
            mm = str(data.pop(0))
            ss = str(data.pop(0))
            date_str = yy + "-" + MM + "-" + dd + " " + HH + ":" + mm + ":" + ss
            date = datetime.strptime(date_str, date_format)
            return date.timestamp() * 1000
        else:
            log.error("Data incorrect with length %s. Ignore buffer '%s'", length, data)
        return None
        
    @staticmethod
    def read_time_string(buffer, length, date_format = "%y-%m-%d %H:%M:%S", order='big'):
        try:
            data = MqttWaterUtil.read_bytearray(buffer, length, order)
            if length == 6:
                dd = str(MqttWaterUtil.read_int(data, 1))
                MM = str(MqttWaterUtil.read_int(data, 1))
                yy = str(MqttWaterUtil.read_int(data, 1))
                HH = str(MqttWaterUtil.read_int(data, 1))
                mm = str(MqttWaterUtil.read_int(data, 1))
                ss = str(MqttWaterUtil.read_int(data, 1))
                date_str = yy + "-" + MM + "-" + dd + " " + HH + ":" + mm + ":" + ss
                return datetime.strptime(date_str, "%y-%m-%d %H:%M:%S").strftime(date_format)
            elif length == 5:
                yy = str(MqttWaterUtil.read_int(data, 1))
                MM = str(MqttWaterUtil.read_int(data, 1))
                dd = str(MqttWaterUtil.read_int(data, 1))
                HH = str(MqttWaterUtil.read_int(data, 1))
                mm = str(MqttWaterUtil.read_int(data, 1))
                date_str = yy + "-" + MM + "-" + dd + " " + HH + ":" + mm
                return datetime.strptime(date_str, "%y-%m-%d %H:%M").strftime(date_format)
            else:
                log.error("Data incorrect with length %s. Ignore buffer '%s'", length, data)
        except Exception as e:
            log.exception(e)
            return "Error parse time."
        return ""

    @staticmethod
    def get_scale(scale):
        # 0x00 -> 1
        # 0xFF->  0.1
        # 0xFE -> 0.01
        # 0xFD -> 0.001
        # 0xFC -> 0.0001
        # 0xFB -> 0.00001
        if scale == 0x00:
            return 1
        elif scale == 0xFF:
            return 0.1
        elif scale == 0xFE:
            return 0.01
        elif scale == 0xFD:
            return 0.001
        elif scale == 0xFC:
            return 0.0001
        elif scale == 0xFB:
            return 0.00001
        else:
            log.error("scale value '%s' is not valid", scale)
            return -1

    @staticmethod
    def validate_crc(buffer):
        crc = buffer.pop(len(buffer) - 1)
        log.debug("crc checking crc_message[%s] ---- crc calculate[%s]", crc, MqttWaterUtil.get_crc(buffer))
        return MqttWaterUtil.get_crc(buffer) == crc
        # return True

    @staticmethod
    def get_crc(buffer): 
        xor = 0
        for x in buffer:
            xor ^= x
        return xor

    @staticmethod
    def int_to_bytes(value, length, order='big'): 
        return (value).to_bytes(length, byteorder=order)

    @staticmethod
    def float_to_bytes(value, length, order='big'): 
        byteorder = '>f' if order == 'big' else '<f'
        return struct.pack(byteorder, value)
        
    @staticmethod
    def isoformat_to_ms(value): 
        return int(datetime.fromisoformat(value).timestamp() * 1000)