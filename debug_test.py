try:
    with open("debug_output.txt", "w") as f:
        f.write("Hello from debug")
except Exception as e:
    pass # Can't print
