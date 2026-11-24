import os
import pickle
import time
from datetime import datetime

import cv2
import numpy as np

from face_recognition.face_detector import FaceDetector
from face_recognition.face_embedding import FaceEmbedder
from door_control import unlock_door

from notifications.notification import (
    send_visitor_photo,
    check_user_decision,
    send_access_result
)


# ==========================================
# CONFIGURATION
# ==========================================

EMBEDDINGS_FILE = "known_faces/embeddings.pkl"
VISITOR_FOLDER = "captured_visitors"

THRESHOLD = 0.8

# Known person opens the door directly
AUTO_UNLOCK_KNOWN = True      # set False if known people should also need approval
KNOWN_FRAMES_REQUIRED = 5     # consecutive "known" frames before opening
UNLOCK_COOLDOWN = 10          # seconds before the next automatic unlock


# ==========================================
# LOAD DATABASE
# ==========================================

def load_database():

    if not os.path.exists(EMBEDDINGS_FILE):

        print("❌ No registered faces found.")
        print("Run register_face.py first.")

        return None

    with open(EMBEDDINGS_FILE, "rb") as file:

        return pickle.load(file)


# ==========================================
# RECOGNIZE FACE
# ==========================================

def recognize_face(visitor_embedding, database):

    best_name = "UNKNOWN"
    best_distance = float("inf")

    for name, embeddings in database.items():

        for known_embedding in embeddings:

            distance = np.linalg.norm(
                known_embedding - visitor_embedding
            )

            if distance < best_distance:

                best_distance = distance
                best_name = name

    if best_distance <= THRESHOLD:

        return best_name, best_distance

    return "UNKNOWN", best_distance


# ==========================================
# SAVE VISITOR IMAGE
# ==========================================

