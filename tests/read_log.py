with open('test_output.log', 'rb') as f:
    content = f.read()
    print(content.decode('utf-16le', errors='ignore'))
