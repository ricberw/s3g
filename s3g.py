# Some utilities for speaking s3g
import struct

class PacketError(Exception):
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return repr(self.value)

class PacketLengthError(PacketError):
  def __init__(self, length, expected_length):
    self.value='Invalid length. Got=%i, Expected=%i'%(length, expected_length)

class PacketLengthFieldError(PacketError):
  def __init__(self, length, expected_length):
    self.value='Invalid length field. Got=%i, Expected=%i'%(length, expected_length)

class PacketHeaderError(PacketError):
  def __init__(self, header, expected_header):
    self.value='Invalid header. Got=%x, Expected=%x'%(ord(header), ord(expected_header))

class PacketCRCError(PacketError):
  def __init__(self, crc, expected_crc):
    self.value='Invalid crc. Got=%x, Expected=%x'%(ord(crc), ord(expected_crc))

def CalculateCRC(data):
  """
  Calculate the iButton/Maxim crc for a give bytearray
  @param data bytearray of data to calculate a CRC for
  @return Single byte CRC calculated from the data.
  """
  # CRC table from http://forum.sparkfun.com/viewtopic.php?p=51145
  crctab = [
    0, 94, 188, 226, 97, 63, 221, 131, 194, 156, 126, 32, 163, 253, 31, 65,
    157, 195, 33, 127, 252, 162, 64, 30, 95, 1, 227, 189, 62, 96, 130, 220,
    35, 125, 159, 193, 66, 28, 254, 160, 225, 191, 93, 3, 128, 222, 60, 98,
    190, 224, 2, 92, 223, 129, 99, 61, 124, 34, 192, 158, 29, 67, 161, 255,
    70, 24, 250, 164, 39, 121, 155, 197, 132, 218, 56, 102, 229, 187, 89, 7,
    219, 133, 103, 57, 186, 228, 6, 88, 25, 71, 165, 251, 120, 38, 196, 154,
    101, 59, 217, 135, 4, 90, 184, 230, 167, 249, 27, 69, 198, 152, 122, 36,
    248, 166, 68, 26, 153, 199, 37, 123, 58, 100, 134, 216, 91, 5, 231, 185,
    140, 210, 48, 110, 237, 179, 81, 15, 78, 16, 242, 172, 47, 113, 147, 205,
    17, 79, 173, 243, 112, 46, 204, 146, 211, 141, 111, 49, 178, 236, 14, 80,
    175, 241, 19, 77, 206, 144, 114, 44, 109, 51, 209, 143, 12, 82, 176, 238,
    50, 108, 142, 208, 83, 13, 239, 177, 240, 174, 76, 18, 145, 207, 45, 115,
    202, 148, 118, 40, 171, 245, 23, 73, 8, 86, 180, 234, 105, 55, 213, 139,
    87, 9, 235, 181, 54, 104, 138, 212, 149, 203, 41, 119, 244, 170, 72, 22,
    233, 183, 85, 11, 136, 214, 52, 106, 43, 117, 151, 201, 74, 20, 246, 168,
    116, 42, 200, 150, 21, 75, 169, 247, 182, 232, 10, 84, 215, 137, 107, 53
  ]

  data_bytes = bytearray(data)

  val = 0
  for x in data_bytes:
     val = crctab[val ^ x]
  return val


def EncodeInt32(number):
  """
  Interpret number as a 32-bit integer, and 
  @param number 
  @return byte array of size 4 that represents the integer
  """
  return struct.pack('<i', number)

def EncodeUint32(number):
  """
  Interpret number as a 32-bit integer, and 
  @param number 
  @return byte array of size 4 that represents the integer
  """
  return struct.pack('<I', number)

def EncodePacket(payload):
  """
  Encode a packet that contains the given payload
  @param payload Command payload, 1 - n bytes describing the command to send
  @return bytearray containing the packet
  """
  packet = bytearray()
  packet.append(0xD5)
  packet.append(len(payload))
  packet += payload
  packet.append(CalculateCRC(payload))

  return packet

def DecodePacket(packet):
  """
  Read in a packet, extract the payload, and verify that the CRC of the
  packet is correct. Raises a PacketError exception if there was an error
  decoding the packet
  @param packet byte array containing the input packet
  @return payload of the packet
  """
  if len(packet) < 4:
    raise PacketLengthError(len(packet), 4)

  if packet[0] != 0xD5:
    raise PacketHeaderError(packet[0], 0xD5)

  if packet[1] != len(packet) - 3:
    raise PacketLengthFieldError(packet[1], len(packet) - 3)

  if packet[len(packet)-1] != CalculateCRC(packet[2:(len(packet)-1)]):
    raise PacketCRCError(packet[len(packet)-1], CalculateCRC(packet[2:(len(packet)-1)]))

  return packet[2:(len(packet)-1)]


command_map = {
  'QUEUE_EXTENDED_POINT'    : 139,
  }

class Replicator:
  stream = None

  def Move(self, position, rate):
    """
    Move the toolhead to a new position at the given rate
    @param position array 5D position to move to. All dimension should be in mm.
    @param rate double Movement speed, in mm/minute
    """
    payload = bytearray()
    payload.append(command_map['QUEUE_EXTENDED_POINT'])
    payload += EncodeInt32(position[0])
    payload += EncodeInt32(position[1])
    payload += EncodeInt32(position[2])
    payload += EncodeInt32(position[3])
    payload += EncodeInt32(position[4])
    payload += EncodeUint32(rate)
    
    packet = EncodePacket(payload)
    self.stream.write(packet)
