import cv2
import pandas as pd
import os
import numpy as np
from datetime import datetime
import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
from collections import defaultdict

class GPUVideoFrameExtractor:
    def __init__(self, excel_file_path, video_folder_path, output_folder_path, use_gpu=True, max_workers=None):
        """
        Initialize GPU-accelerated VideoFrameExtractor
        
        Args:
            excel_file_path (str): Path to Excel file containing emotion data
            video_folder_path (str): Path to folder containing video files
            output_folder_path (str): Path to folder where extracted frames will be saved
            use_gpu (bool): Whether to use GPU acceleration
            max_workers (int): Number of parallel workers
        """
        self.excel_file_path = excel_file_path
        self.video_folder_path = video_folder_path
        self.output_folder_path = output_folder_path
        self.use_gpu = use_gpu
        self.max_workers = max_workers or mp.cpu_count()
        
        # Create output folder if it doesn't exist
        Path(self.output_folder_path).mkdir(parents=True, exist_ok=True)
        
        # Page mapping
        self.page_mapping = {
            '/tantangan/penjumlahan-dua-angka': 'challenge1',
            '/tantangan/status-http': 'challenge2'
        }
        
        # Check GPU availability
        self.gpu_available = self.check_gpu_support()
        if use_gpu and not self.gpu_available:
            print("Warning: GPU acceleration requested but not available, falling back to CPU")
            self.use_gpu = False
    
    def check_gpu_support(self):
        """Check if GPU acceleration is available"""
        try:
            # Check if OpenCV was compiled with CUDA support
            if hasattr(cv2, 'cuda'):
                count = cv2.cuda.getCudaEnabledDeviceCount()
                if count > 0:
                    print(f"GPU acceleration available: {count} CUDA device(s) found")
                    return True
            
            print("GPU acceleration not available (OpenCV not compiled with CUDA)")
            return False
        except:
            print("GPU acceleration not available")
            return False
    
    def load_excel_data(self):
        """Load and process Excel data"""
        try:
            df = pd.read_excel(self.excel_file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d/%m/%Y %H:%M:%S')
            return df
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            return None
    
    def group_records_by_video(self, df):
        """Group records by video file to minimize video loading"""
        video_groups = defaultdict(list)
        
        for index, row in df.iterrows():
            user_id = row['user_id']
            timestamp = row['timestamp']
            
            video_path = self.find_video_file(user_id, timestamp)
            if video_path:
                video_groups[video_path].append({
                    'index': index,
                    'user_id': user_id,
                    'timestamp': timestamp,
                    'page': row['page']
                })
        
        return dict(video_groups)
    
    def find_video_file(self, user_id, timestamp):
        """Find the corresponding video file for a user and timestamp"""
        date_str = timestamp.strftime('%Y-%m-%d')
        hour_str = timestamp.strftime('%H')
        
        patterns = [
            f"user{user_id}-{date_str} {hour_str}-*.mp4",
            f"user{user_id}-{date_str} {hour_str}-*.mkv"
        ]
        
        for pattern in patterns:
            search_path = os.path.join(self.video_folder_path, pattern)
            matches = glob.glob(search_path)
            if matches:
                return matches[0]
        
        # Find closest match
        video_files = glob.glob(os.path.join(self.video_folder_path, f"user{user_id}-{date_str}*.mp4"))
        video_files.extend(glob.glob(os.path.join(self.video_folder_path, f"user{user_id}-{date_str}*.mkv")))
        
        if video_files:
            return video_files[0]
        
        return None
    
    def extract_video_start_time(self, video_filename):
        """Extract start time from video filename"""
        try:
            basename = os.path.basename(video_filename)
            time_part = basename.split('-', 1)[1].rsplit('.', 1)[0]
            video_start = datetime.strptime(time_part, '%Y-%m-%d %H-%M-%S')
            return video_start
        except Exception as e:
            print(f"Error parsing video filename {video_filename}: {e}")
            return None
    
    def generate_output_filename(self, user_id, timestamp, page):
        """Generate output filename for extracted frame"""
        challenge = self.page_mapping.get(page, 'challenge_unknown')
        time_str = timestamp.strftime('%H%M%S')
        filename = f"user{user_id}_{challenge}_time{time_str}.jpg"
        return filename
    
    def extract_frames_opencv_gpu(self, video_path, records, video_start_time):
        """Extract frames using OpenCV with GPU acceleration"""
        try:
            # Open video with GPU decoder if available
            if self.use_gpu and self.gpu_available:
                cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
                # Try to enable hardware acceleration
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))
            else:
                cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return [(False, f"Could not open video: {video_path}") for _ in records]
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # Default fallback
            
            results = []
            
            # Sort records by timestamp for efficient seeking
            sorted_records = sorted(records, key=lambda x: x['timestamp'])
            
            for record in sorted_records:
                timestamp = record['timestamp']
                time_offset = (timestamp - video_start_time).total_seconds()
                
                if time_offset < 0:
                    results.append((False, "Timestamp before video start"))
                    continue
                
                # Calculate frame number
                frame_number = int(time_offset * fps)
                
                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                
                ret, frame = cap.read()
                if not ret:
                    results.append((False, f"Could not read frame at {time_offset}s"))
                    continue
                
                # Generate output path
                output_filename = self.generate_output_filename(
                    record['user_id'], record['timestamp'], record['page']
                )
                output_path = os.path.join(self.output_folder_path, output_filename)
                
                # Save frame
                if cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                    results.append((True, output_path))
                    print(f"✓ Extracted: {os.path.basename(output_path)}")
                else:
                    results.append((False, f"Could not save frame to {output_path}"))
            
            cap.release()
            return results
            
        except Exception as e:
            return [(False, str(e)) for _ in records]
    
    def extract_frames_memory_efficient(self, video_path, records, video_start_time):
        """Memory-efficient frame extraction using frame skipping"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return [(False, f"Could not open video: {video_path}") for _ in records]
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps <= 0:
                fps = 30
            
            results = []
            
            # Group records by second to minimize seeking
            time_groups = defaultdict(list)
            for record in records:
                time_offset = (record['timestamp'] - video_start_time).total_seconds()
                if time_offset >= 0:
                    second = int(time_offset)
                    time_groups[second].append((time_offset, record))
            
            # Process each second group
            for second in sorted(time_groups.keys()):
                if second * fps >= total_frames:
                    for _, record in time_groups[second]:
                        results.append((False, "Frame beyond video duration"))
                    continue
                
                # Seek to the second
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(second * fps))
                
                # Read a few frames around this second
                frames_buffer = []
                for i in range(int(fps) + 1):  # Read 1 second worth of frames
                    ret, frame = cap.read()
                    if ret:
                        frames_buffer.append((second + i/fps, frame))
                    else:
                        break
                
                # Extract the closest frame for each record in this second
                for time_offset, record in time_groups[second]:
                    closest_frame = None
                    min_diff = float('inf')
                    
                    for frame_time, frame in frames_buffer:
                        diff = abs(frame_time - time_offset)
                        if diff < min_diff:
                            min_diff = diff
                            closest_frame = frame
                    
                    if closest_frame is not None:
                        output_filename = self.generate_output_filename(
                            record['user_id'], record['timestamp'], record['page']
                        )
                        output_path = os.path.join(self.output_folder_path, output_filename)
                        
                        if cv2.imwrite(output_path, closest_frame, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                            results.append((True, output_path))
                            print(f"✓ Extracted: {os.path.basename(output_path)}")
                        else:
                            results.append((False, f"Could not save frame"))
                    else:
                        results.append((False, f"No frame found for timestamp"))
            
            cap.release()
            return results
            
        except Exception as e:
            return [(False, str(e)) for _ in records]
    
    def process_video_group(self, args):
        """Process a group of records from the same video"""
        video_path, records = args
        
        video_start_time = self.extract_video_start_time(video_path)
        if not video_start_time:
            return [(False, "Could not parse video start time") for _ in records]
        
        print(f"Processing {len(records)} frames from {os.path.basename(video_path)}")
        
        # Choose extraction method based on number of records
        if len(records) > 10:
            # Use memory-efficient method for many frames
            return self.extract_frames_memory_efficient(video_path, records, video_start_time)
        else:
            # Use GPU method for few frames
            return self.extract_frames_opencv_gpu(video_path, records, video_start_time)
    
    def process_all_records(self):
        """Process all records using the fastest available method"""
        df = self.load_excel_data()
        if df is None:
            return
        
        print(f"Processing {len(df)} records...")
        print(f"GPU acceleration: {'Enabled' if self.use_gpu and self.gpu_available else 'Disabled'}")
        
        # Group records by video
        video_groups = self.group_records_by_video(df)
        print(f"Found {len(video_groups)} unique videos")
        
        successful_extractions = 0
        failed_extractions = 0
        
        # Use ThreadPoolExecutor for I/O bound operations
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(video_groups))) as executor:
            # Process video groups in parallel
            args_list = list(video_groups.items())
            
            all_results = executor.map(self.process_video_group, args_list)
            
            # Collect results
            for results in all_results:
                for success, message in results:
                    if success:
                        successful_extractions += 1
                    else:
                        failed_extractions += 1
                        if not success and "Extracted:" not in str(message):
                            print(f"✗ {message}")
        
        print(f"\n=== SUMMARY ===")
        print(f"Total records processed: {len(df)}")
        print(f"Successful extractions: {successful_extractions}")
        print(f"Failed extractions: {failed_extractions}")
        print(f"Output folder: {self.output_folder_path}")

def check_system_capabilities():
    """Check system capabilities for optimal performance"""
    print("=== SYSTEM CAPABILITIES ===")
    
    # Check CPU cores
    cpu_cores = mp.cpu_count()
    print(f"CPU cores: {cpu_cores}")
    
    # Check OpenCV build info
    print(f"OpenCV version: {cv2.__version__}")
    
    # Check CUDA support
    try:
        if hasattr(cv2, 'cuda'):
            cuda_devices = cv2.cuda.getCudaEnabledDeviceCount()
            print(f"CUDA devices: {cuda_devices}")
        else:
            print("CUDA: Not available")
    except:
        print("CUDA: Not available")
    
    # Memory recommendation
    import psutil
    memory_gb = psutil.virtual_memory().total / (1024**3)
    print(f"Available RAM: {memory_gb:.1f} GB")
    
    if memory_gb < 8:
        print("⚠️  Recommendation: Use max_workers=2 for low memory systems")
    elif memory_gb < 16:
        print("💡 Recommendation: Use max_workers=4 for moderate memory systems")
    else:
        print("✅ Recommendation: Use max_workers=6-8 for high memory systems")

def main():
    # Check system capabilities
    check_system_capabilities()
    
    # Configuration
    excel_file_path = "emotion_data.xlsx"
    video_folder_path = "videos"
    output_folder_path = "extracted_frames_video"
    
    print("\nChoose extraction method:")
    print("1. GPU-accelerated (fastest if GPU available)")
    print("2. CPU-optimized (most compatible)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    use_gpu = choice == "1"
    
    # Adjust workers based on method
    if use_gpu:
        max_workers = 2  # GPU processing is memory intensive
    else:
        max_workers = min(mp.cpu_count(), 6)  # CPU processing can use more workers
    
    print(f"Using {max_workers} workers")
    
    # Create extractor instance
    extractor = GPUVideoFrameExtractor(
        excel_file_path,
        video_folder_path,
        output_folder_path,
        use_gpu=use_gpu,
        max_workers=max_workers
    )
    
    # Process all records
    extractor.process_all_records()

if __name__ == "__main__":
    main()
