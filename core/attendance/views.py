import cv2, face_recognition, os
import numpy as np
import pandas as pd
import pyttsx3
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.conf import settings
from django.http import FileResponse, Http404
from .models import Student

# --- 1. HELPER FUNCTIONS ---

def get_user_log_dir(user):
    """Har administrator ke liye alag directory create karta hai[cite: 400, 469]."""
    path = os.path.join(settings.BASE_DIR, 'attendance_logs', str(user.username))
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def mark_attendance_logic(name, user):
    """Student ki duplicate attendance check karta hai aur record karta hai."""
    now = datetime.now()
    log_dir = get_user_log_dir(user)
    filename = os.path.join(log_dir, f"Attendance_{now.strftime('%Y-%m-%d')}.csv")
    
    # 1. File exist karti hai toh duplicate check karein
    if os.path.isfile(filename):
        df_existing = pd.read_csv(filename)
        # Agar aaj ke CSV mein yeh naam pehle se hai, toh function yahi stop kar dein
        if name in df_existing['Name'].values:
            print(f"Attendance already marked for {name} today.")
            return "Already Marked"

    # 2. Status aur Data Setup
    cutoff = datetime.strptime("10:30", "%H:%M").time()
    status = "Present" if now.time() < cutoff else "Late"
    data = {'Name': [name], 'Time': [now.strftime("%H:%M:%S")], 'Status': [status]}
    df_new = pd.DataFrame(data)
    
    # 3. CSV mein entry add karein [cite: 429, 461]
    if not os.path.isfile(filename):
        df_new.to_csv(filename, index=False)
    else:
        df_new.to_csv(filename, mode='a', header=False, index=False)
    
    # 4. Offline Voice Feedback [cite: 399, 486]
    try:
        engine = pyttsx3.init()
        engine.say(f"Attendance marked for {name}")
        engine.runAndWait()
        engine.stop() 
    except Exception as e:
        print(f"Voice Error: {e}")

    return status

# --- 2. MAIN VIEW FUNCTIONS ---

@login_required
def home(request):
    """Admin Dashboard overview[cite: 509]."""
    my_students = Student.objects.filter(added_by=request.user)

    log_dir = get_user_log_dir(request.user)

    csv_files = [f for f in os.listdir(log_dir) if f.endswith(".csv")]

    present_count = 0
    late_count = 0

    today_file = os.path.join(
        log_dir,
        f"Attendance_{datetime.now().strftime('%Y-%m-%d')}.csv"
    )

    if os.path.exists(today_file):

        df = pd.read_csv(today_file)

        present_count = len(df[df["Status"] == "Present"])

        late_count = len(df[df["Status"] == "Late"])

    student_count = my_students.count()

    absent_count = student_count - (present_count + late_count)

    if absent_count < 0:
        absent_count = 0

    return render(request, "home.html", {

        "student_count": student_count,

        "present_count": present_count,

        "late_count": late_count,

        "absent_count": absent_count,

        "csv_files": csv_files,
    })

@login_required
def mark_attendance_view(request):
    """AI Live Scanner: HOG Algorithm aur 128-D Encodings logic[cite: 393, 448, 523]."""
    my_students = Student.objects.filter(added_by=request.user)
    if not my_students:
        messages.error(request, "Please register students first!")
        return redirect('home')

    # Database se encodings ko numpy array mein convert karna [cite: 394, 501]
    known_encs = [np.fromstring(s.encoding, sep=',') for s in my_students]
    known_names = [s.name for s in my_students]
    
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Performance ke liye resize (0.25x) aur RGB conversion [cite: 392, 414]
        small_frame = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # HOG-based face detection [cite: 393, 416, 452]
        face_locs = face_recognition.face_locations(rgb_small, model="hog")
        face_encs = face_recognition.face_encodings(rgb_small, face_locs)

        for enc, loc in zip(face_encs, face_locs):
            # 0.45 Tolerance: Strict recognition ke liye [cite: 397, 454, 507]
            matches = face_recognition.compare_faces(known_encs, enc, tolerance=0.45)
            name = "Unknown"
            
            if True in matches:
                name = known_names[matches.index(True)]
                status = mark_attendance_logic(name, request.user)
                # Recognition ke waqt status screen par dikhana [cite: 433]
                cv2.putText(frame, f"{name}: {status}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Face bounding box draw karna [cite: 451]
            t, r, b, l = [v*4 for v in loc]
            cv2.rectangle(frame, (l, t), (r, b), (0, 255, 0), 2)
            cv2.putText(frame, name, (l, t-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow('FRAS AI Scanner - Press Q to Quit', frame)
        if cv2.waitKey(1) == ord('q'): break
        
    cap.release()
    cv2.destroyAllWindows()
    return redirect('home')

@login_required
def register_student(request):
    """Naye student ko facial landmarks ke saath register karna[cite: 440, 515]."""
    if request.method == "POST":
        s_id = request.POST.get('student_id')
        name = request.POST.get('name')
        
        if Student.objects.filter(student_id=s_id).exists():
            messages.error(request, "Student ID already exists!")
            return render(request, 'register.html')

        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            cv2.imshow("Register - Press SPACE to capture, Q to quit", frame)
            
            if cv2.waitKey(1) == ord(' '):
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # 128-D encoding generate karna [cite: 393, 443]
                encs = face_recognition.face_encodings(rgb)
                if encs:
                    Student.objects.create(
                        name=name, 
                        student_id=s_id, 
                        encoding=",".join(map(str, encs[0])), 
                        added_by=request.user
                    )
                    messages.success(request, f"{name} registered successfully!")
                    break
                else:
                    messages.warning(request, "No face detected. Try again.")
            
            elif cv2.waitKey(1) == ord('q'): break
            
        cap.release()
        cv2.destroyAllWindows()
        return redirect('home')
    return render(request, 'register.html')

# --- 3. ADMINISTRATIVE VIEWS ---

@login_required
def view_students(request):
    """Registered students ki list dikhana[cite: 513]."""
    students = Student.objects.filter(added_by=request.user)
    return render(request, 'view_students.html', {'students': students})

@login_required
def download_csv(request, filename):
    """Attendance reports download karne ke liye[cite: 400, 508]."""
    log_dir = get_user_log_dir(request.user)
    file_path = os.path.join(log_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    raise Http404("Report not found.")

def register_account(request):
    """Naya admin account create karna[cite: 511]."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register_account.html', {'form': form})

def custom_logout(request):
    """Secure logout logic."""
    logout(request)
    return redirect('login')

@login_required
def delete_student(request, pk):
    """Student record delete karna."""
    student = get_object_or_404(Student, pk=pk, added_by=request.user)
    student.delete()
    return redirect('view_students')

@login_required
def edit_student(request, pk):
    """Registered student ka naam edit karne ke liye view."""
    student = get_object_or_404(Student, pk=pk, added_by=request.user)
    if request.method == "POST":
        student.name = request.POST.get('name')
        student.save()
        messages.success(request, "Student updated successfully!")
        return redirect('view_students')
    return render(request, 'edit_student.html', {'student': student})