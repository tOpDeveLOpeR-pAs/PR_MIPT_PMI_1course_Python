import pytest
from Cipher_mashine.main import CaesarCipher


@pytest.mark.parametrize('encrypt_file, decrypt_file',
                         [('data/caesar/to_encrypt/' + file, 'data/caesar/to_decrypt/' + file)
                          for file in ['test1.txt', 'test2.txt']]
                         )
def test_caesar_encrypt(encrypt_file, decrypt_file):
    caesar = CaesarCipher('eng')

    with open(encrypt_file, mode='r', encoding='utf-8') as file:
        buff = list(file.read())
    result_buff = caesar.encrypt(buff)

    with open(encrypt_file, mode='r', encoding='utf-8') as file:
        decrypt_buff = list(file.read())

    assert result_buff == decrypt_buff


