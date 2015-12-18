import qrcode

def gen_jpeg_pic(link):
    qr = qrcode.QRCode(version=1, box_size=7, border=2)
    qr.add_data(link)
    qr.make(fit=True)
    x = qr.make_image()
    
    img_file = open('/tmp/item_pic.jpg', 'wb')
    x.save(img_file, 'JPEG')
    img_file.close()
    
    
if __name__ == '__main__':
    link = 'http://m.xiaolu.so/pages/shangpinxq.html?id=24340&linkid=44'
    gen_jpeg_pic(link)