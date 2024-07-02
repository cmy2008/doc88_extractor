class Viewer:
    _kh_OF_INPUT = -1
    
    _F0 = "U"
    _rs = "g"
    _Jv = ["P", "J", "K", "L", "O", "N", "M", "I", "3", "x", "y", "z", "0", "1", "2", "w", "v", "p", "r", "q", "s", "t", "u", "o", "H", "B", "C", "D", "E", "F", "G", "A", "n", "h", "i", "j", "k", "l", "m", _rs, "f", "Z", "a", "b", "c", "d", "e", "Y", "X", "R", "S", "T", _F0, "V", "W", "Q", "!", "5", "6", "7", "8", "9", "+", "4"]
    _Jv[4] = "M"
    _Jv[6] = "O"
    
    _GZ = "https://ebt160.doc88.com"
    _NP = "0pUV1KPe1KDSzqMT2K3S2pUT2S3!2kjc0pUV1K3e1KDQzq052SMR2LUU2qnW2Kvc0pUV1K3e1KDVzqnV2qnU1LUV0SvR0K3c0pUV1KMe1KDRzqMS1Kj!2qPe2KvW2kH5zKMe2qD5zqnW0LUX1K0W2qM5zqvS1qvS1LRXzqsW2iU!2Sve0k3W2kjV2TUU2kjS0Sjc0pUV2SDe1KDTzq3W2KHT1qHe0SjV2kjTzKMe2qnXzqnW2LUS0qvX1qn!zq0S2SDS1LRXzqsW2TU!2SPe0SvW1qDT2iUT0SHT0qP="
    _lB = None
    _lB = _NP.split(",")
    
    _2x = 0
    _WW = None

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
    
    @staticmethod
    def _2B():
        if not Viewer._WW or Viewer._2x >= len(Viewer._WW):
            return Viewer._kh_OF_INPUT
        c = ord(Viewer._WW[Viewer._2x]) & 255
        Viewer._2x += 1
        return c
    
    @staticmethod
    def _Kq(string):
        string = Viewer._dT(string)
        Viewer._WW = string
        Viewer._2x = 0
        result = []
        inBuffer = [0, 0, 0]
        done = False
        
        while not done:
            inBuffer[0] = Viewer._2B()
            if inBuffer[0] == Viewer._kh_OF_INPUT:
                break
            inBuffer[1] = Viewer._2B()
            inBuffer[2] = Viewer._2B()
            
            result.append(Viewer._Jv[inBuffer[0] >> 2])
            if inBuffer[1] != Viewer._kh_OF_INPUT:
                result.append(Viewer._Jv[((inBuffer[0] << 4) & 48) | (inBuffer[1] >> 4)])
                if inBuffer[2] != Viewer._kh_OF_INPUT:
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
    
    @staticmethod
    def _gH(_xF):
        return Viewer._GZ
def get_url(p_code,headerInfo,page,p_swf,pageInfo):
    Viewer._7I = p_code
    _XC = headerInfo
    _xF = page
    Viewer._lB = decode(pageInfo).split(",")
    print(Viewer._lB)
    Viewer._n5 = p_swf
    _hj = Viewer._lB[_xF - 1].split("-")
    _ca = 1
    _Ev = _hj[3]
    _jo = _hj[4]

    _GJ = Viewer._GZ + "/getebt-" + Viewer._Kq(f"{_ca}-0-{_XC}-{Viewer._n5}") + ".ebt"
    _IP = Viewer._gH(_xF) + "/getebt-" + Viewer._Kq(f"{_ca}-{_Ev}-{_jo}-{Viewer._n5}-{_xF}-{Viewer._7I}") + ".ebt"
    return _GJ,_IP