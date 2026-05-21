from core.type_detector import detect_resource_type, normalize_extension_for_detection


def test_download_suffix_uses_real_extension_for_text():
    assert normalize_extension_for_detection("jquery.min.js.下载") == ".js"
    assert detect_resource_type("jquery.min.js.下载") == "text"
    assert detect_resource_type("style.css.download") == "text"


def test_download_suffix_uses_real_extension_for_image():
    assert normalize_extension_for_detection("logo.png.下载") == ".png"
    assert detect_resource_type("logo.png.下载") == "image"
    assert detect_resource_type("banner.jpg.crdownload") == "image"


def test_download_suffix_without_real_extension_stays_unsupported():
    assert normalize_extension_for_detection("abc.下载") == ""
    assert detect_resource_type("abc.下载") == "unsupported"
    assert detect_resource_type("resource.download") == "unsupported"

