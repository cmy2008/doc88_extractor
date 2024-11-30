class Viewer:
    key1=["P", "J", "L", "K", "M", "N", "O", "I", "3", "x", "y", "z", "0", "2", "1", "w", "v", "r", "p", "q", "s", "t", "o", "u", "H", "C", "F", "B", "D", "E", "G", "A", "n", "h", "i", "k", "j", "l", "m", "g", "f", "Z", "b", "a", "c", "e", "d", "Y", "R", "X", "T", "S", "U", "V", "Q", "W", "!", "5", "6", "7", "8", "9", "+", "4"]
    key2=["P","J","K","L","M","N","O","I","3","x","y","z","0","1","2","w","v","p","r","q","s","t","u","o","H","B","C","D","E","F","G","A","n","h","i","j","k","l","m","g","f","Z","a","b","c","d","e","Y","X","R","S","T","U","V","W","Q","!","5","6","7","8","9","+","4"]   
    def __init__(self):
        self._WW = None
        self._2x = 0
        self._kh_OF_INPUT = -1
    
    def _t8(self, str):
        self._WW = str
        self._2x = 0

    def _06(self, n):
        return chr(n)

    def _9O(self, str):
        out = ""
        i = 0
        while i < len(str):
            c = ord(str[i])
            i += 1
            if c >> 4 in range(0, 8):
                out += chr(c)
            elif c >> 4 in range(12, 14):
                char2 = ord(str[i])
                i += 1
                out += chr(((c & 31) << 6) | (char2 & 63))
            elif c >> 4 == 14:
                char2 = ord(str[i])
                i += 1
                char3 = ord(str[i])
                i += 1
                out += chr(((c & 15) << 12) | ((char2 & 63) << 6) | (char3 & 63))
        return out

    def _w7(self):
        if not self._WW:
            return self._kh_OF_INPUT
        while True:
            if self._2x >= len(self._WW):
                return self._kh_OF_INPUT
            next_character = self._WW[self._2x]
            self._2x += 1
            if next_character in self._fE:
                return self._fE[next_character]
            if next_character == "P":
                return 0
        return self._kh_OF_INPUT

    def _8W(self, str, key):
        Viewer._Jv_r = key
        self._fE = {char: idx for idx, char in enumerate(Viewer._Jv_r)}
        self._t8(str)
        result = ""
        in_buffer = [0] * 4
        done = False
        while not done:
            in_buffer[0] = self._w7()
            in_buffer[1] = self._w7()
            if in_buffer[0] == self._kh_OF_INPUT or in_buffer[1] == self._kh_OF_INPUT:
                break
            in_buffer[2] = self._w7()
            in_buffer[3] = self._w7()
            result += self._06(((in_buffer[0] << 2) & 255) | (in_buffer[1] >> 4))
            if in_buffer[2] != self._kh_OF_INPUT:
                result += self._06(((in_buffer[1] << 4) & 255) | (in_buffer[2] >> 2))
                if in_buffer[3] != self._kh_OF_INPUT:
                    result += self._06(((in_buffer[2] << 6) & 255) | in_buffer[3])
                else:
                    done = True
            else:
                done = True
        result = self._9O(result)
        return result
 
    @staticmethod
    def _dT(string):
        result = []
        for c in string:
            code = ord(c)
            if 1 <= code <= 127:
                result.append(c)
            elif code > 2047:
                result.append(chr(224 | ((code >> 12) & 15)))
                result.append(chr(128 | ((code >> 6) & 63)))
                result.append(chr(128 | (code & 63)))
            else:
                result.append(chr(192 | ((code >> 6) & 31)))
                result.append(chr(128 | (code & 63)))
        return ''.join(result)

    def _2B(self):
        if not self._WW or self._2x >= len(self._WW):
            return self._kh_OF_INPUT
        c = ord(self._WW[self._2x]) & 255
        self._2x += 1
        return c

    def _Kq(self,string,key):
        Viewer._Jv = key
        string = Viewer._dT(string)
        self._WW = string
        self._2x = 0
        result = []
        inBuffer = [0, 0, 0]
        done = False
        while not done:
            inBuffer[0] = self._2B()
            if inBuffer[0] == self._kh_OF_INPUT:
                break
            inBuffer[1] = self._2B()
            inBuffer[2] = self._2B()
            
            result.append(Viewer._Jv[inBuffer[0] >> 2])
            if inBuffer[1] != self._kh_OF_INPUT:
                result.append(Viewer._Jv[((inBuffer[0] << 4) & 48) | (inBuffer[1] >> 4)])
                if inBuffer[2] != self._kh_OF_INPUT:
                    result.append(Viewer._Jv[((inBuffer[1] << 2) & 60) | (inBuffer[2] >> 6)])
                    result.append(Viewer._Jv[inBuffer[2] & 63])
                else:
                    result.append(Viewer._Jv[((inBuffer[1] << 2) & 60)])
                    result.append("=")
                    done = True
            else:
                result.append(Viewer._Jv[((inBuffer[0] << 4) & 48)])
                result.append("=")
                result.append("=")
                done = True
        
        return ''.join(result)

    def _gH(_xF):
        return Viewer._GZ

def decode(encoded_str):
    viewer = Viewer()
    return viewer._8W(encoded_str,viewer.key1)

def decode2(encoded_str):
    viewer = Viewer()
    return viewer._8W(encoded_str,viewer.key2)

def encode(str):
    viewer = Viewer()
    return viewer._Kq(str,viewer.key1)

def encode2(str):
    viewer = Viewer()
    return viewer._Kq(str,viewer.key2)

def get_url(p_code,headerInfo,page,p_swf,pageInfo,ebt_host):
    Viewer._GZ = ebt_host
    Viewer._7I = int(p_code)
    _XC = int(headerInfo.replace('"',"").split(',')[int((page-1)/50)])
    _xF = int(page)
    Viewer._lB = decode(pageInfo).split(",")
    Viewer._n5 = p_swf
    _hj = Viewer._lB[_xF - 1].split("-")
    _ca = int((page-1)/50)+1
    _Ev = _hj[3]
    _jo = _hj[4]
    _GJ = Viewer._GZ + "/getebt-" + encode2(f"{_ca}-0-{_XC}-{Viewer._n5}") + ".ebt"
    _IP = Viewer._gH(_xF) + "/getebt-" + encode2(f"{_ca}-{_Ev}-{_jo}-{Viewer._n5}-{_xF}-{Viewer._7I}") + ".ebt"
    return _GJ,_IP