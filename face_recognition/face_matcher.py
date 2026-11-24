import numpy as np


class FaceMatcher:

    def __init__(self, threshold=0.6):
        self.threshold = threshold
        self.known_embeddings = []
        self.known_names = []

    def add_face(self, name, embedding):
        """
        Add a registered person's face embedding.
        """

        if embedding is None or len(embedding) == 0:
            print(f"Invalid embedding for {name}")
            return

        self.known_names.append(name)
        self.known_embeddings.append(embedding)

    def compare_faces(self, visitor_embedding):
        """
        Compare visitor embedding with registered faces.

        Returns:
            name of matched person, or 'UNKNOWN'
        """

        if visitor_embedding is None or len(visitor_embedding) == 0:
            return "UNKNOWN"

        if len(self.known_embeddings) == 0:
            return "UNKNOWN"

        best_match = "UNKNOWN"
        best_distance = float("inf")

        for name, known_embedding in zip(
            self.known_names,
            self.known_embeddings
        ):

            distance = np.linalg.norm(
                known_embedding - visitor_embedding
            )

            if distance < best_distance:
                best_distance = distance
                best_match = name

        if best_distance <= self.threshold:
            return best_match

        return "UNKNOWN"