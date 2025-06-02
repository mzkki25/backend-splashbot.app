import pandas as pd

def init_question_gm(initial_question):
    command = f"""
        Anda adalah **SPLASHBot**, asisten AI yang ahli dalam bidang **ekonomi**, termasuk topik ekonomi makro dan mikro, kebijakan fiskal dan moneter, perdagangan internasional, keuangan publik, serta indikator ekonomi.

        ### Berikut ini adalah pertanyaan awal dari sistem:
        "{initial_question}"

        Note: **Ini adalah initial question untuk user yang belum tahu untuk bertanya tentang apa**

        ### Tugas Anda adalah membuat **hingga 5 pertanyaan lanjutan** yang:
        - Relevan dan berkaitan langsung dengan topik ekonomi makro,
        - Bersifat eksploratif untuk mendorong pemahaman yang lebih dalam,
        - Disampaikan secara profesional dan mudah dipahami,
        - Singkat dan langsung ke inti persoalan (maksimal satu kalimat per pertanyaan),
        - Cocok untuk percakapan awal bersama chatbot ekonomi.

        Tampilkan hasil akhir dalam format list Python standar seperti ini:
        [
            "Pertanyaan lanjutan 1?",
            "Pertanyaan lanjutan 2?",
            ...
        ]
    """.strip()

    return command

def init_question_ngm(
    types: str,
    df: pd.DataFrame
):
    target_var = ""
    prediction_var = ""
    satuan = ""

    if types == "2 Wheels":
        target_var = "jumlah_penjualan_sepeda_motor"
        prediction_var = "prediksi_jumlah_penjualan_sepeda_motor"
        satuan = "dalam satuan unit"
    elif types == "4 Wheels":
        target_var = "jumlah_penjualan_mobil"
        prediction_var = "prediksi_jumlah_penjualan_mobil"
        satuan = "dalam satuan unit"
    elif types == "Retail Beauty":
        target_var = "jumlah_pengeluaran_produk_kecantikan"
        prediction_var = "prediksi_jumlah_pengeluaran_produk_kecantikan"
        satuan = "dalam satuan rupiah"
    elif types == "Retail Drugstore":
        target_var = "jumlah_pengeluaran_obat"
        prediction_var = "prediksi_jumlah_pengeluaran_obat"
        satuan = "dalam satuan rupiah"
    elif types == "Retail FnB":
        target_var = "jumlah_pengeluaran_fnb"
        prediction_var = "prediksi_jumlah_pengeluaran_fnb"
        satuan = "dalam satuan rupiah"
    elif types == "Retail General":
        target_var = "jumlah_pengeluaran_retail"
        prediction_var = "prediksi_jumlah_pengeluaran_retail"
        satuan = "dalam satuan rupiah"

    command = f"""
        Kamu adalah **SPLASHBot**, sebuah AI Agent yang ahli dalam menjawab pertanyaan seputar **ekonomi**, termasuk ekonomi makro, mikro, kebijakan fiskal/moneter, perdagangan, keuangan, dan indikator ekonomi.

        ### Diketahui Data yang Disediakan (Kolom Kategorikal):
        - Kolom: {df.columns.tolist()} 

        - Kota (`kab`): {df['kab'].unique().tolist()}
        - Provinsi (`prov`): {df['prov'].unique().tolist()}
        - Tahun (`year`): {df['year'].unique().tolist()}
        - Target variabel (penjualan): `{target_var}` ({satuan})
        - Target prediksi: `{prediction_var}` ({satuan})

        Data diatas adalah data penjualan {types} di Indonesia. Data ini berisi informasi tentang penjualan {types} berdasarkan tahun, provinsi, dan kabupaten/kota.

        Note: **Ini adalah initial question untuk user yang belum tahu untuk bertanya tentang apa**

        ### Tugasmu adalah:
        - Buatlah hingga 5 pertanyaan awal yang singkat, relevan, profesional, dan bersifat eksploratif untuk membantu pengguna memahami topik ini lebih lanjut, pastikan pertanyaan yang diberikan hanya yang berkaitan dengan dataset yang tersedia
        - Pertanyaan awal harus berkorelasi dengan pertanyaan bisnis
        - Pertanyaan awal sebisa mungkin harus menyinggung kota dan tahun yang ada di dataset
        - Pertanyaan awal harus **berkaitan dengan data yang tersedia**. 
        - Berikan hasil dalam format list Python (satu pertanyaan per elemen) tanpa ditampung dalam variabel apapun (cukup list nya saja).

        Contoh format:
        [
            "Pertanyaan lanjutan 1?",
            "Pertanyaan lanjutan 2?",
            ...
        ]
    """.strip()

    return command