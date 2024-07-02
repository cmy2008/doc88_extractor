var Viewer = function () { };
var _WW;
var _2x;
var _kh_OF_INPUT = -1;
var _Jv_r = new Array("P", "J", "L", "K", "M", "N", "O", "I", "3", "x", "y", "z", "0", "2", "1", "w", "v", "r", "p", "q", "s", "t", "o", "u", "H", "C", "F", "B", "D", "E", "G", "A", "n", "h", "i", "k", "j", "l", "m", "g", "f", "Z", "b", "a", "c", "e", "d", "Y", "R", "X", "T", "S", "U", "V", "Q", "W", "!", "5", "6", "7", "8", "9", "+", "4");
var _fE = new Array(128);
for (var i = 0; i < _Jv_r.length; i++) {
    _fE[_Jv_r[i]] = i
}
Viewer._t8 = function (str) {
    _WW = str;
    _2x = 0
}
var _WW;
var _2x;
Viewer._t8 = function (str) {
    _WW = str;
    _2x = 0
}
    ;
Viewer._06 = function (n) {
    n = n.toString(16);
    if (n.length == 1) {
        n = "0" + n
    }
    n = "%" + n;
    return unescape(n)
}
    ;
Viewer._9O = function (str) {
    var out, i, len, c;
    var char2, char3;
    out = "";
    len = str.length;
    i = 0;
    while (i < len) {
        c = str.charCodeAt(i++);
        switch (c >> 4) {
            case 0:
            case 1:
            case 2:
            case 3:
            case 4:
            case 5:
            case 6:
            case 7:
                out += str.charAt(i - 1);
                break;
            case 12:
            case 13:
                char2 = str.charCodeAt(i++);
                out += String.fromCharCode(((c & 31) << 6) | (char2 & 63));
                break;
            case 14:
                char2 = str.charCodeAt(i++);
                char3 = str.charCodeAt(i++);
                out += String.fromCharCode(((c & 15) << 12) | ((char2 & 63) << 6) | ((char3 & 63) << 0));
                break
        }
    }
    return out
}
    ;
Viewer._w7 = function () {
    if (!_WW) {
        return _kh_OF_INPUT
    }
    while (true) {
        if (_2x >= _WW.length) {
            return _kh_OF_INPUT
        }
        var nextCharacter = _WW.charAt(_2x);
        _2x++;
        if (_fE[nextCharacter]) {
            return _fE[nextCharacter]
        }
        if (nextCharacter == "P") {
            return 0
        }
    }
    return _kh_OF_INPUT
}
    ;

