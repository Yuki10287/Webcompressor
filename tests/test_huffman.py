from compress.text_compressor import TextCompressor


def main():
    compressor = TextCompressor()

    sample = b"""
    <html>
      <head><title>test</title></head>
      <body>
        <div class="card">hello hello hello hello</div>
        <div class="card">hello hello hello hello</div>
      </body>
    </html>
    """

    compressed = compressor.compress(sample)
    restored = compressor.decompress(compressed)

    print("original:", len(sample))
    print("compressed:", len(compressed))
    print("restored ok:", restored == sample)


if __name__ == "__main__":
    main()