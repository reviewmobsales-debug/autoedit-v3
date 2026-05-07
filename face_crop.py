def auto_crop_vertical(video_path, output_path, target_aspect=9/16):
    """
    Detect face in video and auto-crop to vertical TikTok format (9:16).
    Keeps face centered in frame.
    """
    import cv2, subprocess, tempfile, shutil
    
    # Extract a sample frame for face detection
    cap = cv2.VideoCapture(str(video_path))
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    face_center = None
    frame_count = 0
    
    # Check every 10th frame to find a face
    while frame_count < 90:  # Check first ~3 seconds
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % 10 == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # Use largest face
                largest = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest
                face_center = (x + w//2, y + h//2)
                print(f"Face detected at ({face_center[0]}, {face_center[1]})")
                break
        
        frame_count += 1
    
    cap.release()
    
    if face_center is None:
        # No face found — center crop based on standard composition
        print("No face detected, using center crop")
        face_center = None
    
    # Get video dimensions
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(video_path)
    ], capture_output=True, text=True, timeout=10)
    
    if probe.returncode != 0:
        shutil.copy(str(video_path), str(output_path))
        return False
    
    orig_w, orig_h = map(int, probe.stdout.strip().split("x"))
    
    # Calculate crop dimensions for vertical 9:16
    target_w = int(orig_h * target_aspect) if orig_h else 1080
    target_h = orig_h
    
    if face_center:
        # Center crop around face
        crop_x = max(0, face_center[0] - target_w // 2)
        if crop_x + target_w > orig_w:
            crop_x = orig_w - target_w
        crop_x = max(0, crop_x)
    else:
        # Center crop
        crop_x = (orig_w - target_w) // 2
    
    crop_y = 0
    
    # Use ffmpeg to crop
    r = subprocess.run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"crop={target_w}:{target_h}:{crop_x}:{crop_y},scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy", "-pix_fmt", "yuv420p",
        str(output_path)
    ], capture_output=True, timeout=120)
    
    return r.returncode == 0 and os.path.exists(output_path)