Viewer._8W = function (str) {
    Viewer._t8(str);
    var result = "";
    var inBuffer = new Array(4);
    var done = false;
    while (!done && (inBuffer[0] = Viewer._w7()) != _kh_OF_INPUT && (inBuffer[1] = Viewer._w7()) != _kh_OF_INPUT) {
        inBuffer[2] = Viewer._w7();
        inBuffer[3] = Viewer._w7();
        result += Viewer._06((((inBuffer[0] << 2) & 255) | inBuffer[1] >> 4));
        if (inBuffer[2] != _kh_OF_INPUT) {
            result += Viewer._06((((inBuffer[1] << 4) & 255) | inBuffer[2] >> 2));
            if (inBuffer[3] != _kh_OF_INPUT) {
                result += Viewer._06((((inBuffer[2] << 6) & 255) | inBuffer[3]))
            } else {
                done = true
            }
        } else {
            done = true
        }
    }
    result = Viewer._9O(result);
    return result
}
;
Viewer._Kq = function(str) {
    str = Viewer._dT(str);
    Viewer._t8(str);
    var result = "";
    var inBuffer = new Array(3);
    var lineCount = 0;
    var done = false;
    while (!done && (inBuffer[0] = Viewer._2B()) != _kh_OF_INPUT) {
        inBuffer[1] = Viewer._2B();
        inBuffer[2] = Viewer._2B();
        result += (_Jv[inBuffer[0] >> 2]);
        if (inBuffer[1] != _kh_OF_INPUT) {
            result += (_Jv[((inBuffer[0] << 4) & 48) | (inBuffer[1] >> 4)]);
            if (inBuffer[2] != _kh_OF_INPUT) {
                result += (_Jv[((inBuffer[1] << 2) & 60) | (inBuffer[2] >> 6)]);
                result += (_Jv[inBuffer[2] & 63])
            } else {
                result += (_Jv[((inBuffer[1] << 2) & 60)]);
                result += ("=");
                done = true
            }
        } else {
            result += (_Jv[((inBuffer[0] << 4) & 48)]);
            result += ("=");
            result += ("=");
            done = true
        }
    }
    return result
}
;
var _Jv = new Array("P","J","K","L","M","N","O","I","3","x","y","z","0","1","2","w","v","p","r","q","s","t","u","o","H","B","C","D","E","F","G","A","n","h","i","j","k","l","m","g","f","Z","a","b","c","d","e","Y","X","R","S","T","U","V","W","Q","!","5","6","7","8","9","+","4");
Viewer._GZ = "https://ebt160.doc88.com";
Viewer._NP = "0pUV1KPe1KDSzqMT2K3S2pUT2S3!2kjc0pUV1K3e1KDQzq052SMR2LUU2qnW2Kvc0pUV1K3e1KDVzqnV2qnU1LUV0SvR0K3c0pUV1KMe1KDRzqMS1Kj!2qPe2KvW2kH5zKMe2qD5zqnW0LUX1K0W2qM5zqvS1qvS1LRXzqsW2iU!2Sve0k3W2kjV2TUU2kjS0Sjc0pUV2SDe1KDTzq3W2KHT1qHe0SjV2kjTzKMe2qnXzqnW2LUS0qvX1qn!zq0S2SDS1LRXzqsW2TU!2SPe0SvW1qDT2iUT0SHT0qP="
Viewer._lB = null;
Viewer._lB = Viewer._8W(Viewer._NP).split(",");
Viewer._2B = function() {
    if (!_WW) {
        return _kh_OF_INPUT
    }
    if (_2x >= _WW.length) {
        return _kh_OF_INPUT
    }
    var c = _WW.charCodeAt(_2x) & 255;
    _2x++;
    return c
}
;
Viewer._dT = function(str) {
    var out, i, len, c;
    out = "";
    len = str.length;
    for (i = 0; i < len; i++) {
        c = str.charCodeAt(i);
        if ((c >= 1) && (c <= 127)) {
            out += str.charAt(i)
        } else {
            if (c > 2047) {
                out += String.fromCharCode(224 | ((c >> 12) & 15));
                out += String.fromCharCode(128 | ((c >> 6) & 63));
                out += String.fromCharCode(128 | ((c >> 0) & 63))
            } else {
                out += String.fromCharCode(192 | ((c >> 6) & 31));
                out += String.fromCharCode(128 | ((c >> 0) & 63))
            }
        }
    }
    return out
}
;
Viewer._gH = function(_xF) {
    return Viewer._GZ
}
;
Viewer._7I = 3995949474894; //Config.p_code;
var _XC = 124235; //Config.headerInfo.split(",");
var _xF = 2; //page
Viewer._n5 = "81-20190711-20190711025946_KhYrIyI9";//Config.p_swf;
var _hj = Viewer._lB[_xF - 1].split("-");
var _ca = 1;
var _Ev = _hj[3];
var _jo = _hj[4];
var _4J = _hj[1];
var _jD = _hj[2];
//PH second
var _GJ = Viewer._GZ + "/getebt-" + Viewer._Kq(_ca + "-0-" + _XC + "-" + Viewer._n5) + ".ebt";
//PK first
var _IP = Viewer._gH(_xF) + "/getebt-" + Viewer._Kq(_ca + "-" + _Ev + "-" + _jo + "-" + Viewer._n5 + "-" + _xF + "-" + Viewer._7I) + ".ebt";
// console.log(_ca + "-0-" + _XC + "-" + Viewer._n5)
// // js: 1-0-124235-81-20190711-20190711025946_KhYrIyI9
// // py: 1-0-124235-81-20190711-20190711025946_KhYrIyI9
console.log(_GJ)
console.log(_IP)
