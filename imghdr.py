# imghdr.py
# Мини-реализация модуля imghdr для Python 3.13+

def what(file, h=None):
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            h = file.read(32)

    for test, format in tests:
        res = test(h)
        if res:
            return res
    return None


def test_jpeg(h):
    if h[6:10] in (b'JFIF', b'Exif'):
        return 'jpeg'

def test_png(h):
    if h[:8] == b'\211PNG\r\n\032\n':
        return 'png'

def test_gif(h):
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'

def test_tiff(h):
    if h[:2] in (b'MM', b'II'):
        return 'tiff'

def test_bmp(h):
    if h[:2] == b'BM':
        return 'bmp'

tests = [
    (test_jpeg, 'jpeg'),
    (test_png, 'png'),
    (test_gif, 'gif'),
    (test_tiff, 'tiff'),
    (test_bmp, 'bmp'),
]
