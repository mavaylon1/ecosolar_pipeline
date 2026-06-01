def pytest_addoption(parser):
    parser.addoption("--jnid", action="store", default=None, help="JNB job JNID to preview")
    parser.addoption("--full-trigger", action="store_true", default=False)
