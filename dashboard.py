import streamlit as st
import joblib, requests, tempfile, re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler

# Set page config
st.set_page_config(page_title="Student Dropout Dashboard", layout="wide")

# Load dataset
df = pd.read_csv("https://raw.githubusercontent.com/dicodingacademy/dicoding_dataset/refs/heads/main/students_performance/data.csv", sep=";")

# Unduh file dari URL
url = "https://github.com/Alqurtubi17/pds-hr/raw/refs/heads/main/Klasifikasi%20Dropout/model_pipeline.pkl"
response = requests.get(url)
if response.status_code == 200:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(response.content)
        tmp_file_path = tmp_file.name

    # Load model
    pipeline = joblib.load(tmp_file_path)
    model = pipeline['model']
    scaler = pipeline['scaler']
    selected_features = pipeline['selected_features']
else:
    raise Exception("Gagal mengunduh file model dari GitHub.")

# model, scaler, selected_features = joblib.load("model_pipeline.pkl")
# Preprocessing
def format_column(col):
    # Replace underscores with space and title case
    col = col.replace('_', ' ').title()
    # Perbaiki kapitalisasi ordinal
    col = re.sub(r'\b1St\b', '1st', col)
    col = re.sub(r'\b2Nd\b', '2nd', col)
    col = re.sub(r'\b3Rd\b', '3rd', col)
    col = re.sub(r'\b(\d+)Th\b', lambda m: f"{m.group(1)}th", col)
    return col

# Ambil data hanya dengan label Dropout dan Graduate
df_corr = df.copy()
df_corr = df_corr[df_corr['Status'].isin(['Dropout', 'Graduate'])]
df_corr['Status'] = df_corr['Status'].map({'Dropout': 1, 'Graduate': 0})

# Mapping
application_mode_map = {
    1: '1st phase - general', 2: 'Ordinance No. 612/93', 5: '1st phase - Azores',
    7: 'Other higher courses', 10: 'Ordinance No. 854-B/99', 15: 'International (bachelor)',
    16: '1st phase - Madeira', 17: '2nd phase - general', 18: '3rd phase - general',
    26: 'Ordinance No. 533-A/99 b2', 27: 'Ordinance No. 533-A/99 b3',
    39: 'Over 23 years old', 42: 'Transfer', 43: 'Change of course',
    44: 'Tech diploma holders', 51: 'Change inst/course', 53: 'Short cycle diploma',
    57: 'Change inst/course (Intl)'
}

binomial_mapping = {
    'Gender': {1: 'Male', 0: 'Female'},
    'Debtor': {0: 'No', 1: 'Yes'},
    'Tuition_fees_up_to_date': {0: 'No', 1: 'Yes'},
    'Scholarship_holder': {0: 'No', 1: 'Yes'},
    'International': {0: 'No', 1: 'Yes'},
    'Displaced': {0: 'No', 1: 'Yes'},
    'Educational_special_needs': {0: 'No', 1: 'Yes'},
}

# Menggunakan pemetaan
for col, mapping in binomial_mapping.items():
    df[col] = df[col].map(mapping)

# Terapkan mapping
df['Application_mode'] = df['Application_mode'].map(application_mode_map)

# Sidebar navigation
page = st.sidebar.selectbox("Pilih Halaman", ["Dashboard", "Prediction"])

