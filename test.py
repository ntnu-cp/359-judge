from judge import cmp_n_bit


def test_cmp_n_bit_1_byte():
    assert cmp_n_bit(0b00001111.to_bytes(1, 'big'),0b00001111.to_bytes(1, 'big'), 8 )
    assert cmp_n_bit(0b00001111.to_bytes(1, 'big'),0b00001110.to_bytes(1, 'big'), 6 )
    assert cmp_n_bit(0b01001011.to_bytes(1, 'big'),0b01111111.to_bytes(1, 'big'), 1 )

def test_cmp_n_bit_more_bytes():
    assert not cmp_n_bit(0xffff.to_bytes(2, 'big'), 0xffff.to_bytes(2, 'big'), 24)
    assert not cmp_n_bit(0xffff.to_bytes(2, 'big'), 0x7fff.to_bytes(2, 'big'), 2)
    assert cmp_n_bit(0xffff.to_bytes(2, 'big'), 0xffcf.to_bytes(2, 'big'), 10)
    assert not cmp_n_bit(0xffff.to_bytes(2, 'big'), 0xffcf.to_bytes(2, 'big'), 11)
