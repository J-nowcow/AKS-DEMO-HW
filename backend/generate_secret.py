# import secrets
import base64

redis_key = "New1234!"
# secret_key = "GjA0PHx96N"
secret_key = redis_key
encoded_key = base64.b64encode(secret_key.encode())
print(encoded_key.decode())