import gulp_test as gtest

@gtest.test('round trip')
@gtest.no_errors
def test_round_trip():
	from pyec.packet import Packet, Int
	import random
	import io

	class TestPacket(Packet):
		x = Int()
		y = Int()

	for _ in range(400):
		p = TestPacket(random.randrange(100000), random.randrange(100000))
		assert Packet.deserialize(io.BytesIO(p.serialize())) == p

gtest.do_tests()