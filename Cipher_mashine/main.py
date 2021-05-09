from abc import abstractmethod
from argparse import ArgumentParser
from collections import Counter
from os.path import exists
from random import randint, choice
from string import ascii_lowercase as a_lc

# Cipher classes
class AbstractCipher:

    @abstractmethod
    def encrypt(self, file_data: str, fl: int = None) -> list:
        pass

    @abstractmethod
    def decrypt(self, file_data: str) -> list:
        pass

    @abstractmethod
    def write_key(self) -> None:
        pass

    def load_key(self) -> str:
        if not exists("crypto_key.txt"):
            self.write_key()

        with open("crypto_key.txt", "r", encoding="utf-8") as kf:
            return (kf.read())[2:]
    
    def find_index(self, c: str) -> int:
       if not c.isalpha(): return -1
       elif c == 'ё': return 6
       elif c not in ['а', 'б', 'в', 'г', 'д', 'е']:
           return ord(c) - ord(self.letters[0]) + 1
       return ord(c) - ord(self.letters[0])


class CaesarCipher(AbstractCipher):
    mod_num: int
    letters: str
    ecr_letters: list

    def __init__(self, lang: str = None, way: str = None):
        self.mod_num = 26 if lang == "eng" else 33
        self.letters = a_lc if lang == "eng" else "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

        if lang == "eng":
            self.ecr_letters = ['e', 't', 'a', 'o', 'i', 'n', 's',
                           'h', 'r', 'd', 'l', 'c', 'u', 'm',
                           'w', 'f', 'g', 'y', 'p', 'b', 'v', 
                           'k', 'x', 'j', 'q', 'z']
        else:
            self.ecr_letters = ['о', 'а', 'е', 'и', 'т', 'н', 'л',
                           'р', 'с', 'в', 'к', 'м', 'д', 'у', 'п',
                           'б', 'г', 'ы', 'ч', 'ь', 'з', 'я', 'й',
                           'х', 'ж', 'ш', 'ю', 'ф', 'э', 'щ',
                           'ё', 'ц', 'ъ']

    def encrypt(self, file_data: list, fl: int = 1) -> list: 
        key = int(self.load_key())   

        for i in range(len(file_data)):
            index = self.find_index(file_data[i].lower())
            if index != -1:
                is_upp = file_data[i].isupper() 
                file_data[i] = self.letters[(index + key * fl) % self.mod_num]
                if is_upp: file_data[i] = file_data[i].upper()
                
        return file_data

    def decrypt(self, file_data) -> list:
        return self.encrypt(file_data, -1)

    def hacking(self, bfile_data) -> None:
        dcr_letters_counts = Counter([x.lower() for x in bfile_data 
                                      if x in self.ecr_letters])
        del dcr_letters_counts[" "]
        dcr_letters = [x[0] for x in dcr_letters_counts.most_common()]
        dict_jn = dict(zip(dcr_letters, self.ecr_letters))

        for i in range(len(bfile_data)):
            if bfile_data[i].isalpha():
                is_upp = bfile_data[i].isupper() 
                bfile_data[i] = str(dict_jn.get(bfile_data[i].lower()))
                if is_upp: bfile_data[i] = (bfile_data[i]).upper()
    
        return bfile_data

    def write_key(self) -> None:
        if exists("crypto_key.txt"):
            with open("crypto_key.txt", "r") as kfile:
                if (kfile.read())[:2] == '1 ': return
        
        key = randint(0, self.mod_num)
        with open("crypto_key.txt", "w", encoding="utf-8") as kfile:
            kfile.write("1 " + str(key))

class VigenereCipher(AbstractCipher):
    mod_num: int
    letters: str
    lang: str

    def __init__(self, lang: str = None, way: str = None):
        self.mod_num = 26 if lang == "eng" else 33
        self.letters = a_lc if lang == "eng" else "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        self.lang = lang

    def encrypt(self, file_data: str, fl: int = 1) -> list: 
        key = self.load_key()   

        k_indecis = [self.find_index(letter) for letter in key]
        k_pos = 0
        for i in range(len(file_data)):
            index = self.find_index(file_data[i].lower())
            index_k = k_indecis[k_pos]
            if index != -1:
                is_upp = file_data[i].isupper() 
                file_data[i] = self.letters[(index + index_k * fl) % self.mod_num]
                if is_upp: file_data[i] = (file_data[i]).upper()
                k_pos = (k_pos + 1) % len(key)
        
        return file_data

    def decrypt(self, file_data) -> list:
        return self.encrypt(file_data, -1)

    def write_key(self) -> None:
        if exists("crypto_key.txt"):
            with open("crypto_key.txt", "r") as kfile:
                if (kfile.read())[:2] == '2 ': return

        key = ""
        for i in range(randint(10, 20)):
            key += choice(self.letters)
        with open("crypto_key.txt", "w", encoding="utf-8") as kfile:
            kfile.write("2 " + key)

