import pandas as pd

def follow_up_question_gm(prompt, response):
    command = f"""
        Kamu adalah **SPLASHBot**, sebuah AI Agent yang ahli dalam menjawab pertanyaan seputar **perekonomian**, termasuk ekonomi makro, mikro, kebijakan fiskal/moneter/publik, perbankan, perdagangan, keuangan, dan indikator sosial ekonomi.

        Diberikan sebuah pertanyaan awal dari pengguna berikut:

        "{prompt}"

        dan jawaban yang sudah diberikan oleh sistem:

        "{response}"

        ### Tugasmu adalah:
        - Buatlah hingga 5 pertanyaan lanjutan yang singkat, relevan, profesional, dan bersifat eksploratif yang berkaitan dengan **ekonomi** untuk membantu pengguna memahami topik ini lebih lanjut. 
        - Berikan hasil dalam format list Python (satu pertanyaan per elemen) tanpa ditampung dalam variabel apapun (cukup list nya saja).
        Contoh format:
        [
            "Pertanyaan lanjutan 1?",
            "Pertanyaan lanjutan 2?",
            ...
        ]
    """.strip()
    
    return command

def follow_up_question_ngm(
    types: str, 
    df: pd.DataFrame, prompt, response
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

        Diberikan sebuah pertanyaan awal dari pengguna berikut:

        "{prompt}"

        dan jawaban yang sudah diberikan oleh sistem:

        "{response}"

        ### Tugasmu adalah: 
        - Buatlah hingga 5 pertanyaan lanjutan yang singkat, relevan, profesional, dan bersifat eksploratif untuk membantu pengguna memahami topik ini lebih lanjut
        - Pertanyaan lanjutan harus **berkaitan dengan data yang tersedia**. 
        - Pertanyaan lanjutan harus berkorelasi dengan pertanyaan bisnis
        - Pertanyaan lanjutan sebisa mungkin harus menyinggung kota dan tahun yang ada di dataset
        - Berikan hasil dalam format list Python (satu pertanyaan per elemen) tanpa ditampung dalam variabel apapun (cukup list nya saja).

        Contoh format:
        [
            "Pertanyaan lanjutan 1?",
            "Pertanyaan lanjutan 2?",
            ...
        ]
    """.strip()

    return command