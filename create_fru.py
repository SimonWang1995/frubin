import yaml


class Fru(object):
    def __init__(self):
        fp = open('config.yaml')
        try:
            cfg = yaml.load(fp, Loader=yaml.FullLoader)
        except:
            cfg = yaml.load(fp)
        self.internal = cfg['internal']
        self.chassis = cfg['chassis']
        self.board = cfg['board']
        self.product = cfg['product']

    def store(self, filename):
        byte_array = self.create_header()
        byte_array += self.create_bytearray(self.internal)
        byte_array += self.create_bytearray(self.chassis)
        byte_array += self.create_bytearray(self.board)
        byte_array += self.create_bytearray(self.product)
        with open(filename, 'wb') as fp:
            fp.write(byte_array)

    def create_header(self):
        header = bytearray(8)
        total_length = 1
        header[0] = 1
        header[1] = total_length
        total_length += self.internal.get('length', 0x0a)
        header[2] = total_length
        total_length += self.chassis.get('length', 0x09)
        header[3] = total_length
        total_length += self.board.get('length', 0x08)
        header[4] = total_length
        total_length += self.product.get('length', 0x24)
        header[7] = self.checksum(header)
        return header

    def create_bytearray(self, cfg):
        byte_array = bytearray(2)
        byte_array[0] = 0x01
        total_length = cfg['length'] * 8
        byte_array[1] = cfg['length']
        if cfg.get('before'):
            byte_array += self.format_before(cfg.get('before'))
        if cfg.get('field'):
            byte_array += self.format_field(cfg.get('field'))
            byte_array += bytearray([0xC1])
        space = bytearray(total_length - len(byte_array) - 1)
        byte_array += space
        byte_array += bytearray([self.checksum(byte_array)])
        return byte_array

    def checksum(self, byte_array):
        return ((~(sum(byte_array) & 0xFF)) + 1) & 0xFF

    @staticmethod
    def strtobyte(value, length):
        if isinstance(value, str):
            value = bytearray(value, encoding='utf-8')
        pad = ' ' * (length - len(value))
        return value + bytearray(pad, encoding='utf-8')

    def format_before(self, before_list):
        before_value = bytearray('', encoding='utf-8')
        for info in before_list:
            std_length = info['length']
            desc = info['desc']
            value = info['value']
            if isinstance(value, int):
                if desc == 'Mfg Date':
                    value = bytes.fromhex(str(hex(value)).strip('0x'))
                else:
                    value = bytearray([value])
            if len(value) > std_length:
                raise ValueError(desc + ':' + value + ' Length than standard ' + str(std_length))
            else:
                before_value += self.strtobyte(value, std_length)
        return before_value

    def format_field(self, field_list):
        field_bytearray = bytearray('', encoding='utf-8')
        for field in field_list:
            std_length = field['length']
            desc = field['desc']
            value = field['value']
            if isinstance(value, int):
                value = bytearray([value])
            if len(value) > std_length:
                raise ValueError(desc + ':' + value + ' Length than standard ' + str(std_length))
            else:
                fst = bytearray([0xC0 + std_length])
                field_bytearray += fst
                fmt_value = self.strtobyte(value, std_length)
                field_bytearray += fmt_value
        return field_bytearray


if __name__ == '__main__':
    fru = Fru()
    fru.store('fru.bin')