class VernamCipher(AbstractCipher):
    mod_num: int
    letters: str
    way: str

    def __init__(self, lang: str = None, way: str = None):
        self.mod_num = 26 if lang == "eng" else 33
        self.letters = a_lc if lang == "eng" else "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        self.way = way

    def encrypt(self, file_data: str) -> list: 
        key = ((self.load_key()).split(" "))
        
        for i in range(len(file_data)):
            index = self.find_index(file_data[i].lower())
            if index != -1:
                is_upp = file_data[i].isupper()
                index = int(format(int(key[i]), 'b'), 2) ^ int(str.zfill(format(index, 'b'), 7), 2)
                file_data[i] = self.letters[index]
                if is_upp: file_data[i] = file_data[i].upper()      
                
        return file_data

    def decrypt(self, file_data) -> list:
        return self.encrypt(file_data)

    def write_key(self) -> None:
        if exists("crypto_key.txt"):
            with open("crypto_key.txt", "r") as kfile:
                if (kfile.read())[:2] == '3 ': return
 
        with open(self.way, "r", encoding="utf-8") as rfile:
            rsize = len(rfile.read())

        key = " ".join([str(randint(0, self.mod_num)) for i in range(rsize)])
        with open("crypto_key.txt", "w") as kfile:
            kfile.write("3 " + key)

# -------------- Function for reading / writing with utf-8 ---------------

def read_utf8(way: str) -> list:
    with open(way, "r", encoding="utf-8") as file:
        file_data = list(file.read())
    return file_data

def write_utf8(way: str, rbuff: list) -> None:
    with open(way, "w", encoding="utf-8") as rfile:
        rfile.write(''.join(rbuff))

# --------------------------------------------------------------------

def main():    
    # Parsing command line's arguments
    parser = ArgumentParser(description="Encryption program parser")

    # Positional arguments
    parser.add_argument(
        "way",
        type=str,
        help="The path to the file\n"
    )
    parser.add_argument(
        "mode",
        type=str, 
        default="caesar",
        choices=["caesar", "vigenere", "vernam"],
        help=" Choice of encryption decripthon method: 1 - Caesar chiper," +
                "2 - Vigenère chiper, 3 - Vernam chiper"
    )
    parser.add_argument(
        "lang",
        type=str,
        default="eng",
        choices=["eng", "rus"],
        help=" Language of text: eng - english, rus - russian"
    )

    # Optional argument
    parser.add_argument(
        "-a",
        "--action", 
        type=str, 
        default="encrypt", 
        choices=["encrypt", "decrypt", "hacking"],
        help=" Choice of program operation mode: encryption," +
                "decryption, breaking the Caesar cipher"
    )

    args = parser.parse_args()

    # Creating object of specific cipher's class \ creating key
    cipher: AbstractCipher

    if args.mode == 'caesar':
        cipher = CaesarCipher(args.lang)
    elif args.mode == 'vigenere':
        cipher = VigenereCipher(args.lang)
    else:
        cipher = VernamCipher(args.lang, args.way)
    cipher.write_key()

    # Choice of actions with object
    buff = read_utf8(args.way) if args.action != 'decrypt' else read_utf8("result.txt")

    if args.action == 'encrypt':   
        rbuff = cipher.encrypt(buff)
        write_utf8("result.txt", rbuff)
    elif args.action == 'decrypt':
        rbuff = cipher.decrypt(buff)
        write_utf8("decrypt.txt", rbuff)
    else:
        if args.mode != 'caesar':
            raise TypeError("Impossible action with caesar's " +
                            "breaking algorithm for another cipher")
        else:
            rbuff = cipher.hacking(buff)
            write_utf8("hacking.txt", rbuff)
    

if __name__ == "__main__":
    main()
