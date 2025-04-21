import joblib
import pandas as pd
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler

# Load semua
loaded_model = joblib.load('xgb_dropout_model.pkl')
loaded_scaler = joblib.load('scaler.pkl')
selected_columns = joblib.load('selected_features.pkl')

category_mappings = {
    'Gender': {'Male': 1, 'Female': 0},
    'Debtor': {'Yes': 1, 'No': 0},
    'Scholarship_holder': {'Yes': 1, 'No': 0},
    'Tuition_fees_up_to_date': {'Yes': 1, 'No': 0}
}

application_mode_map = {
    1: '1st phase - general', 2: 'Ordinance No. 612/93', 5: '1st phase - Azores',
    7: 'Other higher courses', 10: 'Ordinance No. 854-B/99', 15: 'International (bachelor)',
    16: '1st phase - Madeira', 17: '2nd phase - general', 18: '3rd phase - general',
    26: 'Ordinance No. 533-A/99 b2', 27: 'Ordinance No. 533-A/99 b3',
    39: 'Over 23 years old', 42: 'Transfer', 43: 'Change of course',
    44: 'Tech diploma holders', 51: 'Change inst/course', 53: 'Short cycle diploma',
    57: 'Change inst/course (Intl)'
}

def convert_input(user_input, mappings):
    converted = user_input.copy()
    for col, mapping in mappings.items():
        if col in user_input:
            converted[col] = mapping.get(user_input[col], user_input[col])
    return converted

# Ambil input dari user
new_student = {
    'Application_mode': input("Masukkan Application Mode (kategorik): "),
    'Debtor': input("Apakah mahasiswa memiliki utang? (Yes/No): "),
    'Tuition_fees_up_to_date': input("Apakah biaya kuliah sudah dibayar? (Yes/No): "),
    'Gender': input("Jenis Kelamin (Male/Female): "),
    'Scholarship_holder': input("Apakah penerima beasiswa? (Yes/No): "),
    'Age_at_enrollment': float(input("Usia saat mendaftar: ")),
    'Curricular_units_1st_sem_approved': int(input("Jumlah mata kuliah lulus semester 1: ")),
    'Curricular_units_1st_sem_grade': float(input("Rata-rata nilai semester 1: ")),
    'Curricular_units_2nd_sem_approved': int(input("Jumlah mata kuliah lulus semester 2: ")),
    'Curricular_units_2nd_sem_grade': float(input("Rata-rata nilai semester 2: "))
}

# Konversi input kategori ke numerik
converted_input = convert_input(new_student, category_mappings)

# Ubah ke DataFrame
input_df = pd.DataFrame([converted_input])

input_df['Application_mode'] = input_df['Application_mode'].map(application_mode_map)

# Scaling sesuai training
input_scaled = loaded_scaler.transform(input_df)  # pakai kolom fitur terpilih

# Prediksi
prediction = loaded_model.predict(input_scaled)[0]
probabilities = loaded_model.predict_proba(input_scaled)[0]
label = 'Dropout' if prediction == 1 else 'Graduate'

# Ambil probabilitas untuk kelas yang diprediksi (Dropout jika prediksi = 1, Graduate jika prediksi = 0)
predicted_prob = probabilities[prediction]  # Ambil probabilitas kelas yang diprediksi

# Tampilkan hasil prediksi dan probabilitas untuk kelas yang diprediksi
print(f"Prediksi: {label} ({predicted_prob * 100:.2f}%)")