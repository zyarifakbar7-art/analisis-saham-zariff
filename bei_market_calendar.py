from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

WIB = timezone(timedelta(hours=7))

HARI_ID: dict[int, str] = {
    0: "Senin",
    1: "Selasa",
    2: "Rabu",
    3: "Kamis",
    4: "Jumat",
    5: "Sabtu",
    6: "Minggu",
}

BULAN_ID: dict[int, str] = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "Mei",
    6: "Jun",
    7: "Jul",
    8: "Agu",
    9: "Sep",
    10: "Okt",
    11: "Nov",
    12: "Des",
}

# Daftar tanggal merah / libur bursa BEI (format "YYYY-MM-DD")
LIBUR_BEI: set[str] = {
    "2026-12-25",  # Hari Raya Natal
}


def ke_wib(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(WIB)
    if now.tzinfo is None:
        return now.replace(tzinfo=WIB)
    return now.astimezone(WIB)


def adalah_tanggal_merah(tgl: date) -> bool:
    return tgl.isoformat() in LIBUR_BEI


def adalah_hari_bursa(tgl: date) -> bool:
    return tgl.weekday() < 5 and not adalah_tanggal_merah(tgl)


def hari_bursa_berikutnya(mulai_dari: date) -> date:
    calon = mulai_dari + timedelta(days=1)
    while not adalah_hari_bursa(calon):
        calon += timedelta(days=1)
    return calon


def format_tanggal_panjang(tgl: date) -> str:
    return f"{HARI_ID[tgl.weekday()]}, {tgl.day:02d} {BULAN_ID[tgl.month]} {tgl.year}"


def format_tanggal_pendek(tgl: date) -> str:
    return f"{tgl.day:02d} {BULAN_ID[tgl.month]}"


def status_sesi_harian(now: datetime | None = None) -> dict[str, Any]:
    dt = ke_wib(now)
    hari_ini = dt.date()
    jam_menit = dt.time()

    if not adalah_hari_bursa(hari_ini):
        tgl_lanjut = hari_bursa_berikutnya(hari_ini)
        return {
            "sesi_aktif": "Sesi 1",
            "label_sesi": f"Sesi 1 ({format_tanggal_pendek(tgl_lanjut)})",
            "label_fokus": f"Sesi 1 • {format_tanggal_panjang(tgl_lanjut)}",
            "tanggal_target": tgl_lanjut,
            "bursa_buka_hari_ini": False,
        }

    # Senin s.d. Jumat: berganti hari otomatis Sesi 1; masuk Sesi 2 mulai 13:30 WIB
    sesi = "Sesi 2" if jam_menit >= time(13, 30) else "Sesi 1"
    return {
        "sesi_aktif": sesi,
        "label_sesi": f"{sesi} • {format_tanggal_panjang(hari_ini)}",
        "label_fokus": f"{sesi} ({format_tanggal_pendek(hari_ini)})",
        "tanggal_target": hari_ini,
        "bursa_buka_hari_ini": True,
    }


def cek_status_bursa_bei(now: datetime | None = None) -> dict[str, Any]:
    dt = ke_wib(now)
    hari_ini = dt.date()
    wd = hari_ini.weekday()
    is_weekend = wd in (5, 6)
    is_libur_biasa = (not is_weekend) and adalah_tanggal_merah(hari_ini)
    sesi_info = status_sesi_harian(dt)

    if is_weekend or is_libur_biasa:
        tgl_lanjut = hari_bursa_berikutnya(hari_ini)
        hari_lanjut_str = format_tanggal_panjang(tgl_lanjut)

        if is_weekend:
            alasan = "akhir pekan"
            lanjut_teks = (
                f"Senin, {tgl_lanjut.day:02d} {BULAN_ID[tgl_lanjut.month]} {tgl_lanjut.year}"
                if tgl_lanjut.weekday() == 0
                else hari_lanjut_str
            )
        else:
            alasan = "tanggal merah / libur bursa"
            lanjut_teks = hari_lanjut_str

        pesan_tutup = (
            f"Pasar saham tutup karena {alasan} ({format_tanggal_panjang(hari_ini)}) "
            f"dan akan dilanjutkan pada {lanjut_teks} (08:45 WIB Pra-Pembukaan / 09:00 WIB Sesi 1)."
        )

        return {
            "bursa_buka": False,
            "jenis_libur": "weekend" if is_weekend else "tanggal_merah",
            "badge": "LIBUR BURSA",
            "sesi_aktif": "Sesi 1",
            "label_sesi": sesi_info["label_sesi"],
            "label_fokus": sesi_info["label_fokus"],
            "tanggal_hari_ini": hari_ini,
            "tanggal_lanjutan": tgl_lanjut,
            "hari_lanjutan_str": lanjut_teks,
            "pesan_pemberitahuan": pesan_tutup,
            "jam_wib": dt.strftime("%H:%M:%S WIB"),
        }

    jam_menit = dt.time()
    if jam_menit < time(8, 45):
        badge = "PRA-PEMBUKAAN"
        pesan_aktif = (
            f"Menunggu Pra-Pembukaan 08:45 WIB • {sesi_info['sesi_aktif']} "
            f"({format_tanggal_panjang(hari_ini)})"
        )
    elif jam_menit < time(9, 0):
        badge = "PRE-OPENING"
        pesan_aktif = (
            f"Sesi Pra-Pembukaan berlangsung • {sesi_info['sesi_aktif']} "
            f"({format_tanggal_panjang(hari_ini)})"
        )
    elif jam_menit < time(12, 0):
        badge = "SESI 1 AKTIF"
        pesan_aktif = f"Perdagangan Sesi 1 berlangsung • {format_tanggal_panjang(hari_ini)}"
    elif jam_menit < time(13, 30):
        badge = "ISHOMA / JEDA"
        pesan_aktif = (
            f"Jeda istirahat sesi • Sesi 2 dimulai 13:30 WIB ({format_tanggal_panjang(hari_ini)})"
        )
    elif jam_menit < time(16, 15):
        badge = "SESI 2 AKTIF"
        pesan_aktif = f"Perdagangan Sesi 2 berlangsung • {format_tanggal_panjang(hari_ini)}"
    else:
        tgl_besok = hari_bursa_berikutnya(hari_ini)
        badge = "PASAR TUTUP"
        pesan_aktif = (
            f"Perdagangan hari ini selesai • Dilanjutkan Sesi 1 pada "
            f"{format_tanggal_panjang(tgl_besok)}."
        )

    tgl_lanjutan_aktif = hari_ini if jam_menit < time(16, 15) else hari_bursa_berikutnya(hari_ini)

    return {
        "bursa_buka": True,
        "jenis_libur": None,
        "badge": badge,
        "sesi_aktif": sesi_info["sesi_aktif"],
        "label_sesi": sesi_info["label_sesi"],
        "label_fokus": sesi_info["label_fokus"],
        "tanggal_hari_ini": hari_ini,
        "tanggal_lanjutan": tgl_lanjutan_aktif,
        "hari_lanjutan_str": format_tanggal_panjang(tgl_lanjutan_aktif),
        "pesan_pemberitahuan": pesan_aktif,
        "jam_wib": dt.strftime("%H:%M:%S WIB"),
    }
