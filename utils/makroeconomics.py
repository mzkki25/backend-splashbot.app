import pandas as pd
import uuid
import os
import time
import json

from core.firebase import bucket
from utils.preprocessing import clean_code, save_code, read_clean_python_file
from core.gemini import model, model_2

from core.logging_logger import setup_logger
logger = setup_logger(__name__)

def two_wheels_model(text, user_id):
    df = pd.read_csv('dataset/fix_2w.csv')
    uid = str(uuid.uuid4())
    filepath = f"utils/_generated_code_{uid}.py"

    try:
        prompt = f"""
            Kamu adalah **SPLASHBot**, sebuah AI Agent yang bertugas membuat **blok kode Python** untuk menjawab pertanyaan berbasis data 2 wheels menggunakan **pandas** dan **plotly**.

            ### Konteks Dataset:
            - Dataset: `df = pd.read_csv('dataset/fix_2w.csv')` (sudah di-load sebelumnya)
            - Kolom: {df.columns.tolist()}
            - Provinsi (`prov`): {df['prov'].unique().tolist()}
            - Kota (`kab`): {df['kab'].unique().tolist()}
            - Tahun (`year`): {df['year'].unique().tolist()}
            - Target utama: `penjualan` (unit)
            - Prediksi: `prediksi` (unit)
            - Kolom numerik: Semua selain `prov`, `kab` (termasuk `cluster` hasil KMeans)
            - Data NaN harus diisi dengan `fillna(0)`

           ### Aturan Wajib:
            1. Jawaban hanya boleh berupa **blok kode Python**, tanpa penjelasan atau komentar apapun.
            2. Jika **pertanyaan TIDAK RELEVAN atau TIDAK DAPAT dijawab** menggunakan dataset tersebut, tampilkan:
            `raise ValueError("Pertanyaan tidak dapat dijawab")`
            3. Jika **pertanyaan DAPAT dijawab**, maka:
            - Gunakan `pandas` untuk manipulasi datanya.
            - Kamu dapat menyesuaikan pertanyaan yang diminta apakah pertanyaan mengharuskan output dataframe atau grafik.
            - Simpan hasil akhir dalam `final_answer` (dalam bentuk DataFrame atau grafik).
            - Jika pertanyaan mengharuskan output grafik, gunakan `plotly` untuk membuat grafik interaktif. dan simpan grafik tersebut ke dalam file JSON 
              dengan format output akhir harus ```final_answer = json.loads(json.dumps(fig.to_plotly_json(), cls=PlotlyJSONEncoder))```.
            - Jika pertanyaan mengharuskan output dataframe, simpan dataframe tersebut ke dalam variabel `final_answer`.
            4. Jangan buat asumsi atau interpolasi data yang tidak ada di dataset.
            5. Jangan mencetak apapun, hanya deklarasi kode

            ### Pertanyaan dari Pengguna:
            **"{text}"**

            ### Tugas Anda:
            Tulis blok kode Python yang valid dan sesuai dengan instruksi di atas.
        """

        generated_code = model.generate_content(contents=prompt).text
        generated_code = clean_code(generated_code)

        save_code(generated_code, f"utils/_generated_code_{uid}.py")
        
        generated_code = read_clean_python_file(filepath)

        logger.info(f"Generated code: {generated_code}")

        local_ns = {'df': df}
        exec(generated_code, {}, local_ns)
        answer_the_code = local_ns.get('final_answer') if 'final_answer' in local_ns else None

        time.sleep(0.03)

        prompt_2 = f"""
            ### Konteks:

            Model menghasilkan kode sebagai respons berikut:  
            {generated_code}

            Output dapat berupa:
            - **DataFrame**: hasil tabular setelah manipulasi data.
            - **String**: nilai hasil akhir atau summary sederhana.
            - **JSON (Plotly Visualisation)**: visualisasi interaktif dari Plotly yang telah dikonversi ke format JSON menggunakan `plotly.io.to_json()`.

            Setelah kode dijalankan, diperoleh hasil output aktual sebagai berikut:  
            {answer_the_code}

            Pengguna mengajukan pertanyaan berikut:  
            **"{text}"**

            ### Konteks Dataset:
            - Fitur: {df.columns.tolist()}
            - Target utama: `penjualan` (unit) -> tidak null untuk tahun 2020 sd 2023 dan null untuk tahun 2024 dan 2025 (karena tahun 2024 dan 2025 adalah data yang hanya ada di `prediksi`)
            - Prediksi: `prediksi` (unit) -> tidak null untuk tahun 2020 sd 2025
            - Error Value: `error_value` -> nilai error dari model yang dilatih sebelumnya -> tidak null untuk tahun 2020 sd 2023 dan null untuk tahun 2024 dan 2025 (karena tahun 2024 dan 2025 adalah data yang hanya ada di `prediksi`)
            - Absolute Percentage Error: `APE` -> selisih dari `prediksi` dan `penjualan` dibagi `penjualan` -> tidak null untuk tahun 2020 sd 2023 dan null untuk tahun 2024 dan 2025
            - Kolom numerik: Semua selain `prov`, `kab` (termasuk `cluster` hasil KMeans)

            ### Tugas Anda:
            - Lakukan **analisis terhadap hasil aktual tersebut** dengan **fokus pada sisi bisnis** (bukan teknis atau algoritmik).
            - Jika hasil berupa visualisasi Plotly (dalam bentuk JSON), bayangkan Anda melihat grafik tersebut lalu berikan interpretasi bisnisnya.
            - **Jangan menjelaskan logika atau algoritma kode**.
            - Soroti **implikasi bisnis, insight, dan dampak nyata** dari hasil tersebut.

            ### Format Jawaban:
            - Berikan jawaban dalam bentuk **poin-poin ringkas dan padat**.
            - Soroti hal-hal yang **penting dengan cetak tebal (bold)**.
            - Fokus pada **kesimpulan dan dampak bisnis** dari hasil tersebut.
            - Berikan **saran atau rekomendasi** jika relevan.

            Jika hasil aktual tidak mengandung informasi bermakna secara bisnis, sampaikan hal itu secara ringkas dan profesional.
        """

        explanation = model_2.generate_content(contents=prompt_2).text.replace("```python", "").replace("```", "").strip()

        formatted_result = ""
        if isinstance(answer_the_code, pd.DataFrame):
            formatted_result += answer_the_code.head(10).to_markdown(index=False, tablefmt="github")
        elif isinstance(answer_the_code, dict):
            blob = bucket.blob(f"users/{user_id}/{uuid.uuid4()}.json")

            json_string = json.dumps(answer_the_code)
            blob.upload_from_string(json_string, content_type="application/json")
            blob.make_public()

            formatted_result = blob.public_url
        else:
            formatted_result += str(answer_the_code)

        return {
            "explanation": f"### Ringkasan Temuan SPLASHBot 🤖:\n\n---\n{explanation}",
            "result": formatted_result,
        }

    except Exception as e:
        logger.error(f"Error in two_wheels_model: {e}")

        fallback_response = model.generate_content(
            contents=f"""
                Kamu tidak dapat memberikan jawaban spesifik dari:

                Pertanyaan: "{text}"
                Kolom DataFrame: {df.columns.tolist()}
                Nama Kota yang ada di DataFrame: {df['kab'].unique().tolist()}
                Nama Provinsi yang ada di DataFrame: {df['prov'].unique().tolist()}

                Namun, kamu bisa memberikan penjelasan/jawaban umum tentang pertanyaan tersebut.
            """
        ).text.replace("```python", "").replace("```", "").strip()

        return {
            "explanation": f"### Maaf, SPLASHBot Belum Dapat Menjawab 😢:\n\n---\n{fallback_response}",
            "result": None,
        }
    
    finally:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            pass
     
def four_wheels_model(text, user_id):
    answer = "Four wheels model masih dalam tahap pengembangan dan belum tersedia untuk digunakan. Silakan coba lagi nanti."
    return {
        "explanation": answer,
        "result": None
    }
    
def retail_general_model(text, user_id):
    answer = "Retail general model masih dalam tahap pengembangan dan belum tersedia untuk digunakan. Silakan coba lagi nanti."
    return {
        "explanation": answer,
        "result": None
    }
    
def retail_beauty_model(text, user_id):
    answer = "Retail beauty model masih dalam tahap pengembangan dan belum tersedia untuk digunakan. Silakan coba lagi nanti."
    return {
        "explanation": answer,
        "result": None
    }
    
def retail_fnb_model(text, user_id):
    answer = "Retail FnB model masih dalam tahap pengembangan dan belum tersedia untuk digunakan. Silakan coba lagi nanti."
    return {
        "explanation": answer,
        "result": None
    }
    
def retail_drugstore_model(text, user_id):
    answer = "Retail drugstore model masih dalam tahap pengembangan dan belum tersedia untuk digunakan. Silakan coba lagi nanti."
    return {
        "explanation": answer,
        "result": None
    }