def save_unknown_visitor(frame):

    os.makedirs(
        VISITOR_FOLDER,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filepath = os.path.join(
        VISITOR_FOLDER,
        f"visitor_{timestamp}.jpg"
    )

    cv2.imwrite(
        filepath,
        frame
    )

    print()
    print("🚨 UNKNOWN VISITOR DETECTED")
    print(f"Image saved: {filepath}")

    return filepath


# ==========================================
# MAIN
# ==========================================

def main():

    database = load_database()

    if database is None:
        return


    detector = FaceDetector()

    embedder = FaceEmbedder()


    camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        print("❌ Could not open camera.")

        return


    print()
    print("================================")
    print(" AI VISITOR ACCESS SYSTEM")
    print("================================")
    print()
    print("Camera started.")
    print("Press Q to exit.")
    print()


    # --------------------------------------
    # Telegram state
    # --------------------------------------

    telegram_waiting = False

    last_update_id = 0

    current_decision = None

    visitor_sent = False


    # --------------------------------------
    # Known person auto-unlock state
    # --------------------------------------

    known_count = 0

    last_unlock = 0.0


    while True:

        # ==================================
        # READ CAMERA
        # ==================================

        ret, frame = camera.read()

        if not ret:

            print("❌ Could not read camera.")

            break


        # ==================================
        # CHECK TELEGRAM
        # ==================================

        if telegram_waiting:

            decision, last_update_id = check_user_decision(
                last_update_id
            )

            if decision == "ACCEPT":

                current_decision = "ACCEPT"

                telegram_waiting = False

                print()
                print("================================")
                print("       ✅ ACCESS GRANTED")
                print("================================")
                print()

                print("🔓 Door should now OPEN.")
                send_access_result("ACCEPT")

                # Servo opens through the ESP32
                unlock_door()


            elif decision == "REJECT":

                current_decision = "REJECT"

                telegram_waiting = False

                print()
                print("================================")
                print("       ❌ ACCESS DENIED")
                print("================================")
                print()

                print("🔒 Door remains LOCKED.")
                send_access_result("REJECT")


        # ==================================
        # FACE DETECTION
        # ==================================

        faces = detector.detect_faces(frame)

        known_names_in_frame = []

        unknown_in_frame = False


        for (x, y, w, h) in faces:

            face = frame[
                y:y+h,
                x:x+w
            ]


            if face.size == 0:
                continue


            face = cv2.resize(
                face,
                (160, 160)
            )


            # ==================================
            # FACE EMBEDDING
            # ==================================

            visitor_embedding = embedder.get_embedding(
                face
            )


            # ==================================
            # RECOGNITION
            # ==================================

            name, distance = recognize_face(
                visitor_embedding,
                database
            )


            # ==================================
            # KNOWN PERSON
            # ==================================

            if name != "UNKNOWN":

                known_names_in_frame.append(name)

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"KNOWN: {name}",
                    (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    "ACCESS GRANTED",
                    (x, y+h+25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


            # ==================================
            # UNKNOWN PERSON
            # ==================================

            else:

                unknown_in_frame = True

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 0, 255),
                    2
                )


                # ----------------------------------
                # If waiting for Telegram
                # ----------------------------------

                if telegram_waiting:

                    label = "WAITING FOR APPROVAL"

                    cv2.putText(
                        frame,
                        label,
                        (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )


                # ----------------------------------
                # If accepted
                # ----------------------------------

                elif current_decision == "ACCEPT":

                    cv2.putText(
                        frame,
                        "ACCESS GRANTED",
                        (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )


                # ----------------------------------
                # If rejected
                # ----------------------------------

                elif current_decision == "REJECT":

                    cv2.putText(
                        frame,
                        "ACCESS DENIED",
                        (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )


                # ----------------------------------
                # New unknown visitor
                # ----------------------------------

                elif not visitor_sent:

                    print()
                    print(
                        f"UNKNOWN VISITOR | "
                        f"Distance: {distance:.3f}"
                    )


                    # Save full camera image
                    image_path = save_unknown_visitor(
                        frame
                    )


                    # Send Telegram
                    sent = send_visitor_photo(
                        image_path
                    )


                    if sent:

                        print()
                        print(
                            "📱 Telegram approval request sent."
                        )

                        print(
                            "Waiting for ACCEPT or REJECT..."
                        )

                        telegram_waiting = True

                        visitor_sent = True

                        current_decision = None

                    else:

                        print(
                            "❌ Telegram notification failed."
                        )


        # ==================================
        # KNOWN PERSON: OPEN DOOR DIRECTLY
        # (only when a known face is seen and NO unknown face is in view)
        # ==================================

        if known_names_in_frame and not unknown_in_frame:

            known_count += 1

        else:

            known_count = 0


        if (
            AUTO_UNLOCK_KNOWN
            and known_count >= KNOWN_FRAMES_REQUIRED
            and not telegram_waiting
            and time.time() - last_unlock >= UNLOCK_COOLDOWN
        ):

            last_unlock = time.time()

            known_count = 0

            print()
            print(
                f"✅ Known person recognised: "
                f"{known_names_in_frame[0]}"
            )
            print("🔓 Door opening.")

            unlock_door()


        # ==================================
        # STATUS ON SCREEN
        # ==================================

        if telegram_waiting:

            cv2.putText(
                frame,
                "WAITING FOR TELEGRAM APPROVAL",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2
            )

        elif current_decision == "ACCEPT":

            cv2.putText(
                frame,
                "ACCESS GRANTED",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

        elif current_decision == "REJECT":

            cv2.putText(
                frame,
                "ACCESS DENIED",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )


        # ==================================
        # SHOW CAMERA
        # ==================================

        cv2.imshow(
            "AI Visitor Access System",
            frame
        )


        # ==================================
        # KEYBOARD
        # ==================================

        key = cv2.waitKey(1) & 0xFF


        if key == ord("q"):

            break


        # ----------------------------------
        # Reset after visitor leaves
        # ----------------------------------

        if len(faces) == 0:

            if not telegram_waiting:

                visitor_sent = False

                current_decision = None


    # ==================================
    # CLEANUP
    # ==================================

    camera.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":

    main()