import os
import cv2
import pickle
import numpy as np

from face_recognition.face_detector import FaceDetector
from face_recognition.face_embedding import FaceEmbedder


EMBEDDINGS_FILE = "known_faces/embeddings.pkl"


def register_person(name):
    # Create required folder
    os.makedirs("known_faces", exist_ok=True)

    detector = FaceDetector()
    embedder = FaceEmbedder()

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    print()
    print(f"Registering: {name}")
    print("Look at the camera.")
    print("Press SPACE to capture a face.")
    print("Press Q to quit.")
    print()

    embeddings = []

    while len(embeddings) < 5:

        ret, frame = camera.read()

        if not ret:
            print("Could not read camera frame.")
            break

        faces = detector.detect_faces(frame)

        for (x, y, w, h) in faces:

            # Draw face rectangle
            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Captured: {len(embeddings)}/5",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            # Crop face
            face = frame[y:y + h, x:x + w]

            # Wait for SPACE
            key = cv2.waitKey(1) & 0xFF

            if key == ord(" "):

                if face.size == 0:
                    print("Invalid face image.")
                    continue

                # Resize face
                face = cv2.resize(face, (160, 160))

                # Generate FaceNet embedding
                embedding = embedder.get_embedding(face)

                if embedding is not None:
                    embeddings.append(embedding)

                    print(
                        f"Face {len(embeddings)}/5 captured successfully."
                    )

        cv2.imshow("Face Registration", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    if len(embeddings) == 0:
        print("No face embeddings captured.")
        return

    # Load existing database
    database = {}

    if os.path.exists(EMBEDDINGS_FILE):

        with open(EMBEDDINGS_FILE, "rb") as file:
            database = pickle.load(file)

    # Store this person's embeddings
    database[name] = embeddings

    # Save database
    with open(EMBEDDINGS_FILE, "wb") as file:
        pickle.dump(database, file)

    print()
    print("================================")
    print(f"Registration complete: {name}")
    print(f"Embeddings saved: {len(embeddings)}")
    print(f"Saved to: {EMBEDDINGS_FILE}")
    print("================================")


if __name__ == "__main__":

    name = input("Enter person's name: ").strip()

    if not name:
        print("Name cannot be empty.")
    else:
        register_person(name)