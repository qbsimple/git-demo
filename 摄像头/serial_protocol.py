import struct  # 导入struct模块，用于处理二进制数据

class SerialProtocol:
    HEAD = 0xAA  # 定义帧头，固定为0xAA
    TAIL = 0x55  # 定义帧尾，固定为0x55

    def __init__(self) -> None:
        pass  # 初始化方法，暂时没有需要初始化的内容

    def _checksum(self, data: bytes) -> int:
        """
        计算和校验
        """
        check_sum = 0  # 初始化校验和为0
        for a in data:
            check_sum = (check_sum + a) & 0xFF  # 累加每个字节，并取低8位
        return check_sum  # 返回计算得到的校验和

    def is_valid(self, raw_data: bytes) -> tuple:
        """
        判断数据是否有效
        """
        bytes_redundant = 0  # 冗余字节数，表示数据包前面有多少无效字节
        index = 0  # 用于遍历数据的索引

        # 查找帧头的位置
        for a in raw_data:
            if a != SerialProtocol.HEAD:  # 如果当前字节不是帧头
                index += 1  # 索引加1，继续查找
            else:
                break  # 找到帧头，跳出循环

        bytes_redundant = index  # 记录冗余字节数

        # 如果剩余数据长度小于3字节（长度字段至少2字节 + 1字节校验和），如果剩余数据长度小于 3 字节，说明数据帧不完整
        if len(raw_data[index:]) < 3:
            return (-1, bytes_redundant)  # 返回错误码-1和冗余字节数

        # 解析数据包中的长度字段（2字节，小端序）
        payload_len = struct.unpack('<H', raw_data[index+1:index+3])[0]

        # 如果剩余数据长度小于完整数据包的长度（帧头1字节 + 长度2字节 + 负载 + 校验和1字节 + 帧尾1字节），数据无效
        if len(raw_data) - bytes_redundant < payload_len + 5:
            return (-2, bytes_redundant)  # 返回错误码-2和冗余字节数

        # 检查帧尾和校验和是否匹配
        if raw_data[index+3+payload_len+1] != SerialProtocol.TAIL or self._checksum(raw_data[index+1:index+3+payload_len]) != raw_data[index+3+payload_len]:
            return (-3, bytes_redundant)  # 返回错误码-3和冗余字节数
        else:
            return (0, bytes_redundant)  # 数据有效，返回0和冗余字节数

    def length(self, raw_data: bytes) -> int:
        """
        取得有效数据包的整体长度
        """
        # 如果数据长度小于5字节（帧头1字节 + 长度2字节 + 校验和1字节 + 帧尾1字节），或者帧头帧尾不匹配，返回-1
        if len(raw_data) < 5 or raw_data[0] != SerialProtocol.HEAD or raw_data[-1] != SerialProtocol.TAIL:
            return -1

        # 解析数据包中的长度字段（2字节，小端序）
        payload_len = struct.unpack('<H', raw_data[1:3])[0]
        return 3 + payload_len + 2  # 返回完整数据包长度（帧头1字节 + 长度2字节 + 负载 + 校验和1字节 + 帧尾1字节）

    def encode(self, payload: bytes) -> bytes:
        """
        编码数据负载部分，添加帧头帧尾校验等部分
        """
        frame = bytearray()  # 创建一个字节数组用于构建数据帧
        frame.append(SerialProtocol.HEAD)  # 添加帧头
        frame.extend(struct.pack('<H', len(payload)))  # 添加负载长度（2字节，小端序）
        frame.extend(payload)  # 添加负载数据
        frame.append(self._checksum(frame[1:]))  # 添加校验和（计算从长度字段到负载的校验和）
        frame.append(SerialProtocol.TAIL)  # 添加帧尾

        return bytes(frame)  # 返回构建好的数据帧

    def decode(self, raw_data: bytes) -> bytes:
        """
        解码出数据负载部分
        """
        # 如果数据长度小于5字节，或者帧头帧尾不匹配，返回空字节
        if len(raw_data) < 5 or raw_data[0] != SerialProtocol.HEAD or raw_data[-1] != SerialProtocol.TAIL:
            return bytes()

        # 解析数据包中的长度字段（2字节，小端序）
        payload_len = struct.unpack('<H', raw_data[1:3])[0]
        return raw_data[3:3+payload_len]  # 返回负载数据部分

if __name__ == '__main__':
    payload = 'hello'  # 定义负载数据
    proto = SerialProtocol()  # 创建SerialProtocol对象
    encoded = proto.encode(payload.encode())  # 编码负载数据
    print(encoded.hex())  # 打印编码后的数据（十六进制格式）
    encoded = bytes([0x01, 0x02]) + encoded  # 在编码数据前添加两个无效字节
    valid = proto.is_valid(encoded)  # 检查数据是否有效
    print(valid)  # 打印检查结果
    decoded = encoded[valid[1]:]  # 去除冗余字节，获取有效数据
    decoded = proto.decode(decoded)  # 解码数据
    print(decoded.decode())  # 打印解码后的负载数据
