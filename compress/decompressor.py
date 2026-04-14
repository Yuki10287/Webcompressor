class Decompressor:
    def restore_text(self, compressor, compressed_data: bytes) -> bytes:
        return compressor.decompress(compressed_data)