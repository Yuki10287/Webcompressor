class Validator:
    def validate_bytes_equal(self, original: bytes, restored: bytes) -> bool:
        return original == restored