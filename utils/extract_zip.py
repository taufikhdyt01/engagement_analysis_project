import zipfile
import os
import sys
from pathlib import Path

def extract_zip_basic(zip_path, extract_to=None):
    """
    Ekstraksi ZIP sederhana
    
    Args:
        zip_path (str): Path ke file ZIP
        extract_to (str): Folder tujuan ekstraksi (opsional)
    """
    try:
        # Jika tidak ada folder tujuan, gunakan folder saat ini
        if extract_to is None:
            extract_to = os.getcwd()
        
        # Pastikan folder tujuan ada
        os.makedirs(extract_to, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            
        print(f"✅ Berhasil mengekstrak {zip_path} ke {extract_to}")
        
    except FileNotFoundError:
        print(f"❌ File {zip_path} tidak ditemukan!")
    except zipfile.BadZipFile:
        print(f"❌ File {zip_path} bukan file ZIP yang valid!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def extract_zip_advanced(zip_path, extract_to=None, password=None, show_progress=True):
    """
    Ekstraksi ZIP dengan fitur advanced
    
    Args:
        zip_path (str): Path ke file ZIP
        extract_to (str): Folder tujuan ekstraksi
        password (str): Password jika ZIP terproteksi
        show_progress (bool): Tampilkan progress ekstraksi
    """
    try:
        # Setup folder tujuan
        if extract_to is None:
            zip_name = Path(zip_path).stem
            extract_to = os.path.join(os.getcwd(), zip_name)
        
        os.makedirs(extract_to, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Cek jika ZIP terproteksi password
            if password:
                zip_ref.setpassword(password.encode())
            
            # Dapatkan list file dalam ZIP
            file_list = zip_ref.namelist()
            total_files = len(file_list)
            
            print(f"📦 Mengekstrak {total_files} file dari {zip_path}")
            print(f"📁 Tujuan: {extract_to}")
            
            # Ekstrak file satu per satu dengan progress
            for i, file_name in enumerate(file_list, 1):
                try:
                    zip_ref.extract(file_name, extract_to)
                    
                    if show_progress:
                        progress = (i / total_files) * 100
                        print(f"\r⏳ Progress: {progress:.1f}% ({i}/{total_files}) - {file_name[:50]}{'...' if len(file_name) > 50 else ''}", end='')
                        
                except Exception as e:
                    print(f"\n⚠️  Gagal mengekstrak {file_name}: {str(e)}")
            
            if show_progress:
                print("\n✅ Ekstraksi selesai!")
                
    except zipfile.BadZipFile:
        print(f"❌ File {zip_path} bukan file ZIP yang valid!")
    except RuntimeError as e:
        if "password required" in str(e).lower():
            print("❌ ZIP file memerlukan password!")
        elif "bad password" in str(e).lower():
            print("❌ Password salah!")
        else:
            print(f"❌ Runtime error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def list_zip_contents(zip_path, show_details=False):
    """
    Tampilkan isi file ZIP tanpa mengekstrak
    
    Args:
        zip_path (str): Path ke file ZIP
        show_details (bool): Tampilkan detail ukuran file
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            print(f"📦 Isi file ZIP: {zip_path}")
            print(f"📊 Total file: {len(file_list)}")
            print("-" * 50)
            
            if show_details:
                print(f"{'Nama File':<40} {'Ukuran':<10} {'Compressed':<10}")
                print("-" * 65)
                
                total_size = 0
                total_compressed = 0
                
                for file_info in zip_ref.infolist():
                    if not file_info.is_dir():
                        total_size += file_info.file_size
                        total_compressed += file_info.compress_size
                        
                        print(f"{file_info.filename:<40} {file_info.file_size:<10} {file_info.compress_size:<10}")
                
                print("-" * 65)
                print(f"{'TOTAL':<40} {total_size:<10} {total_compressed:<10}")
                print(f"Rasio kompresi: {(1 - total_compressed/total_size)*100:.1f}%")
            else:
                for file_name in file_list:
                    print(f"📄 {file_name}")
                    
    except zipfile.BadZipFile:
        print(f"❌ File {zip_path} bukan file ZIP yang valid!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def extract_specific_files(zip_path, file_patterns, extract_to=None):
    """
    Ekstrak file tertentu saja dari ZIP
    
    Args:
        zip_path (str): Path ke file ZIP
        file_patterns (list): List pattern nama file yang ingin diekstrak
        extract_to (str): Folder tujuan ekstraksi
    """
    try:
        if extract_to is None:
            extract_to = os.getcwd()
            
        os.makedirs(extract_to, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            all_files = zip_ref.namelist()
            extracted_count = 0
            
            for pattern in file_patterns:
                matching_files = [f for f in all_files if pattern.lower() in f.lower()]
                
                for file_name in matching_files:
                    zip_ref.extract(file_name, extract_to)
                    print(f"✅ Diekstrak: {file_name}")
                    extracted_count += 1
            
            print(f"📊 Total file diekstrak: {extracted_count}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def batch_extract_zips(zip_folder, extract_base_folder=None):
    """
    Ekstrak semua file ZIP dalam folder
    
    Args:
        zip_folder (str): Folder yang berisi file-file ZIP
        extract_base_folder (str): Folder dasar untuk ekstraksi
    """
    try:
        if extract_base_folder is None:
            extract_base_folder = os.path.join(zip_folder, "extracted")
            
        os.makedirs(extract_base_folder, exist_ok=True)
        
        zip_files = [f for f in os.listdir(zip_folder) if f.lower().endswith('.zip')]
        
        if not zip_files:
            print(f"❌ Tidak ada file ZIP ditemukan di {zip_folder}")
            return
            
        print(f"📦 Ditemukan {len(zip_files)} file ZIP")
        
        for i, zip_file in enumerate(zip_files, 1):
            zip_path = os.path.join(zip_folder, zip_file)
            extract_folder = os.path.join(extract_base_folder, Path(zip_file).stem)
            
            print(f"\n[{i}/{len(zip_files)}] Mengekstrak: {zip_file}")
            extract_zip_advanced(zip_path, extract_folder, show_progress=False)
            
        print(f"\n✅ Semua file ZIP berhasil diekstrak ke {extract_base_folder}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Contoh penggunaan
if __name__ == "__main__":
    # Contoh penggunaan berbagai fungsi
    
    print("=== EKSTRAKSI FILE ZIP ===\n")
    
    # 1. Ekstraksi sederhana
    # extract_zip_basic("example.zip", "output_folder")
    
    # 2. Ekstraksi dengan progress dan fitur advanced
    # extract_zip_advanced("example.zip", "output_advanced", show_progress=True)
    
    # 3. Ekstraksi ZIP dengan password
    # extract_zip_advanced("protected.zip", "output_protected", password="mypassword")
    
    # 4. Lihat isi ZIP tanpa ekstraksi
    # list_zip_contents("example.zip", show_details=True)
    
    # 5. Ekstrak file tertentu saja
    # extract_specific_files("example.zip", [".pdf", ".txt", "important"], "selected_files")
    
    # 6. Ekstrak semua ZIP dalam folder
    # batch_extract_zips("zip_files_folder", "extracted_all")
    
    # Interactive mode
    print("Mode Interaktif:")
    print("1. Ekstrak ZIP")
    print("2. Lihat isi ZIP")
    print("3. Ekstrak file tertentu")
    print("4. Ekstrak semua ZIP dalam folder")
    
    try:
        choice = input("\nPilih opsi (1-4): ").strip()
        
        if choice == "1":
            zip_path = input("Masukkan path file ZIP: ").strip()
            extract_to = input("Folder tujuan (kosong untuk folder saat ini): ").strip()
            password = input("Password (kosong jika tidak ada): ").strip()
            
            if not extract_to:
                extract_to = None
            if not password:
                password = None
                
            extract_zip_advanced(zip_path, extract_to, password)
            
        elif choice == "2":
            zip_path = input("Masukkan path file ZIP: ").strip()
            show_details = input("Tampilkan detail? (y/n): ").strip().lower() == 'y'
            list_zip_contents(zip_path, show_details)
            
        elif choice == "3":
            zip_path = input("Masukkan path file ZIP: ").strip()
            patterns = input("Masukkan pattern file (pisah dengan koma): ").strip().split(',')
            patterns = [p.strip() for p in patterns]
            extract_to = input("Folder tujuan (kosong untuk folder saat ini): ").strip()
            
            if not extract_to:
                extract_to = None
                
            extract_specific_files(zip_path, patterns, extract_to)
            
        elif choice == "4":
            zip_folder = input("Masukkan path folder berisi ZIP: ").strip()
            extract_base = input("Folder dasar ekstraksi (kosong untuk auto): ").strip()
            
            if not extract_base:
                extract_base = None
                
            batch_extract_zips(zip_folder, extract_base)
            
        else:
            print("❌ Pilihan tidak valid!")
            
    except KeyboardInterrupt:
        print("\n\n👋 Program dihentikan oleh user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")