import gulp_test as gtest

@gtest.test('pack')
@gtest.no_errors
def test_pack():
	from pyec.packet.varint import pack

	assert pack(5030) == b'NM'
	assert   pack(32) == b'A'
	assert  pack(512) == b'\x08\x01'
	assert pack(5123) == b'P\x07'

@gtest.test('unpack')
@gtest.no_errors
def test_unpack():
	from pyec.packet.varint import unpack_bytes

	assert unpack_bytes(b'NM') == (5030, b'')
	assert  unpack_bytes(b'A') == (32, b'')

	assert unpack_bytes(b'NM\x01') == (5030, b'\x01')
	assert  unpack_bytes(b'A\x08') == (32, b'\x08')

@gtest.test('round trip')
@gtest.no_errors
def test_round_trip():
	from pyec.packet.varint import pack, unpack_bytes
	import random

	for _ in range(20):
		x = random.randrange(100000)
		assert unpack_bytes(pack(x))[0] == x

gtest.do_tests()
