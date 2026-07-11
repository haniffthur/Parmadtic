# 🚀 PARMADTIC
### Paramadina Multiplier Educational Simulation Platform

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.x-green?style=for-the-badge&logo=django">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/MySQL-8.x-orange?style=for-the-badge&logo=mysql">
  <img src="https://img.shields.io/badge/Redis-Latest-red?style=for-the-badge&logo=redis">
  <img src="https://img.shields.io/badge/TailwindCSS-3.x-38B2AC?style=for-the-badge&logo=tailwind-css">
</p>

---

# 📖 Tentang Project

**PARMADTIC (Paramadina Multiplier Educational Simulation Platform)** adalah sebuah laboratorium virtual berbasis web yang mensimulasikan mekanisme permainan **Crash Game** sebagai media pembelajaran.

Project ini **BUKAN platform perjudian** dan **tidak menggunakan uang asli**. Seluruh mekanisme dibuat untuk tujuan edukasi, penelitian, dan pembelajaran mengenai:

- Sistem Realtime
- WebSocket
- Probabilitas
- Random Number Generation
- Provably Fair Algorithm
- Transaction Flow
- Database Design
- Backend Architecture
- Frontend Animation
- Software Engineering

---

# 🎯 Tujuan Project

Project ini dikembangkan sebagai media pembelajaran untuk memahami bagaimana sebuah sistem multiplayer realtime bekerja, meliputi:

- Simulasi multiplier
- Sinkronisasi data realtime
- Arsitektur backend Django
- WebSocket menggunakan Django Channels
- Manajemen transaksi virtual
- Pengelolaan wallet simulasi
- Sistem leaderboard
- Logging aktivitas
- Dashboard administrator

---

# ✨ Fitur

## 👤 User

- Login & Register
- Dashboard
- Virtual Wallet
- Deposit Virtual
- Withdraw Virtual
- Betting Simulation
- Auto Bet
- Auto Cashout
- History Permainan
- Leaderboard
- Profile

---

## 🎮 Simulation Engine

- Realtime Multiplier
- Countdown sebelum ronde
- Provably Fair System
- Random Crash Point
- Auto Cashout
- Auto Bet
- Live Players
- Live Bets
- Live Multiplier
- Live History

---

## 👨‍💻 Admin

- Dashboard
- User Management
- Wallet Management
- Simulation Monitoring
- Round History
- Betting History
- Deposit Approval
- Withdraw Approval
- System Configuration
- Activity Log

---

# 🏗️ Tech Stack

## Backend

- Python
- Django
- Django REST Framework
- Django Channels
- Daphne

---

## Frontend

- HTML5
- Tailwind CSS
- JavaScript
- Alpine.js

---

## Database

- MySQL

---

## Realtime

- Redis
- Django Channels
- WebSocket

---

# 📂 Struktur Project

```text
Parmadtic
│
├── core/
├── dashboard/
├── simulation/
├── users/
├── wallet/
├── templates/
├── static/
├── media/
│
├── parmadtic/
│     ├── settings.py
│     ├── urls.py
│     ├── asgi.py
│     └── wsgi.py
│
├── manage.py
├── requirements.txt
├── README.md
├── SETUP.md
└── .env.example
```

---

# 🚀 Quick Start

Clone repository

```bash
git clone https://github.com/haniffthur/Parmadtic.git
```

Masuk ke project

```bash
cd Parmadtic
```

Buat Virtual Environment

```bash
python -m venv venv
```

Aktifkan Virtual Environment

Windows

```bash
venv\Scripts\activate
```

Linux / Mac

```bash
source venv/bin/activate
```

Install dependency

```bash
pip install -r requirements.txt
```

Jalankan migration

```bash
python manage.py migrate
```

Buat Superuser

```bash
python manage.py createsuperuser
```

Jalankan server

```bash
python manage.py runserver
```

---

# ⚙️ Environment Variable

Buat file `.env`

```env
SECRET_KEY=
DEBUG=True

DB_NAME=parmadtic
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

---

# 🔴 Redis

Pastikan Redis berjalan sebelum menggunakan fitur realtime.

Default:

```
127.0.0.1:6379
```

---

# 🔄 Git Workflow

```text
main
│
├── feature/login
├── feature/dashboard
├── feature/simulation
├── feature/wallet
├── fix/navbar
├── fix/api
└── hotfix/security
```

---

# 📸 Screenshot

Tambahkan screenshot aplikasi di folder berikut:

```
docs/images/
```

Contoh:

```
docs/images/dashboard.png

docs/images/game.png

docs/images/admin.png
```

---

# 📚 Dokumentasi

| Dokumen | Keterangan |
|---------|------------|
| README.md | Dokumentasi utama project |
| SETUP.md | Panduan instalasi project |

---

# 🤝 Contributing

1. Fork repository

2. Buat branch baru

```bash
git checkout -b feature/nama-fitur
```

3. Commit

```bash
git commit -m "Menambahkan fitur baru"
```

4. Push

```bash
git push origin feature/nama-fitur
```

5. Buat Pull Request

---

# ⚠️ Disclaimer

PARMADTIC dibuat **hanya untuk tujuan edukasi**.

Project ini:

- Tidak menerima uang asli.
- Tidak menyediakan layanan perjudian.
- Tidak memiliki sistem taruhan dengan nilai ekonomi.
- Seluruh transaksi menggunakan saldo virtual.

---

# 👨‍💻 Maintainer

**Hanif**

---

# ⭐ Support

Jika project ini bermanfaat, jangan lupa berikan ⭐ pada repository ini.

---

<p align="center">
Made with ❤️ by handev
</p>