
ÖNCE SERVER.PY DOSYASINI ÇALIŞTIR. DAHA SONRA CLİENT.PY CLİENT DOSYASINI CURSOR ÜZERİNDEN AÇMAYIN MASAÜSTÜNE ATIP DOSYA KONUMUNA CMD EKRANINDAN AÇIN ÖRNEK 
cd\Users\emrea\Desktop
python client.py 




























# Bilgi Yarışması Uygulaması

Bu proje, gerçek zamanlı çok oyunculu bir bilgi yarışması uygulamasıdır.

## Özellikler

- Oda oluşturma ve katılma
- Gerçek zamanlı takım listesi güncellemesi
- Hazır/Hazır Değil durumu
- Sohbet sistemi
- Soru ve cevap yönetimi
- Puan sistemi

## Kurulum

1. Python 3.x'i yükleyin
2. Gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

## Kullanım

1. Sunucuyu başlatın:
```bash
python server.py
```

2. İstemciyi başlatın:
```bash
python client.py
```

## Gereksinimler

- Python 3.x
- Flask
- Flask-SocketIO
- SQLite3
- Tkinter (Python ile birlikte gelir)

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 
