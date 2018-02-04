
import socket
import time


host = "ecs0"
port = 8080

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


try:

    s.connect((host, port))
    s.close()
    value = 0
    print("successfully")
except Exception as e:
    print(e)
    value = 1



# time.sleep(100)
# s.close()


# s.connect((host, port))

