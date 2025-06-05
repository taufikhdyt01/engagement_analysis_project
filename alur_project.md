## Alur Project

### **FASE 1: Baseline dengan Face API**

**1.1 Data Preparation**

- Gunakan data Face API yang sudah Anda miliki sebagai **ground truth awal**
- Implementasi scoring engagement menggunakan bobot dari paper
- Analisis distribusi engagement level pada 20 mahasiswa Anda

**1.2 Engagement Scoring**

- Terapkan formula weighted average dari paper
- Klasifikasi menjadi 3 level: Disengaged, Engaged, Highly Engaged
- Analisis pola engagement per mahasiswa dan per studi kasus

### **FASE 2: CNN Pre-training (Data Sekunder)**

**2.1 Pilihan Dataset Sekunder**
Anda **PERLU** pre-training dengan dataset sekunder karena:

- Data primer Anda (20 mahasiswa) terlalu kecil untuk training CNN dari nol
- CNN butuh ribuan sampel untuk generalisasi yang baik

**Opsi Dataset:**

- **FER2013** - 30K+ gambar, 7 emosi

**2.2 Pre-training Process**

```
Dataset Sekunder → CNN Training → Pre-trained Model
                     ↓
               Transfer Learning Base
```

**2.3 Architecture Design**

- Gunakan lightweight CNN seperti di paper
- Input: 48x48 grayscale (sesuai standar FER)
- Output: 7 emotion classes
- Optimizer: Adam (sesuai paper)

### **FASE 3: Fine-tuning dengan Data Primer**

**3.1 Data Preparation Primer**

- Ekstrak frames dari video Anda (setiap 5 detik)
- Crop dan resize faces menjadi 48x48
- Label dengan hasil Face API sebagai **pseudo-labels**
- Split data: 70% fine-tuning, 30% validation

**3.2 Transfer Learning**

```
Pre-trained CNN → Remove last layer → Add new classifier → Fine-tune
                                           ↓
                              Fine-tune dengan data programming context
```

**3.3 Domain Adaptation**

- Fine-tune model untuk konteks pembelajaran programming
- Adjust untuk pencahayaan/environment ruang belajar Anda
- Pembelajaran pola emosi spesifik programming challenges

### **FASE 4: Hybrid Validation & Integration**

**4.1 Cross-Validation**

- Bandingkan hasil Face API vs Fine-tuned CNN
- Hitung correlation coefficient antara kedua metode
- Identifikasi di mana CNN memberikan improvement

**4.2 Weighted Ensemble**

```
Final Prediction = α × Face_API_Result + β × CNN_Result
```

Di mana α + β = 1, dan bobot ditentukan berdasarkan:

- Confidence score masing-masing metode
- Historical accuracy pada validation set
- Contextual factors (lighting, angle, etc.)

**4.3 Engagement Score Refinement**

- Recalibrate bobot engagement berdasarkan hasil hybrid
- Sesuaikan threshold classification untuk konteks programming
- Validasi dengan observasi manual

### **FASE 5: Deployment & Monitoring**

**5.1 Production Pipeline**

```
Video Frame → Face Detection → Emotion Extraction → Engagement Scoring
                ↓                    ↓                     ↓
           MTCNN/OpenCV    Face API + Fine-tuned CNN    Weighted Formula
```

**5.2 Continuous Learning**

- Collect feedback dari educator
- Periodic re-validation dengan sample baru
- Update model jika diperlukan

## Keuntungan Hybrid Approach

**✅ Strengths:**

- **Robust**: Dua metode saling validasi
- **Efficient**: Face API untuk real-time, CNN untuk refinement
- **Adaptive**: Bisa disesuaikan dengan konteks programming
- **Scalable**: Model bisa improve dengan data baru

**⚠️ Considerations:**

- Butuh komputasi lebih untuk training CNN
- Complexity lebih tinggi dibanding Face API saja
- Perlu careful tuning untuk balance kedua metode

## 🚀 Roadmap Sprint Semalam (8-10 jam)

### **Setup & Baseline Face API**

- Download FER2013 dataset
- Setup environment (TensorFlow, OpenCV, pandas)
- Load data Excel Anda
- Implementasi scoring engagement dengan formula paper
- Quick analysis distribusi engagement 20 mahasiswa

### **Pre-training CNN dengan FER2013**

- Load FER2013 (30K+ images, 48x48)
- Build lightweight CNN architecture (sama persis seperti paper)
- Training dengan Adam optimizer
- **Target**: Accuracy ~70-80% (cukup untuk transfer learning)

### **Data Preparation & Fine-tuning**

- Ekstrak frames dari video Anda
- Crop faces dengan MTCNN/OpenCV
- Prepare labels dari Face API results
- Fine-tune pre-trained model dengan data Anda

### **Hybrid Implementation & Validation**

- Ensemble Face API + Fine-tuned CNN
- Cross-validation dengan sample manual
- Generate final engagement predictions
- Visualisasi results

### **Analysis & Report**

- Confusion matrix seperti paper
- Accuracy metrics comparison
- Temporal engagement analysis
- Export results & visualizations
