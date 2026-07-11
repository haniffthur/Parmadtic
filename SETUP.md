# 🚀 Parmadtic - Development Setup Guide

Selamat datang di project **Parmadtic**.

Dokumen ini berisi panduan lengkap untuk menjalankan project di komputer lokal bagi seluruh anggota tim.

---

## Persyaratan

Pastikan software berikut sudah terinstall.

| Software | Versi yang Disarankan |
| --- | --- |
| Python | 3.11 atau lebih baru |
| Git | Terbaru |
| MySQL Server | 8.x |
| Redis | Terbaru |
| Visual Studio Code | Disarankan |

---

## 1. Clone Repository

```bash
git clone https://github.com/haniffthur/Parmadtic.git
cd Parmadtic
```

---

## 2. Membuat Virtual Environment

```bash
python -m venv venv
```

Aktifkan Virtual Environment:

### Windows

```bash
venv\Scripts\activate
```

### Linux / MacOS

```bash
source venv/bin/activate
```

Jika berhasil maka terminal akan berubah menjadi:

```text
(venv)
```

---

## 3. Install Dependency

```bash
pip install -r requirements.txt
```

Dependency yang akan terinstall antara lain:

- Django
- Django REST Framework
- Django Channels
- Channels Redis
- PyMySQL
- Daphne
- Gunicorn

---

## 4. Membuat Database

```sql
CREATE DATABASE parmadtic;
```

Pastikan MySQL Server sudah berjalan.

---

## 5. Membuat File .env

```env
SECRET_KEY=YOUR_SECRET_KEY_HERE
DEBUG=True
DB_NAME=parmadtic
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

### Apa itu SECRET_KEY?

`SECRET_KEY` adalah kunci rahasia yang digunakan oleh Django untuk mengamankan session login, cookie, CSRF Token, dan fitur keamanan lainnya.

### Cara Mendapatkan SECRET_KEY

**Opsi 1 (Direkomendasikan):** Minta SECRET_KEY kepada maintainer project.

**Opsi 2 (Membuat Sendiri):**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Contoh hasil:

```text
m(5&a+y0)hrr=5#n8b%x!8v!...
```

Masukkan ke file `.env`.

> **Penting:** File `.env` **JANGAN PERNAH** diupload ke GitHub.

---

## 6. Jalankan Migration

```bash
python manage.py migrate
```

Jika terdapat model baru:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 7. Membuat Superuser

```bash
python manage.py createsuperuser
```

---

## 8. Menjalankan Project

```bash
python manage.py runserver
```

Buka browser di `http://127.0.0.1:8000`

---

## Redis

Project menggunakan **Django Channels**. Untuk fitur realtime/WebSocket pastikan Redis berjalan di:

`127.0.0.1:6379`

---

## Struktur Project

```text
Parmadtic
│
├── core/
├── dashboard/
├── simulation/
├── templates/
├── static/
├── parmadtic/
│     ├── settings.py
│     ├── urls.py
│     ├── asgi.py
│     └── wsgi.py
│
├── manage.py
├── requirements.txt
├── README.md
└── SETUP.md
```

---

## Git Workflow

### Sebelum mulai bekerja

```bash
git pull origin main
```


