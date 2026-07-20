def decide_progression(load_signals):
    current_week_hours = load_signals["current_week_hours"]
    load_ratio = load_signals["load_ratio"]

    if current_week_hours == 0:
        status = "restart"
        label = "Ritim yeniden kurulmalı"
        advice = "Bu hafta hedef, performans değil yeniden düzenli hareket etmek olmalı."

    elif load_ratio is None:
        status = "insufficient_data"
        label = "Yeterli geçmiş veri yok"
        advice = "Bu hafta düşük-orta yoğunlukta güvenli bir başlangıç yapılmalı."

    elif load_ratio < 0.75:
        status = "below_baseline"
        label = "Yük normalin altında"
        advice = "Ritmi toparlamak için kolay koşu veya kısa Z2 bisiklet eklenebilir."

    elif load_ratio <= 1.15:
        status = "stable"
        label = "Yük dengeli"
        advice = "Yük dengeli. Uygunsa toplam süre en fazla %5-10 artırılabilir."

    elif load_ratio <= 1.35:
        status = "productive_build"
        label = "Kontrollü gelişim"
        advice = "Yük artışı makul. Sertleşmeden küçük hacim artışı yapılabilir."

    elif load_ratio <= 1.75:
        status = "caution_growth"
        label = "Dikkatli artış"
        advice = "Yük belirgin artmış. Yeni artış yerine benzer hacmi korumak daha güvenli."

    else:
        if current_week_hours < 2:
            status = "sharp_rebuild_low_absolute_load"
            label = "Oransal artış yüksek, mutlak hacim düşük"
            advice = (
                "Son hafta geçmiş ortalamaya göre belirgin artmış. "
                "Mutlak hacim düşük olsa da koşu yükünü artırmak yerine "
                "bisikleti kolay Z2 olarak eklemek daha doğru."
            )
        else:
            status = "spike_risk"
            label = "Ani yük artışı riski"
            advice = "Bu hafta yük fazla sıçramış. Toparlanma ve düşük yoğunluk öncelikli olmalı."

    return {
        "progression_status": status,
        "progression_label": label,
        "progression_advice": advice,
    }