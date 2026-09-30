Berikut panduan langkah demi langkah (*step-by-step*) untuk menginstal kebutuhan dan menjalankan aplikasi **Klasifikasi Himpunan Mahasiswa**:

---

### 1. Pastikan Python Sudah Terinstal

Pastikan Python (versi 3.10 atau yang lebih baru) sudah terpasang di komputer/laptop.
Buka **PowerShell** atau **Terminal**, lalu cek dengan perintah:

```powershell
python --version

```

---

### 2. Buka Terminal di Folder Proyek

Masuk ke direktori/folder proyek `Klasifikasi-Himpunan-Mahasiswa-Kelompok-F` menggunakan PowerShell atau Terminal bawaan VS Code.

---

### 3. (Opsional) Buat & Aktifkan Virtual Environment

Sangat disarankan membuat *virtual environment* agar pustaka (*library*) proyek tersimpan rapi dan tidak bentrok dengan instalasi Python bawaan:

```powershell
# 1. Buat virtual environment bernama venv
python -m venv venv

# 2. Aktifkan venv di Windows (PowerShell)
.\venv\Scripts\activate

```

*(Jika venv berhasil aktif, akan muncul tanda `(venv)` di sebelah kiri terminal).*

---

### 4. Install Dependensi / Library yang Dibutuhkan

Install modul `streamlit` dan `pandas` menggunakan file `requirements.txt`:

```powershell
pip install -r requirements.txt

```

Atau jika ingin menginstal modul secara langsung:

```powershell
pip install streamlit pandas

```

---

### 5. Jalankan Aplikasi

Eksekusi perintah berikut untuk membuka aplikasi di browser:

```powershell
python -m streamlit run app.py

```

Aplikasi akan otomatis terbuka di browser pada alamat **`http://localhost:8501`**.


```markdown
## 🚀 Cara Menjalankan Aplikasi

1. **Clone Repositori:**
   ```bash
   git clone [https://github.com/ojiojioji2006-cpu/Klasifikasi-Himpunan-Mahasiswa-Kelompok-F.git](https://github.com/ojiojioji2006-cpu/Klasifikasi-Himpunan-Mahasiswa-Kelompok-F.git)
   cd Klasifikasi-Himpunan-Mahasiswa-Kelompok-F

```

2. **Install Dependensi:**
```bash
pip install -r requirements.txt

```


3. **Jalankan Aplikasi:**
```bash
python -m streamlit run app.py

```



```

```
