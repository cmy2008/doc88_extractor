import base64

key1 = "PJLKMNOI3xyz021wvrpqstouHCFBDEGAnhikjlmgfZbacedYRXTSUVQW!56789+4"
key2 = "PJKLMNOI3xyz012wvprqstuoHBCDEFGAnhijklmgfZabcdeYXRSTUVWQ!56789+4"
std_str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def encode(data: str, key: str = key1) -> str:
    return (
        base64.b64encode(data.encode("utf-8"))
        .decode("utf-8")
        .translate(str.maketrans(std_str, key))
    )


def decode(data: str, key: str = key1) -> str:
    return base64.b64decode(data.translate(str.maketrans(key, std_str))).decode("utf-8")
