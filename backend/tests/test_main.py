import asyncio
import sys
if sys.platform=="win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def test_signup(client):
    """
    - Test sign up is successful - 201
    - Test sign up with duplicate sign up is unsuccessful with status code - 409
    """
    response=client.post(
        '/signup',
        json={
            "email":"test@example.com",
            "password":"stringst"
        }
    )

    assert response.status_code==201

    response=client.post(
        '/signup',
        json={
            "email":"test@example.com",
            "password":"stringst"
        }
    )

    assert response.status_code==409

def test_login(client):
    """
    - Test login is successful - 200
    - Test login with wrong password - 401
    - Test login with wrong email - 401
    """

    response=client.post(
        '/signup',
        json={
            "email":"test@example.com",
            "password":"stringst"
        }
    )

    assert response.status_code==201

    response=client.post(
        '/login',
        json={
            "email":"test@example.com",
            "password":"stringst"
        }
    )

    assert response.status_code==200

    assert response.cookies.get("access_token") is not None

    response=client.post(
        '/login',
        json={
            "email":"test@example.com",
            "password":"wrong_password"
        }
    )

    assert response.status_code==401

    response=client.post(
        '/login',
        json={
            "email":"wrong_email@example.com",
            "password":"stringst"
        }
    )

    assert response.status_code==401