# ==== Halaman Dashboard
if page == "Dashboard":
    st.markdown("<h2 style='text-align:center; margin-top:0px; margin-bottom:30px'>Student Dropout Dashboard</h2>", unsafe_allow_html=True)

    # Metrics
    status_counts = df['Status'].value_counts()
    total_students = len(df)
    total_dropout = status_counts.get('Dropout', 0)
    total_graduate = status_counts.get('Graduate', 0)
    percent_dropout = (total_dropout / total_students) * 100
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div style='background-color:#FDFAF6; padding:15px; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,0.1); text-align:center;'>" +
                    f"<h5>Total Students</h5><h3>{total_students}</h3></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='background-color:#FDFAF6; padding:15px; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,0.1); text-align:center;'>" +
                    f"<h5>Total Dropout</h5><h3>{total_dropout}</h3></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='background-color:#FDFAF6; padding:15px; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,0.1); text-align:center;'>" +
                    f"<h5>Dropout Rate</h5><h3>{percent_dropout:.2f}%</h3></div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div style='background-color:#FDFAF6; padding:15px; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,0.1); text-align:center;'>" +
                    f"<h5>Total Graduates</h5><h3>{total_graduate}</h3></div>", unsafe_allow_html=True)

    st.markdown("")
    # Feature Importance + Pie Chart
    col_pie, col_feat = st.columns([1, 3])

    with col_feat:
        X = df[['Application_mode', 'Debtor', 'Tuition_fees_up_to_date', 'Gender', 'Scholarship_holder', 'Age_at_enrollment', 'Curricular_units_1st_sem_approved', 'Curricular_units_1st_sem_grade', 'Curricular_units_2nd_sem_approved', 'Curricular_units_2nd_sem_grade']]
        feat_imp = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
        fig_feat = px.bar(
            feat_imp,
            x=feat_imp.index,
            y=feat_imp.values,
            labels={'index': 'Feature', 'y': 'Importance'},
            title="Key Factors Contributing to Dropout Rate",
            color_discrete_sequence=["#A0C4FF"]
        )
        fig_feat.update_traces(textposition='outside')
        fig_feat.update_layout(
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            title=dict(x=0.3),
            showlegend=False
        )
        st.plotly_chart(fig_feat, use_container_width=True)

    with col_pie:
        pie_data = df['Status'].value_counts().reset_index()
        pie_data.columns = ['Status', 'Count']
        fig_pie = px.pie(pie_data, names='Status', values='Count', title="Status Ratio", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            title=dict(x=0.3))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("<h6 style='text-align:center;'>Dropout Comparison by Categorical Features</h6>", unsafe_allow_html=True)
    fig_cat = make_subplots(rows=2, cols=3, subplot_titles=('Gender', 'Debtor', 'Tuition Fees up to Date',
                                                            'Scholarship Holder', 'International', 'Displaced'))
    categorical_features = ['Gender', 'Debtor', 'Tuition_fees_up_to_date', 'Scholarship_holder',
                            'International', 'Displaced']
    for idx, col in enumerate(categorical_features):
        row = idx // 3 + 1
        column = idx % 3 + 1

        # Hitung rasio attrition Yes per kategori
        grouped = df.groupby([col, 'Status']).size().reset_index(name='Count')
        total_per_group = grouped.groupby(col)['Count'].transform('sum')
        grouped['Ratio'] = grouped['Count'] / total_per_group * 100

        do_df = grouped[grouped['Status'] == 'Dropout'].sort_values(by='Ratio', ascending=False)

        fig_cat.add_trace(
            go.Bar(
                x=do_df[col],
                y=do_df['Ratio'],
                name='Status Dropout',
                text=do_df['Ratio'].round(1).astype(str) + '%',
                textposition='auto',
                marker_color="#89C2D9"
            ),
            row=row, col=column
        )

        fig_cat.update_xaxes(showgrid=False, row=row, col=column)
        fig_cat.update_yaxes(title_text='%', showgrid=False, row=row, col=column)

    fig_cat.update_layout(
        height=650,
        width=1400,
        showlegend=False,
        margin=dict(t=50),
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    col1, col2 = st.columns([1.5, 1])
    with col2:
        relevant_numerics = [
            'Application_order', 'Previous_qualification_grade', 'Admission_grade', 'Age_at_enrollment', 'Curricular_units_1st_sem_credited',
           'Curricular_units_1st_sem_enrolled', 'Curricular_units_1st_sem_evaluations', 'Curricular_units_1st_sem_approved', 'Curricular_units_1st_sem_grade',
           'Curricular_units_1st_sem_without_evaluations', 'Curricular_units_2nd_sem_credited', 'Curricular_units_2nd_sem_enrolled', 'Curricular_units_2nd_sem_evaluations',
           'Curricular_units_2nd_sem_approved', 'Curricular_units_2nd_sem_grade', 'Curricular_units_2nd_sem_without_evaluations', 'Unemployment_rate', 'Inflation_rate', 'GDP']
        
        # Buat mapping: tampilan di dropdown → nama kolom asli
        display_to_column = {format_column(col): col for col in relevant_numerics}
        display_names = list(display_to_column.keys())

        st.markdown("<h6 style='text-align:center;'>Key Student Dropout Variable Analysis</h6>", unsafe_allow_html=True)

        # Tampilkan nama yang sudah diformat
        selected_display = st.selectbox("Select Variable", display_names)

        # Ambil nama kolom asli dari mapping
        selected_column = display_to_column[selected_display]

        fig = px.box(
            df,
            x='Status',
            y=selected_column,
            color='Status',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

        fig.update_layout(
            yaxis_title=selected_display, 
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col1:
        # Correlation Heatmap
        st.markdown("<h6 style='text-align:center; font-size:18px;'>Correlation between Numerical Features</h6>", unsafe_allow_html=True)

        # Hitung korelasi
        corr_series = df_corr.drop(columns='Status').corrwith(df_corr['Status']).sort_values(key=lambda x: abs(x), ascending=True)

        # Format label y (fitur) agar tampil rapi
        formatted_index = [format_column(col) for col in corr_series.index]

        # Buat bar chart horizontal
        fig_corr_bar = px.bar(
            x=corr_series.values,
            y=formatted_index,
            orientation='h',
            text=corr_series.round(2),
            color=corr_series.values,
            color_continuous_scale=px.colors.qualitative.Pastel,
            labels={'x': 'Correlation', 'y': 'Feature'}
        )

        fig_corr_bar.update_layout(
            yaxis=dict(showgrid=False),
            xaxis=dict(showgrid=False)
        )

        st.plotly_chart(fig_corr_bar, use_container_width=True)

# ==== Halaman Prediksi ====
elif page == "Prediction":
    st.markdown("<h2 style='text-align:center; margin-top:0px; margin-bottom:30px'>🔮 Predict Student Status</h2>", unsafe_allow_html=True)
    with st.form("prediction_form"):
        st.markdown("<h3 style='text-align:center;'>📥 Formulir Data Mahasiswa</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("Gender", options=['Male', 'Female'])
            age = st.number_input("Age at Enrollment", min_value=15, max_value=60, value=20)
            debtor = st.selectbox("Debtor", options=['Yes', 'No'])
            scholarship = st.selectbox("Scholarship Holder", options=['Yes', 'No'])
            tuition_paid = st.selectbox("Tuition Fees Up To Date", options=['Yes', 'No'])
        with col2:
            app_mode = st.selectbox("Application Mode", options=list(application_mode_map.keys()), format_func=lambda x: application_mode_map[x])
            first_sem_approved = st.number_input("Units Approved (Sem 1)", min_value=0, value=5)
            first_sem_grade = st.number_input("Grade (Sem 1)", min_value=0.0, max_value=20.0, value=10.0)
            second_sem_approved = st.number_input("Units Approved (Sem 2)", min_value=0, value=5)
            second_sem_grade = st.number_input("Grade (Sem 2)", min_value=0.0, max_value=20.0, value=10.0)

        submit = st.form_submit_button("🔮 Predict Now")

        if submit:
            input_dict = {
                'Gender': 1 if gender == 'Male' else 0,
                'Age_at_enrollment': age,
                'Debtor': 1 if debtor == 'Yes' else 0,
                'Scholarship_holder': 1 if scholarship == 'Yes' else 0,
                'Tuition_fees_up_to_date': 1 if tuition_paid == 'Yes' else 0,
                'Application_mode': app_mode,
                'Curricular_units_1st_sem_approved': first_sem_approved,
                'Curricular_units_1st_sem_grade': first_sem_grade,
                'Curricular_units_2nd_sem_approved': second_sem_approved,
                'Curricular_units_2nd_sem_grade': second_sem_grade
            }
            input_df = pd.DataFrame([input_dict])
            input_scaled = scaler.transform(input_df[selected_features])
            pred = model.predict(input_scaled)[0]
            prob = model.predict_proba(input_scaled)[0][pred]
            label = "Dropout" if pred == 1 else "Graduate"

            # Ganti warna teks berdasarkan prediksi
            if label == "Dropout":
                st.error(f"🎓 Hasil Prediksi: **{label}** dengan probabilitas {prob*100:.2f}%")
            else:
                st.success(f"🎓 Hasil Prediksi: **{label}** dengan probabilitas {prob*100:.2f}%")
            