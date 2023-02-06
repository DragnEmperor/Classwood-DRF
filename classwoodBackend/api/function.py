import json
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def attempt_json_deserialize(data, expect_type=None):
    try:
        data = json.loads(data)
    except (TypeError, json.decoder.JSONDecodeError): pass

    if expect_type is not None and not isinstance(data, expect_type):
        raise ValueError(f"Got {type(data)} but expected {expect_type}.")

    return data

def create_jwt_pair(user : User):
    refresh_token = RefreshToken.for_user(user)
    tokens = { "access": str(refresh_token.access_token), "refresh": str(refresh_token) }
    
    return tokens
