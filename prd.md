# Bilgi Yarışması Uygulaması - Ürün Gereksinim Dokümanı

## Genel Bakış
Bilgi Yarışması, kullanıcıların genel kültür sorularını cevaplayarak puan kazandığı bir masaüstü uygulamasıdır. Uygulama, Python ve Tkinter kullanılarak geliştirilmiştir.

## Temel Özellikler

### Ana Menü
- Oyuna Başla: Takım ismi girme ekranına yönlendirir
- Yüksek Skorlar: En yüksek skorları görüntüler
- Ayarlar: Uygulama ayarlarını gösterir
- Çıkış: Uygulamadan çıkış yapar

### Oyun Akışı
1. Kullanıcı "Oyuna Başla" butonuna tıklar
2. Takım ismi girme ekranı gösterilir
3. Takım ismi girildikten sonra veritabanından rastgele 10 soru seçilir
4. Her soru için ayarlarda belirlenen süre verilir (varsayılan: 30 saniye)
5. Doğru cevap verildiğinde, kalan süreye göre ek puan kazanılır
6. Oyun sonunda takım skoru otomatik olarak kaydedilir

### Yüksek Skorlar
- En yüksek 10 skor listelenir
- Sıra, takım ismi, skor ve tarih bilgileri gösterilir

### Ayarlar
- Soru Süresi: Her soru için ayrılan süreyi değiştirme (10-60 saniye arası)
- Tema Seçimi: Gündüz modu (açık tema) ve Gece modu (koyu tema) seçenekleri
- Ayarlar JSON dosyasında saklanır ve uygulama başlatıldığında otomatik olarak yüklenir

### Veritabanı
- SQLite veritabanı kullanılır
- Sorular ve yüksek skorlar veritabanında saklanır

## Teknik Gereksinimler
- Python 3.x
- Tkinter kütüphanesi
- SQLite veritabanı

## Kullanıcı Arayüzü
- Sade ve kullanıcı dostu arayüz
- Responsive tasarım
- Gündüz ve gece modu desteği

## Gelecek Özellikler
- Ses efektleri
- Zorluk seviyeleri
- Daha fazla tema seçeneği
- Çoklu dil desteği 