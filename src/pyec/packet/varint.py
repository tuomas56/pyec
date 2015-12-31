"""
(c) Tuomas Laakkonen 2015

pyec.packet.varint
Simple binary variable-length integers.
Uses a 7bit + continuation bit encoding:

data    data    data
<-----> <-----> <----->
010010100100110001110101
       ^       ^       ^
 cn. bit cn. bit cn. bit
   unset   unset     set

The varint terminates when the continuation is *set*.
"""

def pack(n:int) -> bytes:
	"""Take an integer and encode it to a byte string."""
	if n == 0:
		return bytes([1])
	result = []
	while n > 0:
		byte = (n >> 7 << 7) ^ n
		#take 7 least sig. bytes
		n >>= 7
		result.append(byte << 1) 
		#move the bits up one more for the _empty_ continuation bit
	result[0] += 1 #the last continuation bit is set
	#but its backwards so flip
	return b''.join(map(lambda x: bytes([x]), result[::-1]))

def unpack_bytes(n:bytes) -> (int, bytes):
	"""Take a bytestring and decode it into an integer, returning the remaining bytes - if any.
   	If the bytestring ends without setting a continuation bit, an error will be thrown."""
	result = 0
	n = n.decode()
	while len(n) > 0:
		byte, n = ord(n[0]), n[1:]
		cont, byte = byte & 1, byte >> 1
		#continuation bit is lsb, and then get rid of it.
		result <<= 7
		result += byte
		if cont:
			break
	else:
		raise ValueError('Varint passed to unpack did not terminate!')
	return result, n.encode()

def unpack_stream(n:bytes) -> (int, bytes):
	"""Take a byte stream and decode it into an integer, returning the stream.
   	If the byte stream closes without setting a continuation bit, an error will be thrown."""
	result = 0
	while not n.closed:
		byte = ord(n.read(1))
		cont, byte = byte & 1, byte >> 1
		result <<= 7
		result += byte
		if cont:
			break
	else:
		raise ValueError('Varint passed to unpack did not terminate!')
	return result, n

__all__ = ['pack', 'unpack_bytes', 'unpack_stream']
