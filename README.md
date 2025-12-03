# DENEY İSTATİSTİKLERİ VE KARŞILAŞTIRMA RAPORU


Toplam Senaryo Sayısı: 20
Her Senaryo için Tekrar Sayısı: 5
Toplam Koşu: 100
Rapor Oluşturulma Tarihi: 2025-12-03 20:47:11

--------------------------------------------------------------------------------
BAŞARISIZ ÖRNEKLER ÖZETİ
--------------------------------------------------------------------------------

Toplam Başarısız Örnek Sayısı: 86

Algoritma Bazında Başarısızlık Sayıları:
  Basit: 23 başarısız örnek
  Q-Learning: 30 başarısız örnek
  SARSA: 33 başarısız örnek

İlk 10 Başarısız Örneğin Detayları:

1. Senaryo 1, Tekrar 3, Algoritma: Basit
   Kaynak: 239, Hedef: 18
   Talep Edilen Bant Genişliği: 291.98 Mbps
   Gerekçe: Bant genişliği yetersiz: minimum=115.03 Mbps, talep=291.98 Mbps (darboğaz kenar: (58, 18))

2. Senaryo 1, Tekrar 4, Algoritma: Basit
   Kaynak: 53, Hedef: 136
   Talep Edilen Bant Genişliği: 291.98 Mbps
   Gerekçe: Bant genişliği yetersiz: minimum=227.63 Mbps, talep=291.98 Mbps (darboğaz kenar: (53, 136))

3. Senaryo 1, Tekrar 4, Algoritma: Q-Learning
   Kaynak: 53, Hedef: 136
   Talep Edilen Bant Genişliği: 291.98 Mbps
   Gerekçe: Bant genişliği yetersiz: minimum=227.63 Mbps, talep=291.98 Mbps (darboğaz kenar: (53, 136))

4. Senaryo 1, Tekrar 4, Algoritma: SARSA
   Kaynak: 53, Hedef: 136
   Talep Edilen Bant Genişliği: 291.98 Mbps
   Gerekçe: Bant genişliği yetersiz: minimum=227.63 Mbps, talep=291.98 Mbps (darboğaz kenar: (53, 136))

5. Senaryo 1, Tekrar 5, Algoritma: Q-Learning
   Kaynak: 136, Hedef: 198
   Talep Edilen Bant Genişliği: 291.98 Mbps
   Gerekçe: Bant genişliği yetersiz: minimum=183.41 Mbps, talep=291.98 Mbps (darboğaz kenar: (96, 198))

6. Senaryo 3, Tekrar 1, Algoritma: Basit
   Kaynak: 54, Hedef: 244
   Talep Edilen Bant Genişliği: 468.02 Mbps
   Gerekçe: Bant genişliği yetersiz: minimum=389.66 Mbps, talep=468.02 Mbps (darboğaz kenar: (54, 244))

7. Senaryo 3, Tekrar 1, Algoritma: Q-Learning
   Kaynak: 54, Hedef: 244
   Talep Edilen Bant Genişliği: 468.02 Mbps
   Gerekçe: Bant genişliği yetersiz: minimum=389.66 Mbps, talep=468.02 Mbps (darboğaz kenar: (54, 244))

8. Senaryo 3, Tekrar 1, Algoritma: SARSA
   Kaynak: 54, Hedef: 244
   Talep Edilen Bant Genişliği: 468.02 Mbps
   Gerekçe: Bant genişliği yetersiz: minimum=389.66 Mbps, talep=468.02 Mbps (darboğaz kenar: (54, 244))

9. Senaryo 3, Tekrar 2, Algoritma: Basit
   Kaynak: 10, Hedef: 44
   Talep Edilen Bant Genişliği: 468.02 Mbps
   Gerekçe: Bant genişliği yetersiz: minimum=345.14 Mbps, talep=468.02 Mbps (darboğaz kenar: (10, 44))

10. Senaryo 3, Tekrar 2, Algoritma: Q-Learning
   Kaynak: 10, Hedef: 44
   Talep Edilen Bant Genişliği: 468.02 Mbps
   Gerekçe: Bant genişliği yetersiz: minimum=345.14 Mbps, talep=468.02 Mbps (darboğaz kenar: (10, 44))

#ALGORİTMA KARŞILAŞTIRMASI - İSTATİSTİKSEL ANALİZ

--------------------------------------------------------------------------------
Toplam Maliyet
--------------------------------------------------------------------------------

Basit:
  Geçerli Örnek Sayısı: 77
  Ortalama: 5.157633
  Standart Sapma: 1.241947
  En İyi (Minimum): 1.882216
  En Kötü (Maksimum): 7.161838
  Medyan: 5.408370

Q-Learning:
  Geçerli Örnek Sayısı: 70
  Ortalama: 8.183926
  Standart Sapma: 5.508771
  En İyi (Minimum): 1.882216
  En Kötü (Maksimum): 29.131622
  Medyan: 6.772260

