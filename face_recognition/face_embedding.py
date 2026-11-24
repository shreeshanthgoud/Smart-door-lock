from keras_facenet import FaceNet
import numpy as np


class FaceEmbedder:

    def __init__(self):
        print("Loading FaceNet model...")

        self.model = FaceNet()

        print("FaceNet model loaded successfully.")

    def get_embedding(self, face_image):
        """
        Generate a FaceNet embedding from a cropped face image.
        """

        if face_image is None:
            return None

        # FaceNet expects a batch of images
        face_image = np.asarray(face_image)

        face_image = np.expand_dims(face_image, axis=0)

        # Generate embedding
        embedding = self.model.embeddings(face_image)

        # Return the first embedding
        return embedding[0]