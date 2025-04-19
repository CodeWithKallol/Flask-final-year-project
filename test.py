import cv2
import os
import sqlite3  # Import the SQLite library

def generate_dataset_from_db():
    # --- Database Interaction ---
    try:
        conn = sqlite3.connect('site.db')  # Replace 'your_database.db' with your database file
        cursor = conn.cursor()

        # Example: Fetch a specific student ID
        cursor.execute("SELECT roll_no FROM student")
        student_data = cursor.fetchone()

        if student_data:
            student_id = str(student_data[0])  # Assuming student_id is the first column
            print(f"[INFO] Using student ID from database: {student_id}")
        else:
            print("[ERROR] Could not retrieve student ID from the database.")
            return

        conn.close()

    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        return

    # --- Face Detection and Image Capture (Rest of your original code) ---
    face_classifier = cv2.CascadeClassifier(
        r"C:\Users\itsme\OneDrive\Desktop\Flask App\.venv\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml"
    )

    def face_cropped(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0:
            return None
        for (x, y, w, h) in faces:
            return img[y:y+h, x:x+w]

    student_dir = os.path.join("data", student_id)
    os.makedirs(student_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    img_id = 0

    print(f"\n[INFO] Collecting images for {student_id}...\n")

    while True:
        r, frame = cap.read()
        if not r:
            print("❌ Failed to capture frame from camera.")
            continue

        face = face_cropped(frame)
        if face is not None:
            img_id += 1
            face = cv2.resize(face, (200, 200))
            file_name_path = os.path.join(student_dir, f"{student_id}.{img_id}.jpg")
            cv2.imwrite(file_name_path, face)
            cv2.putText(face, f"Image {img_id}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Capturing Face", face)

            if cv2.waitKey(1) == 13 or img_id == 200:
                break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n✅ {img_id} face images of {student_id} collected and saved in: {student_dir}\n")

# Run the modified function
generate_dataset_from_db()