SARSA:
  Geçerli Örnek Sayısı: 67
  Ortalama: 7.876855
  Standart Sapma: 4.670575
  En İyi (Minimum): 1.882216
  En Kötü (Maksimum): 24.048848
  Medyan: 6.999066

--------------------------------------------------------------------------------
Toplam Gecikme (ms)
--------------------------------------------------------------------------------

Basit:
  Geçerli Örnek Sayısı: 77
  Ortalama: 8.987135
  Standart Sapma: 2.269363
  En İyi (Minimum): 3.043007
  En Kötü (Maksimum): 12.979947
  Medyan: 9.544814

Q-Learning:
  Geçerli Örnek Sayısı: 70
  Ortalama: 14.949313
  Standart Sapma: 10.331002
  En İyi (Minimum): 3.043007
  En Kötü (Maksimum): 52.637106
  Medyan: 12.339305

SARSA:
  Geçerli Örnek Sayısı: 67
  Ortalama: 14.400826
  Standart Sapma: 8.691850
  En İyi (Minimum): 3.043007
  En Kötü (Maksimum): 44.307017
  Medyan: 12.795834

--------------------------------------------------------------------------------
Güvenilirlik Maliyeti
--------------------------------------------------------------------------------

Basit:
  Geçerli Örnek Sayısı: 77
  Ortalama: 0.126597
  Standart Sapma: 0.038373
  En İyi (Minimum): 0.032535
  En Kötü (Maksimum): 0.203263
  Medyan: 0.130712

Q-Learning:
  Geçerli Örnek Sayısı: 70
  Ortalama: 0.127420
  Standart Sapma: 0.059388
  En İyi (Minimum): 0.028324
  En Kötü (Maksimum): 0.305423
  Medyan: 0.127461

SARSA:
  Geçerli Örnek Sayısı: 67
  Ortalama: 0.115623
  Standart Sapma: 0.057836
  En İyi (Minimum): 0.028324
  En Kötü (Maksimum): 0.294276
  Medyan: 0.101197

--------------------------------------------------------------------------------
Kaynak Maliyeti
--------------------------------------------------------------------------------

Basit:
  Geçerli Örnek Sayısı: 77
  Ortalama: 3.130432
  Standart Sapma: 1.199314
  En İyi (Minimum): 1.094492
  En Kötü (Maksimum): 7.092001
  Medyan: 3.166066

Q-Learning:
  Geçerli Örnek Sayısı: 70
  Ortalama: 3.355218
  Standart Sapma: 2.381482
  En İyi (Minimum): 1.030184
  En Kötü (Maksimum): 13.607209
  Medyan: 2.673599

SARSA:
  Geçerli Örnek Sayısı: 67
  Ortalama: 3.208775
  Standart Sapma: 2.198723
  En İyi (Minimum): 1.030184
  En Kötü (Maksimum): 9.739976
  Medyan: 2.587977

--------------------------------------------------------------------------------
Çalışma Süresi (saniye)
--------------------------------------------------------------------------------

Basit:
  Geçerli Örnek Sayısı: 77
  Ortalama: 0.048171
  Standart Sapma: 0.030988
  En İyi (Minimum): 0.000734
  En Kötü (Maksimum): 0.146532
  Medyan: 0.042573

Q-Learning:
  Geçerli Örnek Sayısı: 70
  Ortalama: 2.894277
  Standart Sapma: 0.663784
  En İyi (Minimum): 0.956450
  En Kötü (Maksimum): 4.157265
  Medyan: 2.936830

SARSA:
  Geçerli Örnek Sayısı: 67
  Ortalama: 1.449677
  Standart Sapma: 0.449538
  En İyi (Minimum): 0.349458
  En Kötü (Maksimum): 2.681289
  Medyan: 1.513015

--------------------------------------------------------------------------------
Yol Uzunluğu (düğüm sayısı)
--------------------------------------------------------------------------------

Basit:
  Geçerli Örnek Sayısı: 77
  Ortalama: 2.818182
  Standart Sapma: 0.450943
  En İyi (Minimum): 2.000000
  En Kötü (Maksimum): 4.000000
  Medyan: 3.000000

Q-Learning:
  Geçerli Örnek Sayısı: 70
  Ortalama: 2.842857
  Standart Sapma: 1.016326
  En İyi (Minimum): 2.000000
  En Kötü (Maksimum): 7.000000
  Medyan: 3.000000

SARSA:
  Geçerli Örnek Sayısı: 67
  Ortalama: 2.731343
  Standart Sapma: 0.863083
  En İyi (Minimum): 2.000000
  En Kötü (Maksimum): 5.000000
  Medyan: 3.000000


#ÖZET KARŞILAŞTIRMA TABLOSU

Algoritma            Ort. Toplam Maliyet       Ort. Çalışma Süresi (sn)      
--------------------------------------------------------------------------------
Basit                5.157633                  0.048171                      
Q-Learning           8.183926                  2.894277                      
SARSA                7.876855                  1.449677                      
